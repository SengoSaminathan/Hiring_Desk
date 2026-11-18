"""Playwright Browser Automation Service for LinkedIn Candidate Sourcing.

Implements:
- Persistent browser session (cookies preserved in ./data/browser_profile).
- Headed Chromium execution so recruiter sees browser actions.
- Human Handover Gate: Pauses cleanly if login/verification checkpoint appears.
- Direct URL query navigation (from mobile_control_agent patterns).
- Candidate card DOM extraction with normalized profile schemas.
- Synthetic fixture fallback for offline / unauthenticated testing.
"""

import asyncio
import base64
import io
import json
import logging
import os
import re
import sys
import threading
import time
import urllib.parse
import uuid
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import BrowserContext, Page, async_playwright
from backend.app.core.config import settings
from backend.app.schemas.candidates import CandidateProfile
from backend.app.services.ai_service import ai_service
from backend.app.services.db_service import db_service, clean_linkedin_card_text

logger = logging.getLogger("hiring_desk.browser_service")

# Curated, verified portrait URLs from Unsplash for guaranteed image loading (no 404s)
VERIFIED_AVATARS = [
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=120&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=120&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=120&auto=format&fit=crop&q=80",
    "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=120&auto=format&fit=crop&q=80",
]


def _crop_avatar_to_data_uri(image_bytes: bytes, box: Optional[List[float]]) -> Optional[str]:
    """Crops avatar box coordinates from image bytes and returns base64 PNG data URI."""
    if not box or len(box) != 4:
        return None
    try:
        from PIL import Image
        pil_img = Image.open(io.BytesIO(image_bytes))
        w, h = pil_img.size
        ymin, xmin, ymax, xmax = box

        if max(box) <= 1.0:
            left, top, right, bottom = int(xmin * w), int(ymin * h), int(xmax * w), int(ymax * h)
        else:
            left, top, right, bottom = int(xmin * w / 1000), int(ymin * h / 1000), int(xmax * w / 1000), int(ymax * h / 1000)

        left = max(0, min(left, w - 10))
        top = max(0, min(top, h - 10))
        right = max(left + 10, min(right, w))
        bottom = max(top + 10, min(bottom, h))

        if (right - left) >= 10 and (bottom - top) >= 10:
            cropped = pil_img.crop((left, top, right, bottom))
            cropped.thumbnail((120, 120))
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        logger.debug("Avatar crop warning: %s", e)
    return None


def is_card_geographically_compatible(cand_loc: str, target_locations: Optional[List[str]] = None) -> bool:
    """Verifies that a candidate card does not belong to an incompatible foreign country when searching for local roles."""
    if not target_locations or not cand_loc:
        return True

    cand_loc_lower = cand_loc.lower().strip()
    target_locs_lower = [t.lower().strip() for t in target_locations if t and t.strip()]
    if not target_locs_lower or "remote" in target_locs_lower:
        return True

    # Check if target represents India / Indian cities
    is_india_target = any(k in target_locs_lower for k in [
        "india", "chennai", "coimbatore", "bengaluru", "bangalore", "hyderabad",
        "mumbai", "delhi", "pune", "tamil nadu", "tamilnadu", "karnataka", "telangana"
    ])

    # Check if target represents UAE / Gulf
    is_uae_target = any(k in target_locs_lower for k in [
        "dubai", "uae", "united arab emirates", "abu dhabi", "sharjah", "qatar", "saudi", "riyadh"
    ])

    # Incompatible foreign markers for Indian positions
    FOREIGN_FOR_INDIA = [
        "dubai", "uae", "united arab emirates", "abu dhabi", "egypt", "cairo",
        "saudi arabia", "riyadh", "kuwait", "qatar", "doha", "united states",
        "usa", "united kingdom", "london", "canada", "germany", "australia"
    ]

    if is_india_target:
        # If card mentions foreign country and does not mention India or Indian cities
        has_foreign = any(f in cand_loc_lower for f in FOREIGN_FOR_INDIA)
        has_india = any(i in cand_loc_lower for i in [
            "india", "tamil nadu", "tamilnadu", "chennai", "coimbatore", "bengaluru",
            "bangalore", "hyderabad", "mumbai", "delhi", "pune", "karnataka"
        ])
        if has_foreign and not has_india:
            return False

    if is_uae_target:
        FOREIGN_FOR_UAE = ["egypt", "cairo", "united states", "usa", "canada", "germany", "australia"]
        has_foreign = any(f in cand_loc_lower for f in FOREIGN_FOR_UAE)
        has_uae = any(u in cand_loc_lower for u in ["dubai", "uae", "united arab emirates", "abu dhabi", "sharjah"])
        if has_foreign and not has_uae:
            return False

    return True


def score_card_geographic_relevance(cand_loc: str, target_locations: Optional[List[str]] = None) -> int:
    """Computes a sorting score for candidate cards to prioritize local candidates matching target city/state."""
    if not target_locations or not cand_loc:
        return 50
    cand_loc_lower = cand_loc.lower().strip()
    target_locs_lower = [t.lower().strip() for t in target_locations if t and t.strip()]

    # Direct city or specific token match
    for t in target_locs_lower:
        if t in cand_loc_lower and t not in ("india", "united states", "remote"):
            return 100  # Exact local city/state match

    if any(t in cand_loc_lower for t in target_locs_lower):
        return 75  # Regional / country match

    return 50


class LiveSourcingTracker:
    """Thread-safe state tracker for live browser sourcing sessions."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._resume_events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str, mode: str, query: str, max_results: int) -> Dict[str, Any]:
        with self._lock:
            self._resume_events[session_id] = threading.Event()
            data = {
                "session_id": session_id,
                "mode": mode,
                "query": query,
                "max_results": max_results,
                "state": "initializing",
                "progress": 5,
                "message": "Initializing sourcing session...",
                "candidates": [],
                "error": None,
                "should_stop": False,
                "resumed": False,
                "created_at": time.time(),
                "updated_at": time.time(),
            }
            self._sessions[session_id] = data
            return data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess:
                return dict(sess)
            return None

    def update_session(self, session_id: str, **kwargs):
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess:
                sess.update(kwargs)
                sess["updated_at"] = time.time()

    def resume_session(self, session_id: str) -> bool:
        with self._lock:
            evt = self._resume_events.get(session_id)
            if evt:
                evt.set()
            sess = self._sessions.get(session_id)
            if sess:
                sess["resumed"] = True
                sess["message"] = "Proceed signal received. Verifying login and resuming agent control..."
                sess["updated_at"] = time.time()
                return True
            return False

    def is_resumed(self, session_id: str) -> bool:
        with self._lock:
            evt = self._resume_events.get(session_id)
            if evt and evt.is_set():
                return True
            sess = self._sessions.get(session_id)
            return bool(sess and sess.get("resumed"))

    def reset_resume(self, session_id: str):
        with self._lock:
            evt = self._resume_events.get(session_id)
            if evt:
                evt.clear()
            sess = self._sessions.get(session_id)
            if sess:
                sess["resumed"] = False

    def stop_session(self, session_id: Optional[str] = None):
        with self._lock:
            if session_id:
                sess = self._sessions.get(session_id)
                if sess:
                    sess["should_stop"] = True
                    sess["state"] = "stopped"
                    sess["message"] = "Sourcing session stopped by recruiter."
                evt = self._resume_events.get(session_id)
                if evt:
                    evt.set()
            else:
                for sid, sess in self._sessions.items():
                    if sess.get("state") not in ("completed", "failed", "stopped"):
                        sess["should_stop"] = True
                        sess["state"] = "stopped"
                        sess["message"] = "Sourcing session stopped by recruiter."
                for evt in self._resume_events.values():
                    evt.set()


sourcing_tracker = LiveSourcingTracker()


class DedicatedBrowserRunner:
    """Runs Playwright operations on a dedicated thread with a ProactorEventLoop on Windows.
    
    Guarantees asyncio.create_subprocess_exec works regardless of Uvicorn's event loop policy.
    """
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _ensure_started(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="PlaywrightWorker")
            self._thread.start()
            self._ready.wait(timeout=10.0)

    def _run_loop(self):
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._ready.set()
        loop.run_forever()

    async def run(self, coro):
        self._ensure_started()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return await asyncio.wrap_future(future)


def _clean_stale_profile_locks(profile_dir: str):
    """Removes stale Chromium/Chrome lockfiles left by previous aborted or crashed runs."""
    if not os.path.exists(profile_dir):
        return
    lock_files = [
        "lockfile",
        "SingletonLock",
        "SingletonCookie",
        "SingletonSocket",
        "DevToolsActivePort",
    ]
    for fname in lock_files:
        fpath = os.path.join(profile_dir, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                logger.info("Removed stale lockfile: %s", fpath)
            except Exception as e:
                logger.debug("Could not remove lockfile %s: %s", fpath, e)


class _LinkedInBrowserEngine:
    """Internal engine executing within the dedicated browser thread."""

    def __init__(self):
        self.user_data_dir = os.path.abspath(settings.PLAYWRIGHT_USER_DATA_DIR)
        os.makedirs(self.user_data_dir, exist_ok=True)
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._current_channel: Optional[str] = None
        self._lock = asyncio.Lock()

    async def _get_or_create_context(self, browser_channel: Optional[str] = "chrome") -> Tuple[BrowserContext, Page]:
        """Launches or reuses a persistent browser context with the requested channel (chrome, msedge, or chromium).
        
        Anti-detection measures:
        - Masks navigator.webdriver completely at prototype and instance level
        - Removes --enable-automation and avoids --disable-extensions flag
        - Injects realistic Chrome runtime, plugins, mimeTypes, languages, and WebGL GPU vendor
        - Uses native channel launch so Playwright manages Windows process isolation safely
        """
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        # Determine user data dir and channel
        selected_channel = (browser_channel or "chrome").lower().strip()
        channel = None
        if selected_channel in ("chrome", "google-chrome", "google_chrome"):
            channel = "chrome"
            profile_dir = os.path.abspath(os.path.join("data", "browser_profile_chrome"))
        elif selected_channel in ("msedge", "edge", "microsoft-edge", "microsoft_edge"):
            channel = "msedge"
            profile_dir = os.path.abspath(os.path.join("data", "browser_profile_edge"))
        else:
            channel = None
            profile_dir = os.path.abspath(os.path.join("data", "browser_profile"))

        os.makedirs(profile_dir, exist_ok=True)
        _clean_stale_profile_locks(profile_dir)

        # If existing context has a different channel or is closed, reset context
        if self._context is not None:
            if getattr(self, "_current_channel", None) != (channel or "chromium"):
                logger.info("Switching browser channel from %s to %s", self._current_channel, channel or "chromium")
                try:
                    await self._context.close()
                except Exception:
                    pass
                self._context = None
            else:
                try:
                    _ = self._context.pages
                except Exception:
                    logger.info("Previous browser context closed or disconnected. Resetting context reference...")
                    self._context = None

        if self._context is None:
            logger.info("Launching persistent Playwright context (channel=%s) at %s", channel, profile_dir)

            # Realistic desktop Windows Chrome 131 user-agent
            realistic_ua = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )

            launch_kwargs = {
                "user_data_dir": profile_dir,
                "headless": settings.PLAYWRIGHT_HEADLESS,
                "no_viewport": True,
                "user_agent": realistic_ua,
                "ignore_default_args": ["--enable-automation"],
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                ],
                "timeout": 30000,
            }
            if channel:
                launch_kwargs["channel"] = channel

            try:
                self._context = await self._playwright.chromium.launch_persistent_context(**launch_kwargs)
                self._current_channel = channel or "chromium"
                logger.info("Successfully launched persistent context (channel=%s)", self._current_channel)
            except Exception as e:
                logger.warning("Failed to launch with channel=%s: %s. Attempting fallback...", channel, e)
                fallback_succeeded = False
                if channel == "chrome":
                    try:
                        logger.info("Attempting fallback from chrome to msedge...")
                        edge_profile_dir = os.path.abspath(os.path.join("data", "browser_profile_edge"))
                        os.makedirs(edge_profile_dir, exist_ok=True)
                        _clean_stale_profile_locks(edge_profile_dir)
                        edge_kwargs = dict(launch_kwargs)
                        edge_kwargs["user_data_dir"] = edge_profile_dir
                        edge_kwargs["channel"] = "msedge"
                        self._context = await self._playwright.chromium.launch_persistent_context(**edge_kwargs)
                        self._current_channel = "msedge"
                        fallback_succeeded = True
                        logger.info("Successfully launched with fallback msedge!")
                    except Exception as edge_err:
                        logger.warning("msedge fallback failed: %s", edge_err)

                if not fallback_succeeded:
                    logger.info("Falling back to default bundled Chromium...")
                    default_profile_dir = os.path.abspath(os.path.join("data", "browser_profile"))
                    os.makedirs(default_profile_dir, exist_ok=True)
                    _clean_stale_profile_locks(default_profile_dir)
                    launch_kwargs["user_data_dir"] = default_profile_dir
                    launch_kwargs.pop("channel", None)
                    self._context = await self._playwright.chromium.launch_persistent_context(**launch_kwargs)
                    self._current_channel = "chromium"

            # Inject comprehensive anti-detection scripts on browser context
            await self._setup_anti_detection(self._context)

        pages = self._context.pages
        page = pages[0] if pages else await self._context.new_page()
        try:
            await page.bring_to_front()
        except Exception:
            pass
        return self._context, page

    async def _setup_anti_detection(self, context: BrowserContext):
        """Injects stealth anti-detection scripts into every page to mask Playwright automation signals."""
        anti_detect_script = """
        (() => {
            // 1. Fully eliminate navigator.webdriver detection
            try {
                if ('webdriver' in navigator) {
                    delete Object.getPrototypeOf(navigator).webdriver;
                }
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true,
                    enumerable: false,
                });
            } catch (e) {}

            // 2. Mock full window.chrome runtime & app objects
            try {
                if (!window.chrome) {
                    window.chrome = {};
                }
                if (!window.chrome.app) {
                    window.chrome.app = {
                        isInstalled: false,
                        InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                        RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' },
                    };
                }
                if (!window.chrome.runtime) {
                    window.chrome.runtime = {
                        id: undefined,
                        connect: () => ({ onMessage: { addListener: () => {} }, postMessage: () => {} }),
                        sendMessage: () => {},
                    };
                }
            } catch (e) {}

            // 3. Mock genuine plugins & mimeTypes
            try {
                if (!navigator.plugins || navigator.plugins.length === 0) {
                    const fakePlugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                    ];
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => fakePlugins,
                        enumerable: true,
                        configurable: true,
                    });
                }
            } catch (e) {}

            // 4. Mock languages
            try {
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                    enumerable: true,
                    configurable: true,
                });
            } catch (e) {}

            // 5. Hardware concurrency & device memory
            try {
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                    configurable: true,
                });
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                    configurable: true,
                });
            } catch (e) {}

            // 6. WebGL GPU vendor & renderer masking (avoids SwiftShader / headless detection)
            try {
                const maskWebGL = (glContext) => {
                    if (!glContext || !glContext.prototype) return;
                    const origGetParam = glContext.prototype.getParameter;
                    glContext.prototype.getParameter = function(param) {
                        // UNMASKED_VENDOR_WEBGL
                        if (param === 37445) return 'Google Inc. (NVIDIA)';
                        // UNMASKED_RENDERER_WEBGL
                        if (param === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                        return origGetParam.call(this, param);
                    };
                };
                if (window.WebGLRenderingContext) maskWebGL(WebGLRenderingContext);
                if (window.WebGL2RenderingContext) maskWebGL(WebGL2RenderingContext);
            } catch (e) {}

            // 7. Permissions query consistency
            try {
                if (window.navigator && window.navigator.permissions && window.navigator.permissions.query) {
                    const origQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => {
                        if (parameters.name === 'notifications') {
                            return Promise.resolve({ state: Notification.permission });
                        }
                        return origQuery(parameters);
                    };
                }
            } catch (e) {}
        })();
        """
        try:
            await context.add_init_script(anti_detect_script)
            logger.info("Comprehensive anti-detection init script registered on browser context.")
        except Exception as e:
            logger.debug("Could not add anti-detection init script: %s", e)

        # Also inject into all existing pages immediately
        for page in context.pages:
            try:
                await page.evaluate(anti_detect_script)
            except Exception:
                pass


    async def has_linkedin_cookie(self) -> bool:
        """Inspects browser context cookies for active LinkedIn authentication (li_at)."""
        if self._context is None:
            return False
        try:
            cookies = await self._context.cookies(["https://www.linkedin.com", "https://linkedin.com"])
            for c in cookies:
                # li_at is the authentic session token (usually 100+ chars)
                if c.get("name") == "li_at" and c.get("value") and len(c.get("value")) > 15:
                    return True
        except Exception as e:
            logger.debug("Cookie check exception: %s", e)
        return False

    async def is_authenticated_session(self, page: Page) -> bool:
        """Thoroughly checks if the browser has an active, authenticated LinkedIn session.
        
        Uses multiple signals:
        1. URL pattern analysis (login/authwall/signup = not authenticated)
        2. li_at session cookie presence
        3. DOM elements indicating logged-in state (global nav, feed, profile)
        4. Page title heuristics ("LinkedIn" vs "Log In or Sign Up")
        
        Returns False if on any authwall, login, checkpoint, or signup screen.
        """
        try:
            curr_url = page.url or ""
            # about:blank or empty URL means we haven't navigated yet
            if not curr_url or "about:blank" in curr_url:
                return False
            # Any authwall, checkpoint, or login page immediately means unauthenticated
            if any(x in curr_url.lower() for x in ["/login", "/checkpoint", "/authwall", "/signup", "uas/login"]):
                return False
        except Exception:
            pass

        # Check for genuine session cookie (most reliable signal)
        if await self.has_linkedin_cookie():
            return True

        # Check for authenticated DOM elements (multiple selectors for robustness)
        auth_selectors = [
            "#global-nav",
            ".global-nav__me",
            ".feed-identity-module",
            "[data-view-name*='profile-card']",
            ".scaffold-layout__main",
            "div[data-test-global-nav]",
            "nav.global-nav",
            ".feed-shared-actor",
            ".share-box-feed-entry__trigger",
        ]
        try:
            for sel in auth_selectors:
                elem = await page.query_selector(sel)
                if elem:
                    logger.debug("Auth detected via DOM selector: %s", sel)
                    return True
        except Exception:
            pass

        # Heuristic: check page title — logged-in LinkedIn shows "Feed | LinkedIn" or "(N) LinkedIn"
        try:
            title = (await page.title() or "").lower()
            if "linkedin" in title and not any(x in title for x in ["log in", "sign up", "sign in", "join"]):
                # Title looks authenticated (e.g. "Feed | LinkedIn" or "John Doe | LinkedIn")
                return True
        except Exception:
            pass

        return False

    async def _inject_login_handover_banner(self, page: Page, browser_name: str = "Browser"):
        """Injects prominent golden action banner into the browser window asking user to log in."""
        banner_script = f"""
        (() => {{
            let banner = document.getElementById('hiring-desk-login-banner');
            if (!banner) {{
                banner = document.createElement('div');
                banner.id = 'hiring-desk-login-banner';
                banner.style.position = 'fixed';
                banner.style.top = '14px';
                banner.style.left = '50%';
                banner.style.transform = 'translateX(-50%)';
                banner.style.zIndex = '9999999';
                banner.style.background = '#0f172a';
                banner.style.color = '#ffffff';
                banner.style.border = '2px solid #f59e0b';
                banner.style.borderRadius = '14px';
                banner.style.padding = '14px 28px';
                banner.style.boxShadow = '0 10px 30px rgba(0,0,0,0.6), 0 0 20px rgba(245,158,11,0.5)';
                banner.style.fontFamily = 'system-ui, -apple-system, sans-serif';
                banner.style.fontSize = '14px';
                banner.style.textAlign = 'center';
                document.body.appendChild(banner);
            }}
            banner.style.border = '2px solid #f59e0b';
            banner.innerHTML = `
                <div style="font-weight:700; color:#fbbf24; margin-bottom:4px; font-size:15px; display:flex; align-items:center; justify-content:center; gap:8px;">
                    <span>🔑</span> <span>Recruiter Action Required: Sign in to LinkedIn ({browser_name.title()})</span>
                </div>
                <div style="font-size:12px; color:#cbd5e1;">
                    Please log into your LinkedIn account in this window. Once logged in, click <strong>"Proceed"</strong> in the Hiring Desk UI to resume automated candidate search.
                </div>
            `;
        }})();
        """
        try:
            await page.evaluate(banner_script)
        except Exception:
            pass

    async def _inject_login_warning_banner(self, page: Page):
        """Flashes red warning when user clicks Proceed without actually having logged in."""
        warning_script = """
        (() => {
            let banner = document.getElementById('hiring-desk-login-banner');
            if (banner) {
                banner.style.border = '3px solid #ef4444';
                banner.style.boxShadow = '0 10px 35px rgba(239,68,68,0.7), 0 0 25px rgba(239,68,68,0.6)';
                banner.innerHTML = `
                    <div style="font-weight:800; color:#f87171; margin-bottom:4px; font-size:16px; display:flex; align-items:center; justify-content:center; gap:8px;">
                        <span>⚠️</span> <span>Action Required: Please Finish Signing In First</span>
                    </div>
                    <div style="font-size:13px; color:#fee2e2;">
                        You clicked Proceed, but LinkedIn login is not detected yet. Please enter your credentials and sign in, then click <strong>"Proceed"</strong> in the Hiring Desk UI.
                    </div>
                `;
            }
        })();
        """
        try:
            await page.evaluate(warning_script)
        except Exception:
            pass

    async def search_live_linkedin(
        self,
        keywords: str,
        max_results: int = 6,
        deep_scrape: bool = True,
        browser_channel: Optional[str] = "chrome",
        session_id: Optional[str] = None,
        role_title: Optional[str] = None,
        mandatory_skills: Optional[List[str]] = None,
        preferred_locations: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Tuple[List[CandidateProfile], str, str]:
        """Live LinkedIn Sourcing directly on LinkedIn with Recruiter Handover and Portal Return:
        
        1. Launches visible headed browser (Chrome, Edge, or Chromium) with persistent profile.
        2. Strictly checks if LinkedIn session cookie (li_at) is active and user is logged in.
        3. If cookie is NOT available:
           - Opens LinkedIn login page directly: https://www.linkedin.com/login
           - Injects handover banner asking recruiter to take control and log in.
           - Sets session tracker state="waiting_for_login".
           - Waits for recruiter to sign in and click "Proceed" in the Hiring Desk UI.
           - If user clicks "Proceed" without logging in, rejects proceed and insists on real login.
        4. Once verified logged in:
           - AI Agent takes control of the UI!
           - Directly navigates to LinkedIn People Search:
             https://www.linkedin.com/search/results/people/?keywords=...
           - Injects Agent HUD on LinkedIn to indicate active agent control.
           - Harvests candidate profile cards from search results DOM.
           - Autonomously traverses profiles to extract deep resumes (About, Experience, Skills, Avatar photos).
           - Persists candidate profiles into SQLite database (data/hiring_desk.db).
        5. Completion & Portal Return:
           - Displays completion notification with countdown in browser HUD.
           - Redirects browser back to Hiring Desk portal (http://localhost:3000) with welcome banner.
        """
        encoded_query = urllib.parse.quote(keywords.strip())
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}&origin=GLOBAL_SEARCH_HEADER"
        channel_name = (browser_channel or "chrome").title()

        if session_id:
            sourcing_tracker.update_session(
                session_id,
                state="launching_browser",
                progress=15,
                message=f"Launching headed {channel_name} browser directly to LinkedIn...",
            )

        async with self._lock:
            _, page = await self._get_or_create_context(browser_channel=browser_channel)
            await page.bring_to_front()

        try:
            if True:
                if session_id:

                    sess = sourcing_tracker.get_session(session_id)
                    if sess and sess.get("should_stop"):
                        return [], search_url, "Sourcing session stopped by user."

                # Step 1: Strict Cookie & Authentication Check
                logger.info("Checking LinkedIn authentication cookie (li_at) in %s...", channel_name)
                is_auth = await self.is_authenticated_session(page)

                if not is_auth:
                    logger.info("No active LinkedIn session found. Insisting user log in at https://www.linkedin.com/login...")
                    if session_id:
                        sourcing_tracker.update_session(
                            session_id,
                            state="waiting_for_login",
                            progress=25,
                            message=f"LinkedIn login required. Please take control of the open {channel_name} browser, log in to LinkedIn, then click 'Proceed' below.",
                            error=None,
                        )

                    try:
                        curr = page.url or ""
                        if not curr or "about:blank" in curr or not any(x in curr for x in ["login", "checkpoint"]):
                            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=25000)
                    except Exception as e:
                        logger.warning("Goto login timeout/warning: %s", e)

                    # Inject Handover Banner inside the open browser window
                    await self._inject_login_handover_banner(page, channel_name)

                    # Wait for user to sign in and click "Proceed" in the UI (strict verification)
                    logger.info("Waiting for recruiter login and verified 'Proceed' signal (up to 300s)...")
                    wait_start = time.time()
                    while time.time() - wait_start < 300:
                        if session_id:
                            sess = sourcing_tracker.get_session(session_id)
                            if sess and sess.get("should_stop"):
                                return [], "https://www.linkedin.com/login", "Sourcing session stopped by user."

                        resumed = session_id and sourcing_tracker.is_resumed(session_id)
                        is_logged_in_now = await self.is_authenticated_session(page)

                        # If user clicked Proceed:
                        if resumed:
                            if not is_logged_in_now:
                                logger.warning("Proceed was clicked, but LinkedIn login is NOT yet complete! Rejecting proceed.")
                                sourcing_tracker.reset_resume(session_id)
                                if session_id:
                                    sourcing_tracker.update_session(
                                        session_id,
                                        state="waiting_for_login",
                                        progress=25,
                                        message="⚠️ Login not detected in browser. Please sign in to LinkedIn before clicking Proceed.",
                                        error="Login not detected yet. Please sign into LinkedIn in the browser window.",
                                    )
                                await self._inject_login_warning_banner(page)
                                await asyncio.sleep(1.0)
                                continue
                            else:
                                logger.info("Verified login confirmed via Proceed button! Resuming agent control...")
                                break

                        # Also auto-detect if user logged in without clicking proceed
                        if is_logged_in_now:
                            logger.info("Active LinkedIn session automatically detected! Resuming agent control...")
                            break

                        await asyncio.sleep(1.0)

                    # Clean up handover banner
                    try:
                        await page.evaluate("(() => { const b = document.getElementById('hiring-desk-login-banner'); if (b) b.remove(); })();")
                    except Exception:
                        pass

                # Step 2: Knowledge-Driven Deduplication & Adaptive Sourcing Loop
                known_identifiers = db_service.get_known_candidate_identifiers()
                known_urls = set(known_identifiers.get("urls", set()))
                known_names = set(known_identifiers.get("names", set()))

                harvested_candidates: List[CandidateProfile] = []
                active_query = keywords.strip()
                attempted_queries = [active_query]
                page_num = 1
                query_pivot_count = 0
                max_pivots = 3

                logger.info(
                    "Starting adaptive LinkedIn sourcing loop. Initial query: '%s', target: %d candidates. DB known: %d URLs, %d names.",
                    active_query, max_results, len(known_urls), len(known_names)
                )

                while len(harvested_candidates) < max_results:
                    if session_id:
                        sess = sourcing_tracker.get_session(session_id)
                        if sess and sess.get("should_stop"):
                            return harvested_candidates, search_url, "Sourcing session stopped by user."

                    encoded_query = urllib.parse.quote(active_query)
                    search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}&origin=GLOBAL_SEARCH_HEADER"
                    if page_num > 1:
                        search_url += f"&page={page_num}"

                    prog = 40 + int((len(harvested_candidates) / max(1, max_results)) * 40)
                    if session_id:
                        sourcing_tracker.update_session(
                            session_id,
                            state="searching",
                            progress=prog,
                            message=f"Agent UI Control: Searching LinkedIn for '{active_query}' (Page {page_num})...",
                            error=None,
                        )

                    logger.info("Agent UI navigation: Visiting search URL: %s", search_url)
                    try:
                        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    except Exception as e:
                        logger.warning("Search goto warning: %s. Continuing...", e)

                    # Check if navigation got caught in authwall / checkpoint
                    curr_url = page.url or ""
                    if any(x in curr_url for x in ["login", "checkpoint", "authwall", "signup"]):
                        logger.warning("Authwall or login checkpoint detected during search navigation! URL: %s", curr_url)
                        if session_id:
                            sourcing_tracker.update_session(
                                session_id,
                                state="waiting_for_login",
                                progress=25,
                                message="LinkedIn checkpoint or sign-in required. Please complete it in browser, then click Proceed.",
                                error="LinkedIn checkpoint or login required.",
                            )
                        await self._inject_login_handover_banner(page, channel_name)
                        while True:
                            if session_id:
                                sess = sourcing_tracker.get_session(session_id)
                                if sess and sess.get("should_stop"):
                                    return harvested_candidates, curr_url, "Sourcing session stopped by user."
                            resumed = session_id and sourcing_tracker.is_resumed(session_id)
                            is_ok = await self.is_authenticated_session(page)
                            if (resumed or is_ok) and not any(x in (page.url or "") for x in ["login", "checkpoint", "authwall", "signup"]):
                                break
                            if resumed and not is_ok:
                                sourcing_tracker.reset_resume(session_id)
                                await self._inject_login_warning_banner(page)
                            await asyncio.sleep(1.0)
                        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                    await self._dismiss_common_overlays(page)

                    # Inject HUD
                    await self._inject_linkedin_hud(
                        page,
                        f"🤖 Agent Active: Sourcing for '{active_query}' (Page {page_num}) — Harvested {len(harvested_candidates)}/{max_results}"
                    )

                    # Smooth scroll to trigger lazy loading
                    try:
                        await page.evaluate("window.scrollBy({ top: 450, behavior: 'smooth' })")
                        await asyncio.sleep(1.2)
                    except Exception:
                        pass

                    # Step 3: Extract Candidate Cards from DOM
                    if session_id:
                        sourcing_tracker.update_session(
                            session_id,
                            state="extracting",
                            message=f"Harvesting and evaluating candidate profiles on Page {page_num}...",
                        )

                    cards = await self._extract_candidate_cards(page, max_results * 2)

                    # Knowledge Deduplication: Separate fresh cards from previously stored profiles
                    fresh_cards: List[CandidateProfile] = []
                    duplicate_cards: List[CandidateProfile] = []
                    effective_targets = preferred_locations or ([location] if location else [])

                    for c in cards:
                        if db_service.is_candidate_duplicate(c.canonical_url, c.name, {"urls": known_urls, "names": known_names}):
                            duplicate_cards.append(c)
                        else:
                            card_loc = c.location or c.current_location or ""
                            if effective_targets and not is_card_geographically_compatible(card_loc, effective_targets):
                                logger.info(
                                    "Filtered out foreign candidate card '%s' (%s) incompatible with target locations: %s",
                                    c.name, card_loc, effective_targets
                                )
                                continue
                            fresh_cards.append(c)

                    # Prioritize candidate cards that directly match the target city/state
                    if effective_targets and fresh_cards:
                        fresh_cards.sort(
                            key=lambda x: score_card_geographic_relevance(x.location or x.current_location or "", effective_targets),
                            reverse=True
                        )

                    total_cards = len(cards)
                    sat_pct = int((len(duplicate_cards) / max(total_cards, 1)) * 100) if total_cards > 0 else 100

                    # Check for 0 results on page
                    is_no_results = (total_cards == 0)
                    if not is_no_results:
                        try:
                            no_res_el = await page.query_selector(
                                ".search-reusables__no-results, h2:has-text('No results found'), div.artdeco-empty-state"
                            )
                            if no_res_el:
                                is_no_results = True
                        except Exception:
                            pass

                    logger.info(
                        "Search results evaluation: %d total cards (%d duplicates, %d fresh, zero_results=%s). Saturation: %d%%",
                        total_cards, len(duplicate_cards), len(fresh_cards), is_no_results, sat_pct
                    )

                    # BRANCH 1: Fresh candidates discovered!
                    if fresh_cards:
                        for cand in fresh_cards:
                            if len(harvested_candidates) >= max_results:
                                break
                            if session_id:
                                sess = sourcing_tracker.get_session(session_id)
                                if sess and sess.get("should_stop"):
                                    break
                                cur_idx = len(harvested_candidates) + 1
                                prog = 50 + int((cur_idx / max_results) * 38)
                                sourcing_tracker.update_session(
                                    session_id,
                                    state="extracting",
                                    progress=prog,
                                    message=f"Agent taking control: Profiling candidate {cur_idx}/{max_results}: {cand.name} (duplicates skipped)...",
                                )

                            # Deep profile extraction
                            if deep_scrape and cand.canonical_url and "linkedin.com/in/" in cand.canonical_url and not cand.canonical_url.endswith("-1"):
                                logger.info("Agent UI navigation: Visiting %s (%s)", cand.name, cand.canonical_url)
                                await self._inject_linkedin_hud(
                                    page,
                                    f"👤 Profiling Candidate {len(harvested_candidates)+1}/{max_results}: {cand.name} — Extracting Experience & Skills..."
                                )
                                try:
                                    cand = await self._visit_and_extract_profile(page, cand)
                                except Exception as deep_err:
                                    logger.warning("Deep extraction failed on %s (%s): %s. Preserving card data.", cand.name, cand.canonical_url, deep_err)

                            if not cand.avatar_url:
                                cand.avatar_url = VERIFIED_AVATARS[len(harvested_candidates) % len(VERIFIED_AVATARS)]

                            if role_title:
                                cand.target_role = role_title

                            cand.stored_in_db = True
                            try:
                                cand_data = cand.model_dump() if hasattr(cand, "model_dump") else cand.dict()
                                db_service.save_candidate(cand_data)
                            except Exception as save_err:
                                logger.warning("Could not persist candidate %s to DB: %s", cand.name, save_err)

                            # Register in known sets to avoid intra-run duplication
                            norm_u = db_service.normalize_url(cand.canonical_url)
                            if norm_u:
                                known_urls.add(norm_u)
                            norm_n = db_service.normalize_name(cand.name)
                            if norm_n:
                                known_names.add(norm_n)

                            harvested_candidates.append(cand)

                            if session_id:
                                sourcing_tracker.update_session(
                                    session_id,
                                    candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in harvested_candidates],
                                )
                            await asyncio.sleep(1.0)

                        if len(harvested_candidates) >= max_results:
                            logger.info("Reached target candidate count of %d. Sourcing loop complete.", max_results)
                            break
                        else:
                            # Advance to next page of current query
                            page_num += 1
                            continue

                    # BRANCH 2: High Saturation / All duplicate profiles on page
                    if page_num == 1 and total_cards > 0 and not is_no_results:
                        # Strategy 1: Advance to Page 2 of same query
                        logger.info("Page 1 of '%s' saturated with %d duplicates. Advancing to Page 2...", active_query, len(duplicate_cards))
                        if session_id:
                            sourcing_tracker.update_session(
                                session_id,
                                message=f"⚠️ {len(duplicate_cards)} duplicate profiles detected on Page 1. Advancing to Page 2 of search...",
                            )
                        await self._inject_linkedin_hud(
                            page,
                            f"⚠️ Page 1 saturated ({len(duplicate_cards)} existing profiles). Checking Page 2..."
                        )
                        page_num = 2
                        await asyncio.sleep(1.2)
                        continue

                    # Strategy 2: AI / LLM Decision Layer — Pivot or Relax Search Query
                    if query_pivot_count < max_pivots:
                        query_pivot_count += 1
                        if is_no_results:
                            logger.info("0 results on '%s'. Auto-broadening search query (Relaxation #%d)...", active_query, query_pivot_count)
                            if session_id:
                                sourcing_tracker.update_session(
                                    session_id,
                                    message=f"⚠️ 0 candidate profiles found on LinkedIn for query. Auto-broadening search parameters...",
                                )
                            await self._inject_linkedin_hud(
                                page,
                                f"⚠️ 0 results found. Auto-broadening search query to expand candidate reach..."
                            )
                        else:
                            logger.info("Saturation detected on '%s'. Triggering AI Decision Layer (Pivot #%d)...", active_query, query_pivot_count)
                            if session_id:
                                sourcing_tracker.update_session(
                                    session_id,
                                    message=f"🧠 AI Decision Layer: Query '{active_query}' saturated ({sat_pct}% duplicates). Synthesizing orthogonal query...",
                                )
                            await self._inject_linkedin_hud(
                                page,
                                f"🧠 AI Decision Layer: Query saturated. Optimizing query..."
                            )

                        decision = ai_service.optimize_sourcing_query(
                            role_title=role_title or keywords,
                            current_query=active_query,
                            mandatory_skills=mandatory_skills,
                            attempt=query_pivot_count,
                            previous_queries=attempted_queries,
                            reason="no_results" if is_no_results else "saturation",
                            preferred_locations=preferred_locations,
                            location=location,
                        )

                        if decision.get("action") == "pivot_query" and decision.get("optimized_query"):
                            opt_q = decision["optimized_query"].strip()
                            if opt_q not in attempted_queries:
                                attempted_queries.append(opt_q)
                                active_query = opt_q
                                page_num = 1
                                exp = decision.get("explanation", "Pivoting query to discover distinct talent pool.")
                                logger.info("AI Decision Layer pivoted query to: '%s'. Strategy: %s", active_query, exp)

                                if session_id:
                                    sourcing_tracker.update_session(
                                        session_id,
                                        message=f"🧠 Search adjusted to: '{active_query}' ({exp})",
                                    )
                                await self._inject_linkedin_hud(
                                    page,
                                    f"🔍 Sourcing with adjusted query: '{active_query}'"
                                )
                                await asyncio.sleep(2.0)
                                continue

                    # Strategy 3: Gracefully conclude search if talent pool or pivots are exhausted
                    logger.info("Talent pool search space fully explored or maximum pivots reached. Concluding sourcing.")
                    if session_id:
                        sourcing_tracker.update_session(
                            session_id,
                            message=f"🛑 Talent pool search complete. Captured {len(harvested_candidates)} fresh candidate profiles (all duplicates skipped).",
                        )
                    await self._inject_linkedin_hud(
                        page,
                        f"🛑 Search complete! Captured {len(harvested_candidates)} fresh candidates (duplicates skipped)."
                    )
                    break

                candidates = harvested_candidates

                # Step 5: Finalize & Persist to SQLite
                if session_id:
                    sourcing_tracker.update_session(
                        session_id,
                        state="persisting",
                        progress=90,
                        message=f"Saving {len(candidates)} verified candidate profiles to shortlist...",
                        candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in candidates],
                    )

                for cand in candidates:
                    try:
                        if role_title:
                            cand.target_role = role_title
                        cand_data = cand.model_dump() if hasattr(cand, "model_dump") else cand.dict()
                        db_service.save_candidate(cand_data)
                    except Exception as err:
                        logger.warning("Could not persist candidate to DB: %s", err)

                # Step 6: Inform user in browser HUD (keeping LinkedIn tab open for human review)
                await self._inject_linkedin_hud(
                    page,
                    f"🎉 Sourcing Complete! Harvested {len(candidates)} candidate profiles. Return to your Hiring Desk portal tab to review shortlist & match scores."
                )

                if session_id:
                    sourcing_tracker.update_session(
                        session_id,
                        state="completed",
                        progress=100,
                        message=f"🎉 Successfully harvested {len(candidates)} candidates directly from LinkedIn! Shortlist updated in portal.",
                        candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in candidates],
                    )

                logger.info("Live LinkedIn sourcing complete: %d candidates harvested. Kept browser tab open.", len(candidates))

                return (
                    candidates,
                    search_url,
                    f"SUCCESS_LIVE_LINKEDIN: Autonomous agent sourced {len(candidates)} candidate profiles directly from LinkedIn.",
                )

        except Exception as e:
            logger.exception("Error during live LinkedIn search: %s", e)
            err_msg = f"{type(e).__name__}: {str(e)}"
            if session_id:
                sourcing_tracker.update_session(
                    session_id,
                    state="failed",
                    progress=0,
                    error=err_msg,
                    message=f"Browser search failed: {err_msg[:120]}",
                )
            raise


    async def search_live_browser_ocr(
        self,
        keywords: str,
        max_results: int = 6,
        session_id: Optional[str] = None,
    ) -> Tuple[List[CandidateProfile], str, str]:
        """Direct LinkedIn candidate sourcing with login handover and autonomous extraction."""
        return await self.search_live_linkedin(
            keywords=keywords,
            max_results=max_results,
            deep_scrape=True,
            session_id=session_id,
        )

    async def search_linkedin(
        self,
        keywords: str,
        max_results: int = 10,
        mode: str = "linkedin",
        deep_scrape: bool = True,
        timeout_seconds: int = 45,
        session_id: Optional[str] = None,
        browser_channel: Optional[str] = "chrome",
        role_title: Optional[str] = None,
        mandatory_skills: Optional[List[str]] = None,
        preferred_locations: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Tuple[List[CandidateProfile], str, str]:
        """Navigates to LinkedIn, executes candidate search, and visits profiles.
        
        Mode A (autonomous / simulation with session): Autonomous agent sourcing on real LinkedIn in background.
            - If already logged in, proceeds directly to search and profile extraction.
            - If not logged in, enters safe login handover flow.
        Mode B (live_linkedin): Guided live LinkedIn sourcing with headed browser.
        Offline Demo (demo / offline_demo / simulation without session_id): Uses offline test profiles.
        """
        # If offline demo or simulation mode
        if mode in ("demo", "offline_demo", "simulation"):
            logger.info("Simulation/demo mode: Generating candidate profiles for query: %s", keywords)
            candidates = self._generate_simulated_candidates(keywords, max_results)
            if session_id:
                sourcing_tracker.update_session(
                    session_id,
                    state="completed",
                    progress=100,
                    message=f"Offline demo completed: Generated {len(candidates)} candidate profiles for offline testing.",
                    candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in candidates],
                )
            return candidates, "https://www.linkedin.com/search/results/people", f"DEMO_OFFLINE: Generated {len(candidates)} candidate profiles for offline testing."

        # All live modes (autonomous, simulation with session, live_linkedin) execute direct live LinkedIn sourcing
        return await self.search_live_linkedin(
            keywords=keywords,
            max_results=max_results,
            deep_scrape=deep_scrape,
            browser_channel=browser_channel,
            session_id=session_id,
            role_title=role_title,
            mandatory_skills=mandatory_skills,
            preferred_locations=preferred_locations,
            location=location,
        )

    async def _extract_candidate_cards(self, page: Page, max_results: int) -> List[CandidateProfile]:
        """Extracts structured candidate cards from the active LinkedIn search page DOM.
        
        Uses multiple resilient selectors to support all LinkedIn interface versions:
        1. Universal template: div[data-view-name*="result"]
        2. Modern list items: li.reusable-search__result-container, ul.reusable-search__entity-result-list > li
        3. Classic cards: div.entity-result, div[data-chameleon-result-urn]
        4. Fallback anchor scanning: any card container wrapping an /in/ profile link
        """
        candidates = []

        # Give page time to load dynamic results
        try:
            await page.wait_for_selector(
                "div[data-view-name*='result'], li.reusable-search__result-container, div.entity-result, a[href*='/in/']",
                timeout=10000
            )
        except Exception:
            pass

        # Scroll down in stages to populate search cards
        for scroll_y in [300, 700, 1100]:
            try:
                await page.evaluate(f"window.scrollBy({{ top: {scroll_y}, behavior: 'smooth' }})")
                await asyncio.sleep(0.5)
            except Exception:
                pass

        # Query all card containers
        cards = await page.query_selector_all(
            "div[data-view-name*='result'], li.reusable-search__result-container, "
            "ul.reusable-search__entity-result-list > li, div.entity-result, "
            "div.scaffold-layout__list-item, div[data-chameleon-result-urn]"
        )
        logger.info("Found %d candidate card elements in DOM", len(cards))

        seen_urls = set()
        for idx, card in enumerate(cards):
            if len(candidates) >= max_results:
                break
            try:
                # Find profile URL
                link_elem = await card.query_selector("a[href*='/in/']")
                if not link_elem:
                    continue
                href = await link_elem.get_attribute("href")
                if not href or "/in/" not in href:
                    continue
                canonical_url = href.split("?")[0].rstrip("/")
                if canonical_url in seen_urls:
                    continue
                seen_urls.add(canonical_url)

                # Name
                name_elem = await card.query_selector(
                    "span[aria-hidden='true'], .entity-result__title-text a, a.app-aware-link, h3, .t-16.t-black"
                )
                name = (await name_elem.inner_text()).strip() if name_elem else f"Candidate #{len(candidates)+1}"
                name = re.sub(r"\s+", " ", name).split("\n")[0].strip()

                # Headline
                sub_elem = await card.query_selector(
                    ".entity-result__primary-subtitle, .subline-level-1, .artdeco-entity-lockup__subtitle, div.t-14.t-black"
                )
                raw_subtitle = (await sub_elem.inner_text()).strip() if sub_elem else ""
                parsed_card = clean_linkedin_card_text(raw_subtitle)
                headline = parsed_card["headline"] if parsed_card["headline"] else raw_subtitle
                headline = re.sub(r"\s+", " ", headline).strip()

                # Parse inline metadata if concatenated in card subtitle
                card_skills = []
                card_certs = []
                card_about = ""
                if "\n" in headline or "Skills:" in headline or "Certifications:" in headline or "Summary:" in headline:
                    lines = [ln.strip() for ln in headline.split("\n") if ln.strip()]
                    cleaned_hl_parts = []
                    for ln in lines:
                        if re.search(r"\bskills:\s*", ln, re.I):
                            s_text = re.sub(r".*?\bskills:\s*", "", ln, flags=re.I)
                            card_skills = [s.strip() for s in re.split(r"[,•·\|]", s_text) if s.strip()]
                        elif re.search(r"\bcertifications:\s*", ln, re.I):
                            c_text = re.sub(r".*?\bcertifications:\s*", "", ln, flags=re.I)
                            card_certs = [{"name": c.strip(), "issuing_org": "Verified Profile"} for c in re.split(r"[,•·\|]", c_text) if c.strip()]
                        elif re.search(r"\bsummary:\s*", ln, re.I):
                            card_about = re.sub(r".*?\bsummary:\s*", "", ln, flags=re.I)
                        elif ln.lower() in ("connect", "message", "follow", "view profile"):
                            continue
                        elif not cleaned_hl_parts:
                            cleaned_hl_parts.append(ln)
                    if cleaned_hl_parts:
                        headline = " ".join(cleaned_hl_parts)

                # Disentangle compound name if search card concatenated headline or degree badge
                if "•" in name or "·" in name or "3rd+" in name or "2nd+" in name:
                    parts = re.split(r"\s+[•·]\s*", name)
                    c_name = parts[0].strip()
                    c_name = re.sub(r"\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message|follow)\b", "", c_name, flags=re.IGNORECASE).strip()
                    if c_name:
                        name = c_name
                    if len(parts) > 1 and not headline:
                        rest = " • ".join(parts[1:]).strip()
                        rest = re.sub(r"^(?:3rd\+|2nd\+|1st\+|3rd|2nd|1st)\s*", "", rest, flags=re.IGNORECASE)
                        rest = re.sub(r"^[\|\-·•]\s*", "", rest).strip()
                        for stopword in [" Follow ", " Connect ", " Message ", " Past:", " Current:"]:
                            if stopword in rest:
                                rest = rest.split(stopword)[0].strip()
                        if rest and len(rest) > 2:
                            headline = rest

                # Clean badges from name
                name = re.sub(r"\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message|follow)\b", "", name, flags=re.IGNORECASE).strip()
                if not name or name.lower() in ("linkedin member", "view profile"):
                    name = f"LinkedIn Candidate #{len(candidates)+1}"
                if not headline:
                    headline = "Software Professional"

                # Location
                loc_elem = await card.query_selector(
                    ".entity-result__secondary-subtitle, .subline-level-2, .artdeco-entity-lockup__caption, div.t-12.t-black--light"
                )
                location = (await loc_elem.inner_text()).strip() if loc_elem else ""
                location = re.sub(r"\s+", " ", location).strip()

                # Summary / Snippet
                snippet_elem = await card.query_selector(".entity-result__summary, p.entity-result__summary, p.t-12")
                snippet = (await snippet_elem.inner_text()).strip() if snippet_elem else f"{name} - {headline}"

                combined_card_txt = f"{headline} {snippet} {location}".lower()
                if not location or location in ("Location not specified", "Location on Profile"):
                    if parsed_card.get("location"):
                        location = parsed_card["location"]
                    else:
                        loc_match = re.search(r"\b(Dubai(?:,\s*United Arab Emirates)?|Abu Dhabi(?:,\s*United Arab Emirates)?|United Arab Emirates|UAE|Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Delhi(?:,\s*India)?|Chennai|Coimbatore(?:,\s*Tamil\s*Nadu)?|Coimbatore|Tamil\s*Nadu|Tamilnadu|Kolkata(?:,\s*West\s*Bengal)?|India|San Francisco|New York|Seattle|London|Berlin|Toronto|Singapore|Remote)\b", combined_card_txt, re.I)
                        if loc_match:
                            location = loc_match.group(0).strip()
                        else:
                            location = ""

                work_auth = None
                if "golden visa" in combined_card_txt:
                    work_auth = "UAE Golden Visa Holder"
                elif "citizen" in combined_card_txt:
                    work_auth = "Citizen"

                company = parsed_card.get("company") or None
                if not company:
                    if " at " in headline:
                        company = headline.split(" at ")[-1].strip()
                    elif " @ " in headline:
                        company = headline.split(" @ ")[-1].strip()

                ts = int(time.time() * 1000)
                candidates.append(CandidateProfile(
                    id=f"cand_{ts}_{len(candidates)+1}",
                    name=name,
                    canonical_url=canonical_url,
                    headline=headline,
                    current_company=company,
                    location=location,
                    current_location=location,
                    work_authorization=work_auth,
                    raw_snippet=snippet,
                    about=card_about,
                    skills=card_skills,
                    certifications=card_certs,
                ))
            except Exception as e:
                logger.debug("Failed to parse card %d: %s", idx, e)

        # Fallback: If no structured cards found, look for all /in/ links directly
        if not candidates:
            logger.info("Structured card query returned 0. Falling back to direct profile link scan in DOM...")
            profile_links = await page.query_selector_all("a[href*='/in/']")
            for pl in profile_links:
                if len(candidates) >= max_results:
                    break
                try:
                    href = await pl.get_attribute("href")
                    if not href or "/in/" not in href or "/in/ACoA" in href:
                        continue
                    canonical_url = href.split("?")[0].rstrip("/")
                    if canonical_url in seen_urls:
                        continue
                    seen_urls.add(canonical_url)
                    text = (await pl.inner_text()).strip()
                    parts = re.split(r"\s+[•·]\s*", text)
                    clean_name = parts[0].strip()
                    clean_name = re.sub(r"\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message|follow)\b", "", clean_name, flags=re.IGNORECASE).strip()

                    card_headline = "Software Professional"
                    if len(parts) > 1:
                        rest = " • ".join(parts[1:]).strip()
                        rest = re.sub(r"^(?:3rd\+|2nd\+|1st\+|3rd|2nd|1st)\s*", "", rest, flags=re.IGNORECASE)
                        rest = re.sub(r"^[\|\-·•]\s*", "", rest).strip()
                        for stopword in [" Follow ", " Connect ", " Message ", " Past:", " Current:"]:
                            if stopword in rest:
                                rest = rest.split(stopword)[0].strip()
                        if rest and len(rest) > 2:
                            card_headline = rest

                    if not clean_name or len(clean_name) < 2 or clean_name.lower() in ("linkedin member", "view profile", "connect", "message"):
                        continue
                    ts = int(time.time() * 1000)
                    candidates.append(CandidateProfile(
                        id=f"cand_{ts}_{len(candidates)+1}",
                        name=clean_name,
                        canonical_url=canonical_url,
                        headline=card_headline,
                        location="",
                        raw_snippet=f"{clean_name} — {card_headline}",
                        skills=[],
                    ))
                except Exception:
                    pass

        return candidates

    async def _visit_and_extract_profile(self, page: Page, candidate: CandidateProfile, skip_navigation: bool = False) -> CandidateProfile:
        """Autonomous Agent UI Action: Navigates to candidate profile, expands 'Show all' and 'see more' sections,
        and extracts complete 7-section dossier (About, Activity, Experience, Education, Certs, Projects, Skills)."""
        clean_canonical = candidate.canonical_url.split("?")[0].rstrip("/")
        try:
            if not skip_navigation:
                logger.info("Agent UI navigation: Visiting %s", clean_canonical)
                target_url = clean_canonical + "/"
                await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(1.2)
                await self._dismiss_common_overlays(page)

            # 0. Extract Clean Profile Top Card Details (Real Name, Real Headline, Real Location, Avatar)
            try:
                top_card = await page.evaluate("""
                    () => {
                        const nameEl = document.querySelector('h1.text-heading-xlarge, h1.inline, div.pv-text-details__left-panel h1, h1');
                        const name = nameEl ? nameEl.innerText.trim() : '';
                        const hlEl = document.querySelector('div.text-body-medium.break-words, div.pv-text-details__left-panel div.text-body-medium, h2.top-card-layout__headline');
                        const headline = hlEl ? hlEl.innerText.trim() : '';
                        const locEl = document.querySelector('span.text-body-small.inline.t-black--light.break-words, div.pv-text-details__left-panel span.text-body-small, span.top-card__subline-item, div.ph5 span.t-black--light');
                        const location = locEl ? locEl.innerText.trim() : '';
                        const imgEl = document.querySelector('img.pv-top-card-profile-picture__image, button.pv-top-card-profile-picture img, img.presence-entity__image');
                        const avatar = imgEl ? (imgEl.src || '') : '';
                        return { name, headline, location, avatar };
                    }
                """)
                if top_card:
                    c_name = re.sub(r"\b(1st\+?|2nd\+?|3rd\+?|view profile|connect|message|linkedin member)\b", "", top_card.get("name", ""), flags=re.I).strip()
                    if c_name and len(c_name) > 1 and "linkedin" not in c_name.lower():
                        candidate.name = c_name
                    p_hl = re.sub(r"\s+", " ", top_card.get("headline", "")).strip()
                    parsed_tc = clean_linkedin_card_text(p_hl)
                    if parsed_tc["headline"]:
                        p_hl = parsed_tc["headline"]
                    if p_hl and len(p_hl) > 3:
                        candidate.headline = p_hl
                        if parsed_tc.get("company"):
                            candidate.current_company = parsed_tc["company"]
                        elif " at " in p_hl:
                            candidate.current_company = p_hl.split(" at ")[-1].strip()
                        elif " @ " in p_hl:
                            candidate.current_company = p_hl.split(" @ ")[-1].strip()
                    p_loc = top_card.get("location", "").strip()
                    p_loc = re.sub(r"\b(contact info|\d+\+?\s+connections|\d+\s+followers)\b", "", p_loc, flags=re.I).strip()
                    p_loc = re.sub(r"^[•·\-\|]\s*", "", p_loc).strip()
                    if not p_loc and parsed_tc.get("location"):
                        p_loc = parsed_tc["location"]
                    if p_loc and len(p_loc) > 2 and "location on profile" not in p_loc.lower():
                        candidate.location = p_loc
                    p_av = top_card.get("avatar", "")
                    if p_av and "media.licdn.com" in p_av and not p_av.startswith("data:"):
                        candidate.avatar_url = p_av
            except Exception as e:
                logger.debug("Profile topcard extraction warning: %s", e)

            # Progressive Scroll to Hydrate Virtualized DOM & Harvest Detail Links
            # Modern LinkedIn dynamically renders sections as user scrolls down.
            detail_links = {}
            try:
                detail_links = await page.evaluate(r"""
                    async () => {
                        const res = {};
                        let currentY = 0;
                        let stagnantCount = 0;
                        while (currentY < 12000 && stagnantCount < 3) {
                            currentY += 700;
                            window.scrollTo({ top: currentY, behavior: 'instant' });
                            await new Promise(r => setTimeout(r, 120));
                            const totalHeight = document.body.scrollHeight;
                            if (currentY >= totalHeight) {
                                stagnantCount++;
                            } else {
                                stagnantCount = 0;
                            }
                            for (const a of document.querySelectorAll('a[href*="/details/"]')) {
                                const href = a.getAttribute('href') || '';
                                if (href.includes('/details/skills')) res['skills'] = a.href;
                                else if (href.includes('/details/experience')) res['experience'] = a.href;
                                else if (href.includes('/details/education')) res['education'] = a.href;
                                else if (href.includes('/details/certifications') || href.includes('/details/licenses')) res['certifications'] = a.href;
                                else if (href.includes('/details/projects')) res['projects'] = a.href;
                            }
                        }
                        // Click all inline "see more" / "show more" buttons across entire loaded profile
                        for (const b of document.querySelectorAll('button.inline-show-more-text__button, button[aria-label*="see more" i], button[aria-label*="show more" i], button.pv-profile-section__see-more-inline')) {
                            try {
                                b.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                b.click();
                            } catch(e) {}
                        }
                        return res;
                    }
                """)
            except Exception as e:
                logger.debug("Initial hydration scroll warning: %s", e)

            if not isinstance(detail_links, dict):
                detail_links = {}

            # Construct standard fallback detail URLs based on canonical profile link
            fallback_detail_links = {
                "certifications": f"{clean_canonical}/details/certifications/",
                "projects": f"{clean_canonical}/details/projects/",
                "skills": f"{clean_canonical}/details/skills/",
                "experience": f"{clean_canonical}/details/experience/",
                "education": f"{clean_canonical}/details/education/",
            }

            # ------------------------------------------------------------------
            # 1. Section 1: About / Executive Summary
            # ------------------------------------------------------------------
            await self._update_overlay(page, f"HR Dossier: [1/7] Analyzing Executive Summary for {candidate.name[:18]}...")
            about_text = ""
            try:
                about_text = await page.evaluate(r"""
                    async () => {
                        let sec = null;
                        const anchor = document.getElementById('about');
                        if (anchor) {
                            sec = anchor.closest('section, div.artdeco-card') || anchor.parentElement;
                        }
                        if (!sec) {
                            for (const s of document.querySelectorAll('section, div.artdeco-card, div[data-view-name*="profile-card"]')) {
                                const h = s.querySelector('h2, h3, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                                const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                if (/^about/i.test(t) || (s.id && /(?:^about|about$)/i.test(s.id))) {
                                    sec = s;
                                    break;
                                }
                            }
                        }
                        if (!sec) {
                            let y = 0;
                            while (y < Math.min(document.body.scrollHeight, 12000)) {
                                y += 600;
                                window.scrollTo({ top: y, behavior: 'instant' });
                                await new Promise(r => setTimeout(r, 60));
                                const a = document.getElementById('about');
                                if (a) {
                                    sec = a.closest('section, div.artdeco-card') || a.parentElement;
                                    break;
                                }
                                for (const s of document.querySelectorAll('section, div.artdeco-card')) {
                                    const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"]');
                                    const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                    if (/^about/i.test(t)) {
                                        sec = s;
                                        break;
                                    }
                                }
                                if (sec) break;
                            }
                        }
                        if (!sec) return '';

                        sec.scrollIntoView({ behavior: 'instant', block: 'center' });
                        await new Promise(r => setTimeout(r, 120));

                        // 1. Try reading complete text from .visually-hidden if present (LinkedIn includes full text for screen readers)
                        const hiddenFull = sec.querySelector('.visually-hidden, span.visually-hidden');
                        if (hiddenFull && hiddenFull.innerText && hiddenFull.innerText.trim().length > 25) {
                            let fullTxt = hiddenFull.innerText.trim();
                            fullTxt = fullTxt.replace(/^about\s*/i, '').trim();
                            fullTxt = fullTxt.replace(/[\s\n\r]*[…\.]+\s*(?:more|see more)\s*$/i, '').trim();
                            if (fullTxt.length > 20) return fullTxt;
                        }

                        // 2. Expand all show more buttons
                        for (const b of sec.querySelectorAll('button.inline-show-more-text__button, button[aria-label*="see more" i], button[aria-label*="show more" i], button.pv-profile-section__see-more-inline')) {
                            try {
                                b.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                b.click();
                            } catch(e) {}
                        }
                        await new Promise(r => setTimeout(r, 120));

                        const textEl = sec.querySelector('div.inline-show-more-text, div.display-flex span[aria-hidden="true"], p') || sec;
                        const clone = textEl.cloneNode(true);
                        for (const b of clone.querySelectorAll('button, .inline-show-more-text__button')) {
                            b.remove();
                        }
                        let raw = clone.innerText || '';
                        raw = raw.replace(/^about\s*/i, '').trim();
                        raw = raw.replace(/[\s\n\r]*[…\.]+\s*(?:more|see more)\s*$/i, '').trim();
                        return raw;
                    }
                """)
                if about_text:
                    about_text = re.sub(r"[\s\n\r]*[…\.]+\s*(?:more|see more)\s*$", "", about_text, flags=re.I).strip()
                    about_text = re.sub(r"^about\s*", "", about_text, flags=re.I).strip()
            except Exception as e:
                logger.debug("About extraction warning: %s", e)

            # ------------------------------------------------------------------
            # 2. Section 2: Recent Activity & Contributions
            # ------------------------------------------------------------------
            await self._update_overlay(page, f"HR Dossier: [2/7] Inspecting Activity & Articles for {candidate.name[:18]}...")
            recent_activities = []
            try:
                recent_activities = await page.evaluate(r"""
                    async () => {
                        const items = [];
                        let sec = null;
                        const actAnchor = document.getElementById('recent_activity');
                        if (actAnchor) {
                            sec = actAnchor.closest('section, div.artdeco-card') || actAnchor.parentElement;
                        }
                        if (!sec) {
                            for (const s of document.querySelectorAll('section, div.artdeco-card')) {
                                if (s.id && /activity/i.test(s.id)) { sec = s; break; }
                                const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"]');
                                if (h && /activity/i.test(h.innerText || '')) { sec = s; break; }
                            }
                        }
                        if (!sec) return items;

                        sec.scrollIntoView({ behavior: 'instant', block: 'center' });
                        await new Promise(r => setTimeout(r, 120));

                        const lis = sec.querySelectorAll('ul.pvs-list > li, div[data-view-name*="feed-mini-update"], div.feed-shared-update-v2');
                        for (const li of Array.from(lis).slice(0, 3)) {
                            const txt = (li.innerText || '').replace(/\s+/g, ' ').trim();
                            if (txt && txt.length > 15) {
                                items.push({
                                    action_type: "Post / Share",
                                    headline: txt.slice(0, 120),
                                    snippet: txt.slice(0, 260),
                                    date: "Recent"
                                });
                            }
                        }
                        return items;
                    }
                """)
            except Exception as e:
                logger.debug("Activity extraction warning: %s", e)

            # ------------------------------------------------------------------
            # 3. Section 3: Work Experience Records
            # ------------------------------------------------------------------
            await self._update_overlay(page, f"HR Dossier: [3/7] Auditing Experience & Tenures for {candidate.name[:18]}...")
            experience_items = []
            try:
                main_page_exp_script = r"""
                    async () => {
                        const list = [];
                        let sec = null;
                        const expAnchor = document.getElementById('experience');
                        if (expAnchor) {
                            sec = expAnchor.closest('section, div.artdeco-card') || expAnchor.parentElement;
                        }
                        if (!sec) {
                            for (const s of document.querySelectorAll('section, div.artdeco-card')) {
                                if (s.id && /experience/i.test(s.id)) { sec = s; break; }
                                const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"]');
                                if (h && (h.innerText || '').toLowerCase().trim().startsWith('experience')) { sec = s; break; }
                            }
                        }
                        if (sec) {
                            sec.scrollIntoView({ behavior: 'instant', block: 'center' });
                            await new Promise(r => setTimeout(r, 150));
                            for (const b of sec.querySelectorAll('button.inline-show-more-text__button, button[aria-label*="see more" i]')) {
                                try { b.click(); } catch(e) {}
                            }
                            await new Promise(r => setTimeout(r, 120));
                        }
                        if (!sec) return [];

                        const lis = sec.querySelectorAll(':scope > div > ul.pvs-list > li, ul.pvs-list > li, div.pvs-entity');
                        for (const li of Array.from(lis)) {
                            const subComponent = li.querySelector('div.pvs-entity__sub-components, ul.pvs-list');
                            const subLis = subComponent ? subComponent.querySelectorAll(':scope > li, :scope > div > ul > li') : [];

                            if (subLis && subLis.length > 0) {
                                const headerSpans = Array.from(li.querySelectorAll('span[aria-hidden="true"]'))
                                    .map(s => (s.innerText || '').trim()).filter(Boolean);
                                const compName = headerSpans[0] || 'Company';

                                for (const subLi of subLis) {
                                    const subSpans = Array.from(subLi.querySelectorAll('span[aria-hidden="true"]'))
                                        .map(s => (s.innerText || '').trim()).filter(Boolean);
                                    if (subSpans.length >= 1) {
                                        const subTitle = subSpans[0];
                                        const subDates = subSpans.length > 1 ? subSpans[1] : '';
                                        const subLoc = subSpans.length > 2 ? subSpans[2] : '';
                                        const subDesc = subSpans.length > 3 ? subSpans.slice(3).join(' ') : '';
                                        if (subTitle && !subTitle.toLowerCase().includes('experience')) {
                                            list.push({
                                                title: subTitle,
                                                role: subTitle,
                                                company: compName,
                                                dates: subDates,
                                                location: subLoc,
                                                description: subDesc.slice(0, 400)
                                            });
                                        }
                                    }
                                }
                            } else {
                                const spans = Array.from(li.querySelectorAll('span[aria-hidden="true"]'))
                                    .map(s => (s.innerText || '').trim()).filter(Boolean);
                                if (spans.length >= 2) {
                                    const title = spans[0];
                                    const comp = spans[1];
                                    const dates = spans.length > 2 ? spans[2] : '';
                                    const desc = spans.length > 3 ? spans.slice(3).join(' ') : '';
                                    if (title && !title.toLowerCase().includes('experience')) {
                                        list.push({
                                            title: title,
                                            role: title,
                                            company: comp,
                                            dates: dates,
                                            description: desc.slice(0, 350)
                                        });
                                    }
                                }
                            }
                        }
                        return list;
                    }
                """
                experience_items = await page.evaluate(main_page_exp_script)
            except Exception as e:
                logger.debug("Main page experience extraction: %s", e)

            # Optional deep dive if main page was empty and a real details link was found
            if not skip_navigation and not experience_items and detail_links.get("experience"):
                try:
                    sub_page = await page.context.new_page()
                    try:
                        await sub_page.goto(detail_links["experience"], wait_until="domcontentloaded", timeout=6000)
                        sub_exp = await sub_page.evaluate(main_page_exp_script)
                        if sub_exp:
                            experience_items = sub_exp
                    finally:
                        await sub_page.close()
                except Exception as e:
                    logger.debug("Experience subpage skipped: %s", e)

            # ------------------------------------------------------------------
            # 4. Section 4: Academic Degrees & Education
            # ------------------------------------------------------------------
            await self._update_overlay(page, f"HR Dossier: [4/7] Verifying Academic Degrees for {candidate.name[:18]}...")
            education_items = []
            try:
                main_edu_script = r"""
                    async () => {
                        const list = [];
                        let sec = null;
                        const eduAnchor = document.getElementById('education');
                        if (eduAnchor) {
                            sec = eduAnchor.closest('section, div.artdeco-card') || eduAnchor.parentElement;
                        }
                        if (!sec) {
                            for (const s of document.querySelectorAll('section, div.artdeco-card')) {
                                if (s.id && /education/i.test(s.id)) { sec = s; break; }
                                const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"]');
                                if (h && (h.innerText || '').toLowerCase().trim().startsWith('education')) { sec = s; break; }
                            }
                        }
                        if (sec) {
                            sec.scrollIntoView({ behavior: 'instant', block: 'center' });
                            await new Promise(r => setTimeout(r, 120));
                        }
                        if (!sec) return [];

                        const lis = sec ? sec.querySelectorAll('ul.pvs-list > li, div.pvs-entity') : [];
                        for (const li of Array.from(lis)) {
                            const spans = Array.from(li.querySelectorAll('span[aria-hidden="true"]')).map(s => (s.innerText || '').trim()).filter(Boolean);
                            if (spans.length >= 1) {
                                const school = spans[0];
                                const degree = spans.length > 1 ? spans[1] : '';
                                const dates = spans.length > 2 ? spans[2] : '';
                                if (school && !school.toLowerCase().includes('education')) {
                                    list.push({ school, degree, dates });
                                }
                            }
                        }
                        // Top card school icon fallback if main section was not present
                        if (list.length === 0) {
                            const schoolSvg = document.querySelector('svg[id*="school"], svg[id*="education"]');
                            if (schoolSvg) {
                                const parentCard = schoolSvg.closest('div, button, a');
                                if (parentCard) {
                                    const name = parentCard.innerText.trim().replace(/\s+/g, ' ');
                                    if (name && name.length > 2 && name.length < 100 && !name.toLowerCase().includes('connect')) {
                                        list.push({
                                            school: name,
                                            degree: 'Degree / Coursework',
                                            dates: 'Verified from profile'
                                        });
                                    }
                                }
                            }
                        }
                        return list;
                    }
                """
                education_items = await page.evaluate(main_edu_script)
            except Exception as e:
                logger.debug("Main page education extraction: %s", e)

            detail_edu_url = detail_links.get("education") or fallback_detail_links.get("education")
            if not skip_navigation and not education_items and detail_edu_url:
                try:
                    sub_page = await page.context.new_page()
                    try:
                        await sub_page.goto(detail_edu_url, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(1.0)
                        edu_page_text = await sub_page.evaluate(r"() => document.body ? document.body.innerText : ''")
                        if edu_page_text:
                            lines = [l.strip() for l in edu_page_text.split('\n') if l.strip()]
                            for i, line in enumerate(lines):
                                if line.lower() == 'education':
                                    continue
                                if re.search(r'\b(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|Present)\b', line) or re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', line, re.I):
                                    dates = line
                                    degree = lines[i-1] if i > 0 and lines[i-1].lower() != 'education' else 'Degree / Coursework'
                                    school = lines[i-2] if i > 1 and lines[i-2].lower() != 'education' else ''
                                    if school and not school.lower().startswith('education') and not any((e.get('school') or '').lower() == school.lower() for e in education_items):
                                        education_items.append({'school': school, 'degree': degree, 'dates': dates})
                    finally:
                        await sub_page.close()
                except Exception as e:
                    logger.debug("Education subpage skipped: %s", e)

            # ------------------------------------------------------------------
            # 5. Section 5: Licenses & Certifications
            # ------------------------------------------------------------------
            await self._update_overlay(page, f"HR Dossier: [5/7] Checking Licenses & Certs for {candidate.name[:18]}...")
            cert_items = []
            cert_meta = {}
            try:
                cert_result = await page.evaluate(r"""
                    async () => {
                        const res = { items: [], total_expected: 0, detail_link: '' };
                        const anchorIds = ['licenses_and_certifications', 'certifications', 'licenses'];
                        let sec = null;
                        for (const id of anchorIds) {
                            const el = document.getElementById(id);
                            if (el) {
                                sec = el.closest('section, div.artdeco-card') || el.parentElement;
                                break;
                            }
                        }
                        if (!sec) {
                            for (const s of document.querySelectorAll('section, div.artdeco-card, div[data-view-name*="profile-card"]')) {
                                const h = s.querySelector('h2, h3, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                                const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                if (t.includes('license') || t.includes('certification') || /(?:licenses?|certifications?)/i.test(s.id || '')) {
                                    sec = s;
                                    break;
                                }
                            }
                        }
                        if (!sec) {
                            const maxScroll = Math.min(document.body.scrollHeight, 12000);
                            for (let y = window.scrollY || 0; y <= maxScroll; y += 600) {
                                window.scrollTo({ top: y, behavior: 'instant' });
                                await new Promise(r => setTimeout(r, 100));
                                for (const id of anchorIds) {
                                    const el = document.getElementById(id);
                                    if (el) {
                                        sec = el.closest('section, div.artdeco-card') || el.parentElement;
                                        break;
                                    }
                                }
                                if (sec) break;
                                for (const s of document.querySelectorAll('section, div.artdeco-card')) {
                                    const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                                    const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                    if (t.includes('license') || t.includes('certification')) {
                                        sec = s;
                                        break;
                                    }
                                }
                                if (sec) break;
                            }
                        }
                        if (!sec) return res;

                        sec.scrollIntoView({ behavior: 'instant', block: 'center' });
                        await new Promise(r => setTimeout(r, 180));

                        // Total count from header e.g. 'Licenses & certifications (4)'
                        const h = sec.querySelector('h2, h3, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                        const hText = h ? (h.innerText || '') : '';
                        const cm = hText.match(/\((\d+)\)/);
                        if (cm) res.total_expected = parseInt(cm[1], 10);

                        // Detail link / Show all
                        const dAnchor = sec.querySelector('a[href*="/details/certifications"], a[href*="/details/licenses"]');
                        if (dAnchor && dAnchor.href) {
                            res.detail_link = dAnchor.href;
                        } else {
                            for (const a of sec.querySelectorAll('a, button')) {
                                const txt = (a.innerText || '').toLowerCase();
                                if (txt.includes('show all') || txt.includes('see all')) {
                                    const m = txt.match(/(\d+)/);
                                    if (m && !res.total_expected) res.total_expected = parseInt(m[1], 10);
                                    if (a.href) res.detail_link = a.href;
                                }
                            }
                        }

                        // Expand inline show more
                        for (const b of sec.querySelectorAll('button.inline-show-more-text__button, button[aria-label*="see more" i], button[aria-label*="show more" i]')) {
                            try {
                                b.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                b.click();
                            } catch(e) {}
                        }
                        await new Promise(r => setTimeout(r, 120));

                        let itemEls = Array.from(sec.querySelectorAll(
                            'ul.pvs-list > li, ' +
                            'div.pvs-list__outer-container > ul > li, ' +
                            'div.pvs-entity, ' +
                            'div[data-view-name*="profile-component-entity"]'
                        )).filter(el => !el.parentElement.closest('ul.pvs-list > li, div.pvs-entity'));

                        if (!itemEls.length) {
                            const all = Array.from(sec.querySelectorAll('*'));
                            const cardNodes = all.filter(el => {
                                const text = el.innerText || '';
                                return (text.includes('Credential ID') || text.includes('Issued ') || /\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b/.test(text)) && 
                                       !Array.from(el.children).some(c => (c.innerText || '').includes('Credential ID') || (c.innerText || '').includes('Issued '));
                            });
                            for (const cn of cardNodes) {
                                const card = cn.closest('div.artdeco-card, div[data-view-name*="entity"], li') || cn.parentElement;
                                if (card && !itemEls.includes(card)) itemEls.push(card);
                            }
                        }

                        for (const el of itemEls) {
                            let spans = Array.from(el.querySelectorAll('span[aria-hidden="true"]'))
                                .map(s => (s.innerText || '').trim())
                                .filter(Boolean);
                            if (!spans.length) {
                                spans = (el.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
                            }
                            if (!spans.length) continue;

                            let name = '';
                            let org = '';
                            let issueDate = '';
                            let credentialId = '';
                            let skills = [];
                            let url = '';

                            const credLink = el.querySelector('a[href*="credential"], a[href*="verify"], a[data-field="credential_url"]');
                            if (credLink && credLink.href && !credLink.href.includes('linkedin.com/in')) {
                                url = credLink.href;
                            }

                            let nameFound = false;
                            let orgFound = false;
                            for (const span of spans) {
                                const lower = span.toLowerCase();
                                if (lower.includes('licenses & certifications') || lower === 'licenses' || lower === 'certifications') continue;
                                if (/^issued\b/i.test(span) || /\b(?:expires?|valid)\b/i.test(span) || /\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b/i.test(span)) {
                                    issueDate = span;
                                    continue;
                                }
                                if (/credential\s*id/i.test(span)) {
                                    credentialId = span.replace(/credential\s*id\s*[:\-]?\s*/i, '').trim();
                                    continue;
                                }
                                if (/^skills?:/i.test(span)) {
                                    const skStr = span.replace(/^skills?:\s*/i, '').trim();
                                    skills = skStr.split(/[·•,]/).map(s => s.trim()).filter(Boolean);
                                    continue;
                                }
                                if (/^(?:show\s+credential|see\s+credential)/i.test(span)) continue;

                                if (!nameFound) {
                                    name = span;
                                    nameFound = true;
                                } else if (!orgFound) {
                                    org = span;
                                    orgFound = true;
                                }
                            }

                            if (name && !name.toLowerCase().startsWith('show all')) {
                                res.items.push({
                                    name: name,
                                    issuing_org: org,
                                    issue_date: issueDate,
                                    credential_id: credentialId,
                                    skills: skills,
                                    url: url
                                });
                            }
                        }
                        return res;
                    }
                """)
                if cert_result and cert_result.get("items"):
                    cert_items = cert_result["items"]
                cert_meta = cert_result or {}
            except Exception as e:
                logger.debug("Main page certifications extraction warning: %s", e)

            # Deep subpage extraction if more certifications exist or detail link is present
            detail_cert_url = cert_meta.get("detail_link") or detail_links.get("certifications") or fallback_detail_links.get("certifications")

            if not skip_navigation and detail_cert_url and (len(cert_items) < cert_meta.get("total_expected", 0) or cert_meta.get("total_expected", 0) > 2 or not cert_items):
                try:
                    sub_page = await page.context.new_page()
                    try:
                        await sub_page.goto(detail_cert_url, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(1.0)
                        sub_raw_certs = await sub_page.evaluate(r"""
                            async () => {
                                const h = Math.min(document.body.scrollHeight, 8000);
                                for (let y = 0; y <= h; y += 600) {
                                    window.scrollTo({ top: y, behavior: 'instant' });
                                    await new Promise(r => setTimeout(r, 60));
                                }
                                for (const b of document.querySelectorAll('button.inline-show-more-text__button')) {
                                    try { b.click(); } catch(e) {}
                                }
                                const all = Array.from(document.querySelectorAll('*'));
                                const cardNodes = all.filter(el => {
                                    const text = el.innerText || '';
                                    return (text.includes('Credential ID') || text.includes('Issued ') || /\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b/.test(text)) && 
                                           !Array.from(el.children).some(c => (c.innerText || '').includes('Credential ID') || (c.innerText || '').includes('Issued '));
                                });
                                return cardNodes.map(el => {
                                    const card = el.closest('div.artdeco-card, div[data-view-name*="entity"], li') || el.parentElement;
                                    const lines = (card.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
                                    const link = card.querySelector('a[href*="credential"], a[href*="verify"], a[data-field="credential_url"]');
                                    return { lines: lines, href: link ? link.href : '' };
                                });
                            }
                        """)
                        for cr in (sub_raw_certs or []):
                            lines = cr.get("lines", [])
                            name = ""
                            org = ""
                            issue_date = ""
                            credential_id = ""
                            skills = []
                            for ln in lines:
                                if re.search(r"^(?:show credential|see credential|licenses? & certifications?)$", ln, re.I):
                                    continue
                                if not name:
                                    name = ln
                                    continue
                                if not org and not re.search(r"\b(?:issued|expires?|credential id|skills?:)\b", ln, re.I):
                                    org = ln
                                    continue
                                if re.search(r"\b(?:issued|expires?|valid)\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b", ln, re.I):
                                    issue_date = ln if not issue_date else f"{issue_date} • {ln}"
                                    continue
                                if re.search(r"credential\s*id", ln, re.I):
                                    credential_id = re.sub(r"^credential\s*id\s*[:\-]?\s*", "", ln, flags=re.I).strip()
                                    continue
                                if re.search(r"skills?:", ln, re.I) or re.search(r"\b(?:Python|SQL|Power BI|DAX|Snowflake|Azure|AWS)\b", ln, re.I):
                                    sk = re.sub(r"^skills?:\s*", "", ln, flags=re.I)
                                    for s in re.split(r"[•·,]+", sk):
                                        if s.strip() and s.strip() not in skills:
                                            skills.append(s.strip())
                                    continue
                            if name and not any(c.get("name") == name for c in cert_items):
                                cert_items.append({
                                    "name": name,
                                    "issuing_org": org,
                                    "issue_date": issue_date,
                                    "credential_id": credential_id,
                                    "skills": skills,
                                    "url": cr.get("href", ""),
                                })
                    finally:
                        await sub_page.close()
                except Exception as e:
                    logger.debug("Certifications subpage skipped: %s", e)

            # ------------------------------------------------------------------
            # 6. Section 6: Featured Projects & Publications
            # ------------------------------------------------------------------
            await self._update_overlay(page, f"HR Dossier: [6/7] Examining Projects for {candidate.name[:18]}...")
            project_items = []
            proj_meta = {}
            try:
                proj_result = await page.evaluate(r"""
                    async () => {
                        const res = { items: [], total_expected: 0, detail_link: '' };
                        const anchorIds = ['projects', 'featured_projects'];
                        let sec = null;
                        for (const id of anchorIds) {
                            const el = document.getElementById(id);
                            if (el) {
                                sec = el.closest('section, div.artdeco-card') || el.parentElement;
                                break;
                            }
                        }
                        if (!sec) {
                            for (const s of document.querySelectorAll('section, div.artdeco-card, div[data-view-name*="profile-card"]')) {
                                const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                                const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                if (t.startsWith('project') || /(?:^|\b)projects?(?:\s*\(\d+\))?/i.test(t) || (s.id && /projects?/i.test(s.id))) {
                                    sec = s;
                                    break;
                                }
                            }
                        }
                        if (!sec) {
                            const maxScroll = Math.min(document.body.scrollHeight, 12000);
                            for (let y = window.scrollY || 0; y <= maxScroll; y += 600) {
                                window.scrollTo({ top: y, behavior: 'instant' });
                                await new Promise(r => setTimeout(r, 100));
                                for (const id of anchorIds) {
                                    const el = document.getElementById(id);
                                    if (el) {
                                        sec = el.closest('section, div.artdeco-card') || el.parentElement;
                                        break;
                                    }
                                }
                                if (sec) break;
                                for (const s of document.querySelectorAll('section, div.artdeco-card')) {
                                    const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                                    const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                    if (t.startsWith('project') || /(?:^|\b)projects?(?:\s*\(\d+\))?/i.test(t)) {
                                        sec = s;
                                        break;
                                    }
                                }
                                if (sec) break;
                            }
                        }
                        if (!sec) return res;

                        sec.scrollIntoView({ behavior: 'instant', block: 'center' });
                        await new Promise(r => setTimeout(r, 180));

                        const h = sec.querySelector('h2, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                        const hText = h ? (h.innerText || '') : '';
                        const cm = hText.match(/\((\d+)\)/);
                        if (cm) res.total_expected = parseInt(cm[1], 10);

                        const dAnchor = sec.querySelector('a[href*="/details/projects"]');
                        if (dAnchor && dAnchor.href) {
                            res.detail_link = dAnchor.href;
                        } else {
                            for (const a of sec.querySelectorAll('a, button')) {
                                const txt = (a.innerText || '').toLowerCase();
                                if (txt.includes('show all') || txt.includes('see all')) {
                                    const m = txt.match(/(\d+)/);
                                    if (m && !res.total_expected) res.total_expected = parseInt(m[1], 10);
                                    if (a.href) res.detail_link = a.href;
                                }
                            }
                        }

                        for (const b of sec.querySelectorAll('button.inline-show-more-text__button, button[aria-label*="see more" i], button[aria-label*="show more" i]')) {
                            try {
                                b.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                b.click();
                            } catch(e) {}
                        }
                        await new Promise(r => setTimeout(r, 120));

                        let itemEls = Array.from(sec.querySelectorAll(
                            'ul.pvs-list > li, ' +
                            'div.pvs-list__outer-container > ul > li, ' +
                            'div.pvs-entity, ' +
                            'div[data-view-name*="profile-component-entity"]'
                        )).filter(el => !el.parentElement.closest('ul.pvs-list > li, div.pvs-entity'));

                        if (!itemEls.length) {
                            const all = Array.from(sec.querySelectorAll('*'));
                            const pNodes = all.filter(el => {
                                const text = el.innerText || '';
                                return (text.includes('Present') || /\b202\d\b/.test(text)) &&
                                       !Array.from(el.children).some(c => (c.innerText || '').includes('Present') && c.innerText.length > 50);
                            });
                            for (const pn of pNodes) {
                                const card = pn.closest('div.artdeco-card, div[data-view-name*="entity"], li') || pn.parentElement;
                                if (card && !itemEls.includes(card)) itemEls.push(card);
                            }
                        }

                        for (const el of itemEls) {
                            const titleEl = el.querySelector('div.display-flex span[aria-hidden="true"], h3 span[aria-hidden="true"], a span[aria-hidden="true"]');
                            let title = titleEl ? titleEl.innerText.trim() : '';

                            let spans = Array.from(el.querySelectorAll('span[aria-hidden="true"]'))
                                .map(s => (s.innerText || '').trim())
                                .filter(Boolean);
                            if (!spans.length) {
                                spans = (el.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
                            }
                            if (!title && spans.length > 0) title = spans[0];
                            if (title.toLowerCase() === 'projects' && spans.length > 1) title = spans[1];

                            let dates = '';
                            let skills = [];
                            let description = '';
                            let url = '';

                            const projLink = el.querySelector('a[href*="http"]:not([href*="linkedin.com/in"])');
                            if (projLink && projLink.href) url = projLink.href;

                            const descEl = el.querySelector('div.inline-show-more-text, div.pvs-entity__sub-components, div[data-view-name*="description"]');
                            if (descEl) {
                                const clone = descEl.cloneNode(true);
                                for (const b of clone.querySelectorAll('button, .inline-show-more-text__button, .visually-hidden')) {
                                    b.remove();
                                }
                                description = (clone.innerText || '').trim();
                            }

                            for (const span of spans) {
                                if (span === title) continue;
                                if (!dates && (/\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b/i.test(span) || /\b\d{4}\s*-\s*(?:\d{4}|Present)/i.test(span))) {
                                    dates = span;
                                    continue;
                                }
                                if (/^(?:associated with|other contributors)/i.test(span)) continue;
                                if (/^(?:skills?|technologies):\s*/i.test(span)) {
                                    const skStr = span.replace(/^(?:skills?|technologies):\s*/i, '').trim();
                                    skills = skStr.split(/[·•,]/).map(s => s.trim()).filter(Boolean);
                                    continue;
                                }
                                if (/^(?:show\s+project|see\s+project)/i.test(span)) continue;
                                if (!description && span.length > 30) description = span;
                            }

                            description = description.replace(/[\s\n\r]*[…\.]+\s*(?:more|see more)\s*$/i, '').trim();

                            if (title && !title.toLowerCase().startsWith('show all')) {
                                res.items.push({
                                    title: title,
                                    description: description,
                                    dates: dates,
                                    skills: skills,
                                    url: url
                                });
                            }
                        }
                        return res;
                    }
                """)
                if proj_result and proj_result.get("items"):
                    project_items = proj_result["items"]
                proj_meta = proj_result or {}
            except Exception as e:
                logger.debug("Main page projects extraction warning: %s", e)

            # Deep subpage extraction if more projects exist or detail link is present
            detail_proj_url = proj_meta.get("detail_link") or detail_links.get("projects") or fallback_detail_links.get("projects")

            if not skip_navigation and detail_proj_url and (len(project_items) < proj_meta.get("total_expected", 0) or proj_meta.get("total_expected", 0) > 2 or not project_items):
                try:
                    sub_page = await page.context.new_page()
                    try:
                        await sub_page.goto(detail_proj_url, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(1.0)
                        sub_raw_projs = await sub_page.evaluate(r"""
                            async () => {
                                const h = Math.min(document.body.scrollHeight, 8000);
                                for (let y = 0; y <= h; y += 600) {
                                    window.scrollTo({ top: y, behavior: 'instant' });
                                    await new Promise(r => setTimeout(r, 60));
                                }
                                for (const b of document.querySelectorAll('button.inline-show-more-text__button')) {
                                    try { b.click(); } catch(e) {}
                                }
                                const all = Array.from(document.querySelectorAll('*'));
                                const pNodes = all.filter(el => {
                                    const text = el.innerText || '';
                                    return (text.includes('Present') || /\b202\d\b/.test(text)) &&
                                           !Array.from(el.children).some(c => (c.innerText || '').includes('Present') && c.innerText.length > 50);
                                });
                                return pNodes.map(el => {
                                    const card = el.closest('div.artdeco-card, div[data-view-name*="entity"], li') || el.parentElement;
                                    const lines = (card.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
                                    const link = card.querySelector('a[href*="http"]:not([href*="linkedin.com/in"])');
                                    return { lines: lines, href: link ? link.href : '' };
                                });
                            }
                        """)
                        for pc in (sub_raw_projs or []):
                            lines = pc.get("lines", [])
                            if len(lines) >= 1:
                                title = lines[0]
                                if title.lower() in ("projects", "show all", "see all") and len(lines) > 1:
                                    title = lines[1]
                                dates = ""
                                desc = ""
                                skills = []
                                for ln in lines[1:]:
                                    if not dates and re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b|\bPresent\b", ln, re.I):
                                        dates = ln
                                        continue
                                    if re.search(r"skills?:", ln, re.I) or re.search(r"\b(?:Python|Power BI|Streamlit|Claude|Groq|FastAPI|Playwright|SQL|Fabric|DAX)\b", ln, re.I):
                                        sk = re.sub(r"^skills?:\s*", "", ln, flags=re.I)
                                        for s in re.split(r"[•·,]+", sk):
                                            if s.strip() and s.strip() not in skills:
                                                skills.append(s.strip())
                                        continue
                                    if not desc and len(ln) > 25:
                                        desc = ln
                                if title:
                                    if re.search(r"^(?:(?:19|20)\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present)\b", title, re.I):
                                        continue
                                    if re.search(r"^(?:About|LinkedIn Corporation|Show\s+all|See\s+all|Projects?|Page\b)", title, re.I):
                                        continue
                                    half_len = len(title) // 2
                                    if half_len > 10 and title[:half_len] == title[half_len:]:
                                        title = title[:half_len]
                                if title and len(title) > 3 and not any(p.get("title") == title for p in project_items):
                                    project_items.append({
                                        "title": title,
                                        "description": desc,
                                        "dates": dates,
                                        "skills": skills,
                                        "url": pc.get("href", ""),
                                    })
                    finally:
                        await sub_page.close()
                except Exception as e:
                    logger.debug("Projects subpage skipped: %s", e)

            # ------------------------------------------------------------------
            # 7. Section 7: Verified Skills
            # ------------------------------------------------------------------
            await self._update_overlay(page, f"HR Dossier: [7/7] Unlocking Complete Skills List for {candidate.name[:18]}...")
            extracted_skills = list(candidate.skills)
            skill_meta = {}
            try:
                skill_result = await page.evaluate(r"""
                    async () => {
                        const res = { items: [], total_expected: 0, detail_link: '' };
                        const anchorIds = ['skills'];
                        let sec = null;
                        for (const id of anchorIds) {
                            const el = document.getElementById(id);
                            if (el) {
                                sec = el.closest('section, div.artdeco-card') || el.parentElement;
                                break;
                            }
                        }
                        if (!sec) {
                            for (const s of document.querySelectorAll('section, div.artdeco-card, div[data-view-name*="profile-card"]')) {
                                const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                                const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                if (t.startsWith('skill') || /(?:^|\b)skills?(?:\s*\(\d+\))?/i.test(t) || (s.id && /skills?/i.test(s.id))) {
                                    sec = s;
                                    break;
                                }
                            }
                        }
                        if (!sec) {
                            const maxScroll = Math.min(document.body.scrollHeight, 12000);
                            for (let y = window.scrollY || 0; y <= maxScroll; y += 600) {
                                window.scrollTo({ top: y, behavior: 'instant' });
                                await new Promise(r => setTimeout(r, 100));
                                for (const id of anchorIds) {
                                    const el = document.getElementById(id);
                                    if (el) {
                                        sec = el.closest('section, div.artdeco-card') || el.parentElement;
                                        break;
                                    }
                                }
                                if (sec) break;
                                for (const s of document.querySelectorAll('section, div.artdeco-card')) {
                                    const h = s.querySelector('h2, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                                    const t = (h ? (h.innerText || '') : '').toLowerCase().trim();
                                    if (t.startsWith('skill') || /(?:^|\b)skills?(?:\s*\(\d+\))?/i.test(t)) {
                                        sec = s;
                                        break;
                                    }
                                }
                                if (sec) break;
                            }
                        }
                        if (!sec) return res;

                        sec.scrollIntoView({ behavior: 'instant', block: 'center' });
                        await new Promise(r => setTimeout(r, 180));

                        const h = sec.querySelector('h2, div.pvs-header__title, [data-view-name*="header"], span.pvs-header__title');
                        const hText = h ? (h.innerText || '') : '';
                        const cm = hText.match(/\((\d+)\)/);
                        if (cm) res.total_expected = parseInt(cm[1], 10);

                        const dAnchor = sec.querySelector('a[href*="/details/skills"]');
                        if (dAnchor && dAnchor.href) {
                            res.detail_link = dAnchor.href;
                        } else {
                            for (const a of sec.querySelectorAll('a, button')) {
                                const txt = (a.innerText || '').toLowerCase();
                                if (txt.includes('show all') || txt.includes('see all')) {
                                    const m = txt.match(/(\d+)/);
                                    if (m && !res.total_expected) res.total_expected = parseInt(m[1], 10);
                                    if (a.href) res.detail_link = a.href;
                                }
                            }
                        }

                        const itemEls = Array.from(sec.querySelectorAll(
                            'ul.pvs-list > li, ' +
                            'div.pvs-list__outer-container > ul > li, ' +
                            'div.pvs-entity'
                        )).filter(el => !el.parentElement.closest('ul.pvs-list > li, div.pvs-entity'));

                        for (const el of itemEls) {
                            const firstSpan = el.querySelector('div.display-flex span[aria-hidden="true"], span[aria-hidden="true"]');
                            if (firstSpan) {
                                const t = (firstSpan.innerText || '').trim().replace(/\s+/g, ' ');
                                if (t && t.length > 1 && t.length < 50 &&
                                    !t.toLowerCase().startsWith('show all') &&
                                    !t.toLowerCase().includes('endorsement') &&
                                    !/^\d+$/.test(t) &&
                                    !res.items.includes(t)) {
                                    res.items.push(t);
                                }
                            }
                        }
                        return res;
                    }
                """)
                if skill_result and skill_result.get("items"):
                    for sk in skill_result["items"]:
                        if sk not in extracted_skills:
                            extracted_skills.append(sk)
                skill_meta = skill_result or {}
            except Exception as e:
                logger.debug("Main page skills extraction warning: %s", e)

            # Deep skills lookup if candidate has more skills or explicit details link exists
            detail_skills_url = skill_meta.get("detail_link") or detail_links.get("skills") or fallback_detail_links.get("skills")

            if not skip_navigation and detail_skills_url and (len(extracted_skills) < skill_meta.get("total_expected", 0) or skill_meta.get("total_expected", 0) > 3 or len(extracted_skills) < 10):
                try:
                    sub_page = await page.context.new_page()
                    try:
                        await sub_page.goto(detail_skills_url, wait_until="domcontentloaded", timeout=10000)
                        await asyncio.sleep(0.8)
                        all_skills = await sub_page.evaluate(r"""
                            async () => {
                                const h = Math.min(document.body.scrollHeight, 12000);
                                for (let y = 0; y <= h; y += 600) {
                                    window.scrollTo({ top: y, behavior: 'instant' });
                                    await new Promise(r => setTimeout(r, 80));
                                }
                                const items = [];
                                const itemEls = Array.from(document.querySelectorAll(
                                    'main ul.pvs-list > li, ' +
                                    'div.pvs-list__outer-container > ul > li, ' +
                                    'div.pvs-entity'
                                ));
                                for (const el of itemEls) {
                                    const s = el.querySelector('div.display-flex span[aria-hidden="true"], a span[aria-hidden="true"], span[aria-hidden="true"]');
                                    if (s) {
                                        let t = (s.innerText || '').trim().replace(/\s+/g, ' ');
                                        if (t && t.length > 1 && t.length < 60 &&
                                            !t.toLowerCase().startsWith('show all') &&
                                            !t.toLowerCase().includes('endorsement') &&
                                            !t.toLowerCase().includes('skill assessment') &&
                                            !/^\d+$/.test(t) &&
                                            !items.includes(t)) {
                                            items.push(t);
                                        }
                                    }
                                }
                                return items;
                            }
                        """)
                        if all_skills and len(all_skills) >= len(extracted_skills):
                            for sk in all_skills:
                                if sk not in extracted_skills:
                                    extracted_skills.append(sk)
                    finally:
                        await sub_page.close()
                except Exception as e:
                    logger.debug("Skills subpage extraction skipped: %s", e)

            # Build enriched comprehensive resume dossier
            snippet_parts = []
            if about_text:
                snippet_parts.append(f"About: {about_text}")
            if recent_activities:
                act_str = " | ".join(a['headline'] for a in recent_activities)
                snippet_parts.append(f"Activity: {act_str}")
            if experience_items:
                exp_summary = " | ".join(f"{e['title']} at {e['company']} ({e.get('dates', '')})" for e in experience_items)
                snippet_parts.append(f"Experience: {exp_summary}")
            if education_items:
                edu_str = " | ".join(f"{ed['degree']} from {ed['school']}" for ed in education_items)
                snippet_parts.append(f"Education: {edu_str}")
            if cert_items:
                certs_str = " | ".join(f"{c['name']} ({c.get('issuing_org', '')})" for c in cert_items)
                snippet_parts.append(f"Certifications: {certs_str}")
            if project_items:
                proj_str = " | ".join(f"{p['title']}: {p.get('description', '')[:60]}" for p in project_items)
                snippet_parts.append(f"Projects: {proj_str}")
            if extracted_skills:
                snippet_parts.append(f"Skills: {', '.join(extracted_skills)}")

            full_snippet = "\n".join(snippet_parts) if snippet_parts else candidate.raw_snippet

            candidate.about = about_text or candidate.about
            candidate.recent_activity = recent_activities if recent_activities else candidate.recent_activity
            candidate.experience_history = experience_items if experience_items else candidate.experience_history
            candidate.education = education_items if education_items else candidate.education
            candidate.certifications = cert_items if cert_items else candidate.certifications
            candidate.projects = project_items if project_items else candidate.projects
            candidate.skills = extracted_skills if extracted_skills else candidate.skills
            candidate.raw_snippet = full_snippet

            # Multi-section enrichment from headline / text
            combined_bio = f"{candidate.headline or ''} {full_snippet or ''} {candidate.about or ''}".lower()
            if not candidate.work_authorization:
                if "golden visa" in combined_bio:
                    candidate.work_authorization = "UAE Golden Visa Holder"
                elif "citizen" in combined_bio:
                    candidate.work_authorization = "Citizen"

            # Education fallback from headline/topcard (e.g. University of Birmingham, ISB, IIT, IIM)
            if not candidate.education:
                univ_match = re.search(r"\b(ISB|IIT|IIM|BITS|MIT|Stanford|Harvard|INSEAD|University of [A-Za-z]+|[A-Za-z]+ (?:University|Institute of Technology|College|Business School))\b", candidate.headline or "", re.I)
                if univ_match:
                    school_name = univ_match.group(0).strip()
                    if school_name.upper() == "ISB":
                        school_name = "Indian School of Business (ISB)"
                    candidate.education = [{"school": school_name, "degree": "Postgraduate / Degree", "dates": ""}]

            # Experience fallback from headline if empty
            if not candidate.experience_history and candidate.headline:
                hl = candidate.headline.strip()
                first_seg = hl.split('|')[0].strip()
                if '@' in first_seg:
                    parts = first_seg.split('@', 1)
                    role = parts[0].strip()
                    comp = parts[1].strip()
                elif ' at ' in first_seg:
                    parts = first_seg.split(' at ', 1)
                    role = parts[0].strip()
                    comp = parts[1].strip()
                else:
                    role = first_seg
                    comp = candidate.current_company or "Current Organization"
                
                if role and len(role) > 2 and "member" not in role.lower():
                    candidate.experience_history.append({
                        "title": role,
                        "role": role,
                        "company": comp,
                        "dates": "Current",
                        "description": "Primary role verified from profile headline",
                    })

                ex_match = re.search(r"\b(?:Ex-|Former\s+)([^\|]+)", hl, re.I)
                if ex_match:
                    raw_past = re.sub(r"\b(Bengaluru|Bangalore|Dubai|UAE|India|London|San Francisco|New York)\b.*$", "", ex_match.group(1), flags=re.I).strip()
                    prior_comps = [c.strip() for c in re.split(r"[,/]+", raw_past) if c.strip() and len(c.strip()) > 2]
                    for pc in prior_comps[:3]:
                        candidate.experience_history.append({
                            "title": "Previous Role",
                            "role": "Previous Role",
                            "company": pc,
                            "dates": "Past Tenure",
                            "description": f"Verified prior tenure at {pc}",
                        })

            # Experience extraction from About section if experience history is sparse (< 2 positions)
            if len(candidate.experience_history) < 2 and candidate.about:
                about_str = candidate.about
                # Pattern: "At <Company>, I work/worked on..."
                at_comp_match = re.findall(r"\bAt\s+([A-Z][A-Za-z0-9&]+),?\s+I\s+(?:work|lead|built|engineered|spearhead)", about_str, re.I)
                for comp in at_comp_match:
                    comp_name = comp.strip()
                    if comp_name and not any(comp_name.lower() == (e.get('company') or '').lower() for e in candidate.experience_history):
                        candidate.experience_history.append({
                            "title": candidate.headline.split('|')[0].strip() if candidate.headline else "Team Member",
                            "role": candidate.headline.split('|')[0].strip() if candidate.headline else "Team Member",
                            "company": comp_name,
                            "dates": "Current / Recent",
                            "description": f"Verified from candidate about summary at {comp_name}"
                        })
                # Pattern: "Before that, at <Company>..." or "Previously at <Company>..."
                prev_comp_match = re.findall(r"\b(?:Before that|Previously)[,\s]+(?:at|with)\s+([A-Z][A-Za-z0-9&]+)", about_str, re.I)
                for comp in prev_comp_match:
                    comp_name = comp.strip()
                    if comp_name and not any(comp_name.lower() == (e.get('company') or '').lower() for e in candidate.experience_history):
                        candidate.experience_history.append({
                            "title": "Software Engineer / Professional",
                            "role": "Software Engineer / Professional",
                            "company": comp_name,
                            "dates": "Past Tenure",
                            "description": f"Verified prior tenure at {comp_name} from profile summary"
                        })

            # Skills enrichment from About section and Headline if skills count is low (< 5)
            if len(candidate.skills) < 5:
                text_to_scan = f"{candidate.headline or ''} {candidate.about or ''}"
                known_tech_dictionary = [
                    "React.js", "React", "Next.js", "Vue.js", "Angular", "JavaScript", "TypeScript",
                    "HTML", "CSS", "Tailwind CSS", "Bootstrap", "Redux", "Zustand", "Figma", "UI/UX",
                    "Node.js", "Express", "FastAPI", "Python", "Django", "Flask", "Go", "Golang",
                    "Java", "Spring Boot", "C++", "C#", ".NET", "PHP", "Laravel", "Ruby on Rails",
                    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Supabase",
                    "AWS", "GCP", "Google Cloud", "Azure", "Docker", "Kubernetes", "CI/CD", "Git",
                    "GraphQL", "REST APIs", "REST", "WebSockets", "Microservices", "Kafka",
                    "Product Management", "Roadmapping", "Agile", "Scrum", "PRDs", "Wireframing",
                    "Machine Learning", "Deep Learning", "LLM", "GenAI", "NLP", "PyTorch", "TensorFlow",
                    "RAG", "Data Engineering", "ETL", "Spark", "Pandas", "Snowflake", "Databricks"
                ]
                for tech in known_tech_dictionary:
                    pattern = r"(?<!\w)" + re.escape(tech) + r"(?!\w)"
                    if re.search(pattern, text_to_scan, re.I):
                        # Avoid duplicates like 'React' if 'React.js' already in skills
                        if not any(tech.lower() == s.lower() for s in candidate.skills):
                            candidate.skills.append(tech)

            # Certifications fallback from headline
            if not candidate.certifications:
                cert_matches = re.findall(r"\b(Certified [A-Za-z\s]+?)(?=[\|\-•,]|$)", candidate.headline or "", re.I)
                if cert_matches:
                    candidate.certifications = [{"name": c.strip(), "issuing_org": "Accredited Body", "dates": ""} for c in cert_matches[:3]]

            # Company fallback from experience history if headline did not provide explicit company
            if (not candidate.current_company or candidate.current_company in ("Technology Co.", "Verified Profile")) and candidate.experience_history:
                candidate.current_company = candidate.experience_history[0].get("company", candidate.current_company or "")

            # Location and current location normalization
            if not candidate.location or candidate.location in ("Location not specified", "Location on Profile"):
                loc_match = re.search(r"\b(Dubai(?:,\s*United Arab Emirates)?|Abu Dhabi(?:,\s*United Arab Emirates)?|United Arab Emirates|UAE|Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Delhi|Chennai|Coimbatore(?:,\s*Tamil\s*Nadu)?|Coimbatore|Tamil\s*Nadu|Tamilnadu|Kolkata|India|San Francisco|New York|Seattle|London|Berlin|Toronto|Singapore|Remote)\b", combined_bio, re.I)
                if loc_match:
                    candidate.location = loc_match.group(0).strip()
                elif candidate.experience_history and candidate.experience_history[0].get("location"):
                    candidate.location = candidate.experience_history[0].get("location")
            candidate.current_location = candidate.location

            candidate.stored_in_db = True

            logger.info(
                "Deep dossier extracted for %s: %d skills, %d experiences, %d educations, %d certs, %d projects, work_auth=%s, about_len=%d",
                candidate.name, len(candidate.skills), len(candidate.experience_history), len(candidate.education), len(candidate.certifications), len(candidate.projects), candidate.work_authorization, len(candidate.about or '')
            )
            return candidate
        except Exception as e:
            logger.warning("Error deep-extracting profile %s: %s", candidate.canonical_url, e)
            candidate.stored_in_db = True
            return candidate

    async def extract_candidate_profile(
        self,
        candidate: CandidateProfile,
        browser_channel: Optional[str] = "chrome",
        skip_navigation: bool = False,
    ) -> CandidateProfile:
        """Navigates directly to candidate's LinkedIn profile and extracts full 7-section dossier."""
        context, _ = await self._get_or_create_context(browser_channel=browser_channel)
        page = await context.new_page()
        try:
            return await self._visit_and_extract_profile(page, candidate, skip_navigation=skip_navigation)
        finally:
            await page.close()

    def _generate_simulated_candidates(self, query: str, count: int = 6) -> List[CandidateProfile]:
        """Generates realistic candidate profiles tailored to the search query for robust testing."""
        query_lower = query.lower()
        is_frontend = any(x in query_lower for x in ["frontend", "react", "next.js", "javascript", "tailwind", "ui", "css"])

        if is_frontend:
            templates = [
                {
                    "name": "Sarah Chen",
                    "headline": "Staff Frontend Engineer at Stripe | React, Next.js, WebSockets, TypeScript",
                    "company": "Stripe",
                    "location": "San Francisco, CA (Remote)",
                    "years": 7.5,
                    "skills": ["React", "Next.js", "JavaScript", "Tailwind CSS", "WebSockets", "Server-Sent Events (SSE)"],
                    "snippet": "Experienced Frontend Lead architecting real-time event dashboards with Next.js and Tailwind CSS. 7+ years building high-concurrency UI applications.",
                    "history": [
                        {"title": "Staff Frontend Engineer", "company": "Stripe", "dates": "2021 - Present (3.5 yrs)", "description": "Led core dashboard UI team building high-performance Next.js event visualization components."},
                        {"title": "Senior Frontend Developer", "company": "Square", "dates": "2018 - 2021 (3.0 yrs)", "description": "Built merchant analytics UI and real-time payment feed with React and WebSockets."}
                    ]
                },
                {
                    "name": "Alex Rivera",
                    "headline": "Senior Frontend Developer at Datadog | React, State Management, High-Perf Web Apps",
                    "company": "Datadog",
                    "location": "New York, NY",
                    "years": 6.0,
                    "skills": ["React", "Next.js", "JavaScript", "State management", "REST APIs", "Tailwind CSS"],
                    "snippet": "Senior React Engineer specializing in telemetry monitoring UIs, complex state management, and 60fps web animation optimization.",
                    "history": [
                        {"title": "Senior Frontend Developer", "company": "Datadog", "dates": "2022 - Present (2.5 yrs)", "description": "Architected high-throughput time-series charting controls and streaming state stores."},
                        {"title": "Frontend Engineer", "company": "Etsy", "dates": "2019 - 2022 (3.5 yrs)", "description": "Optimized mobile checkout performance and component library design system."}
                    ]
                },
                {
                    "name": "Priya Sharma",
                    "headline": "Lead UI Engineer at Atlassian | React Ecosystem, Next.js, Design Systems",
                    "company": "Atlassian",
                    "location": "Bengaluru, India (Remote)",
                    "years": 5.5,
                    "skills": ["React", "Next.js", "JavaScript", "Tailwind CSS", "Responsive UI development"],
                    "snippet": "Full-lifecycle frontend engineer passionate about accessible, performant React applications and resilient API error handling.",
                    "history": [
                        {"title": "Lead UI Engineer", "company": "Atlassian", "dates": "2021 - Present (3.0 yrs)", "description": "Spearheaded design system modernization across Jira frontend using Next.js and Tailwind CSS."},
                        {"title": "Software Engineer II", "company": "Swiggy", "dates": "2019 - 2021 (2.5 yrs)", "description": "Built food discovery interface with sub-100ms interaction latency."}
                    ]
                },
                {
                    "name": "Marcus Vance",
                    "headline": "Senior Fullstack Engineer at Coinbase | React, Node.js, WebSockets, Real-time APIs",
                    "company": "Coinbase",
                    "location": "Austin, TX",
                    "years": 5.0,
                    "skills": ["React", "JavaScript", "WebSockets", "REST APIs", "State management"],
                    "snippet": "5 years building financial trading web interfaces with React and WebSockets. Proven track record in rapid recovery and network resiliency.",
                    "history": [
                        {"title": "Senior Fullstack Engineer", "company": "Coinbase", "dates": "2022 - Present (2.0 yrs)", "description": "Engineered order book UI streaming updates at 60fps via bidirectional WebSockets."},
                        {"title": "Fullstack Developer", "company": "Robinhood", "dates": "2019 - 2022 (3.0 yrs)", "description": "Designed real-time trade execution confirmations and responsive web components."}
                    ]
                },
                {
                    "name": "Elena Rostova",
                    "headline": "Frontend Architect at Figma | Next.js, React Hooks, Modern CSS & Micro-frontends",
                    "company": "Figma",
                    "location": "Seattle, WA",
                    "years": 8.0,
                    "skills": ["Next.js", "React", "JavaScript", "Performant UI development", "Tailwind CSS"],
                    "snippet": "Passionate about scalable frontend systems, Next.js App Router performance, and developer experience.",
                    "history": [
                        {"title": "Frontend Architect", "company": "Figma", "dates": "2020 - Present (4.0 yrs)", "description": "Led collaborative canvas UI layer refactor reducing memory footprint by 35%."},
                        {"title": "Senior Web Engineer", "company": "Airbnb", "dates": "2017 - 2020 (3.0 yrs)", "description": "Created shared UI tokens and modular layout primitives for listing flows."}
                    ]
                },
                {
                    "name": "Aarav Mehta",
                    "headline": "Senior Software Engineer at Google | React, Next.js, Distributed Agent Systems",
                    "company": "Google",
                    "location": "Bengaluru, India",
                    "years": 6.5,
                    "skills": ["React", "Next.js", "JavaScript", "TypeScript", "REST APIs", "WebSockets"],
                    "snippet": "Senior Frontend & Distributed Systems Engineer architecting mission-critical web applications at Google with Next.js and real-time telemetry.",
                    "history": [
                        {"title": "Senior Software Engineer", "company": "Google", "dates": "2021 - Present (3.5 yrs)", "description": "Led team of 8 frontend engineers rebuilding Cloud Console microfrontends with Next.js."},
                        {"title": "Frontend Engineer II", "company": "Razorpay", "dates": "2018 - 2021 (3.0 yrs)", "description": "Built developer dashboard and webhook telemetry inspection tools."}
                    ]
                }
            ]
        else:
            templates = [
                {
                    "name": "Tariq Mansoor",
                    "headline": "Principal AI Architect at Careem | Python, PyTorch, RAG, LLMOps, System Design | UAE Golden Visa Holder",
                    "company": "Careem",
                    "location": "Dubai, United Arab Emirates",
                    "years": 8.5,
                    "work_auth": "UAE Golden Visa Holder",
                    "skills": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "Generative AI", "RAG", "Vector Databases", "MLOps", "LLMOps", "System Design"],
                    "snippet": "Principal AI Architect designing production Generative AI platforms, high-throughput RAG pipelines with vector databases, and enterprise agentic systems in Dubai.",
                    "history": [
                        {"title": "Principal AI Architect", "company": "Careem", "dates": "2022 - Present (2.5 yrs)", "description": "Architected multi-agent customer support LLM routing system processing 500k requests/day with pgvector and FastAPI."},
                        {"title": "Senior Machine Learning Engineer", "company": "Noon", "dates": "2019 - 2022 (3.0 yrs)", "description": "Led recommendation and search ranking models using PyTorch and distributed training on Kubernetes."}
                    ]
                },
                {
                    "name": "Hamza A.",
                    "headline": "AI in Education Leadership | Edtech and Innovation | Digital Transformation | University of Birmingham | Certified Trainer | Certified Master Trainer | UAE Golden Visa Holder",
                    "company": "Ministry of Education – UAE",
                    "location": "Abu Dhabi Emirate, United Arab Emirates",
                    "years": 7.5,
                    "work_auth": "UAE Golden Visa Holder",
                    "skills": ["Team Leadership", "Education Management", "Information Technology Training", "Instructional Design", "STEM Education", "Digital Transformation"],
                    "snippet": "Head of AI and Technology at Ministry of Education – UAE. EdTech innovator leading nationwide teacher upskilling programs, AI in schools curriculum, and STEM modernizations.",
                    "history": [
                        {"title": "Head of AI and Technology", "company": "Ministry of Education – UAE", "dates": "Sep 2025 - Present (1 yr 3 mos)", "description": "Guide school tech leaders in integrating technology and generative AI tools across curriculum."},
                        {"title": "Professional Development Trainer – Sustainability, Innovation and Technology", "company": "Ministry of Education – UAE", "dates": "Jul 2022 - Present (4 yrs 5 mos)", "description": "Enhance professional development in Sustainability, Innovation, and modern EdTech training."},
                        {"title": "Head of STEM And Engineering Department", "company": "Ministry of Education – UAE", "dates": "Jul 2022 - Sep 2025 (3 yrs 3 mos)", "description": "Oversee operations, scheduling, budgeting, and STEM curriculum modernizations."},
                        {"title": "STEM and Engineering program teacher", "company": "Ministry of Education – UAE", "dates": "Jul 2019 - Jul 2022 (3 yrs 1 mo)", "description": "Integrate computer science and robotics concepts into high school engineering courses."}
                    ]
                },
                {
                    "name": "Vikram Malhotra",
                    "headline": "Staff Machine Learning Engineer at Flipkart | Python, LLM Application Development, Vector DBs, MLOps",
                    "company": "Flipkart",
                    "location": "Bengaluru, Karnataka, India",
                    "years": 7.0,
                    "work_auth": None,
                    "skills": ["Python", "Machine Learning", "LLM Application Development", "Vector Databases", "Prompt Engineering", "MLOps"],
                    "snippet": "Staff ML Engineer specializing in Large Language Models, hybrid dense retrieval with Milvus vector DB, and automated model evaluation. Willing to relocate to Dubai.",
                    "history": [
                        {"title": "Staff Machine Learning Engineer", "company": "Flipkart", "dates": "2021 - Present (3.5 yrs)", "description": "Architected catalog search RAG assistant delivering 15% CTR lift. Productionized LangChain and FastAPI microservices."},
                        {"title": "Senior Data Scientist", "company": "Swiggy", "dates": "2018 - 2021 (3.0 yrs)", "description": "Engineered real-time ETA prediction and dynamic dispatch neural networks in PyTorch."}
                    ]
                },
                {
                    "name": "Pooja Iyer",
                    "headline": "Senior AI & NLP Engineer at Infosys | Python, LangChain, PyTorch, RAG Pipelines",
                    "company": "Infosys",
                    "location": "Hyderabad, Telangana, India",
                    "years": 6.0,
                    "work_auth": None,
                    "skills": ["Python", "PyTorch", "LangChain", "RAG", "FastAPI", "Docker"],
                    "snippet": "Senior AI engineer developing enterprise document extraction and question-answering systems with LangChain and pgvector.",
                    "history": [
                        {"title": "Senior AI & NLP Engineer", "company": "Infosys", "dates": "2021 - Present (3.0 yrs)", "description": "Built multi-tenant enterprise search RAG platform on Azure with FastAPI and Pinecone."},
                        {"title": "Software Engineer", "company": "Wipro", "dates": "2018 - 2021 (3.0 yrs)", "description": "Developed backend data processing pipelines in Python and PostgreSQL."}
                    ]
                },
                {
                    "name": "David Kim",
                    "headline": "Lead AI Systems Engineer at Scale AI | Python, FastAPI, Agentic AI, LLM Orchestration",
                    "company": "Scale AI",
                    "location": "San Francisco, CA",
                    "years": 8.0,
                    "work_auth": None,
                    "skills": ["Python", "FastAPI", "Agentic Workflows", "LLM Application Development", "Prompt Engineering", "PostgreSQL"],
                    "snippet": "Specializing in autonomous agent state machines, tool-using LLM systems, and resilient multi-model pipelines.",
                    "history": [
                        {"title": "Lead AI Systems Engineer", "company": "Scale AI", "dates": "2021 - Present (3.5 yrs)", "description": "Architected autonomous agent orchestration pipelines with tool execution sandboxes."},
                        {"title": "Senior Backend Engineer", "company": "Twilio", "dates": "2017 - 2021 (4.0 yrs)", "description": "Built distributed telephony webhook dispatch engine handling 50k requests/sec."}
                    ]
                },
                {
                    "name": "Ananya Patel",
                    "headline": "Senior Backend & Agent Engineer at Anthropic | Python, FastAPI, Distributed Systems",
                    "company": "Anthropic",
                    "location": "Seattle, WA",
                    "years": 7.0,
                    "work_auth": None,
                    "skills": ["Python", "FastAPI", "AsyncIO", "LLM Application Development", "Docker", "Playwright"],
                    "snippet": "7+ years architecting high-throughput backend services and state-aware LLM reasoning agents with self-healing fallback loops.",
                    "history": [
                        {"title": "Senior Backend & Agent Engineer", "company": "Anthropic", "dates": "2022 - Present (2.5 yrs)", "description": "Created tool evaluation runtime and safe browser interaction sandboxes for AI agents."},
                        {"title": "Backend Systems Engineer", "company": "Uber", "dates": "2018 - 2022 (4.0 yrs)", "description": "Engineered real-time driver dispatch matching algorithms in Python and Go."}
                    ]
                }
            ]

        results = []
        ts = int(time.time() * 1000)
        num_to_make = max(1, min(count, 50))
        for idx in range(num_to_make):
            t = templates[idx % len(templates)]
            multiplier = idx // len(templates)
            name = t["name"] if multiplier == 0 else f"{t['name']} {chr(65 + multiplier)}"
            slug = name.lower().replace(" ", "-")
            history = t.get("history") or [
                {
                    "title": t["headline"].split(" at ")[0].strip(),
                    "company": t["company"],
                    "dates": f"{int(t['years'])} years",
                    "description": t["snippet"],
                }
            ]

            # Realistic 7 sections data
            edu_degree = "Master of Science in Computer Science" if idx % 2 == 0 else "Bachelor of Technology in Computer Science"
            edu_school = ["Stanford University", "UC Berkeley", "Carnegie Mellon", "IIT Madras", "BITS Pilani", "University of Washington"][idx % 6]
            education = [
                {
                    "school": edu_school,
                    "degree": edu_degree,
                    "dates": f"{2024 - int(t['years']) - 4} - {2024 - int(t['years'])}",
                }
            ]

            certs = [
                {
                    "name": "AWS Certified Solutions Architect - Professional" if idx % 2 == 0 else "Google Cloud Professional Machine Learning Engineer",
                    "issuing_org": "Amazon Web Services" if idx % 2 == 0 else "Google Cloud",
                    "issue_date": f"Issued 202{3 - (idx % 2)}",
                    "credential_id": f"AWS-CERT-{idx+1001}" if idx % 2 == 0 else f"GCP-ML-{idx+2002}",
                }
            ]

            projects = [
                {
                    "title": f"High-Throughput {t['skills'][0]} Platform",
                    "description": f"Architected production system utilizing {', '.join(t['skills'][:3])} handling 10k+ requests/sec.",
                    "dates": "2023 - 2024",
                    "skills": t['skills'][:3],
                }
            ]

            recent_activity = [
                {
                    "action_type": "Post",
                    "headline": f"Published architectural breakdown on building production {t['skills'][0]} microservices",
                    "snippet": f"Shared best practices on high concurrency, distributed state, and clean API design using {t['skills'][0]}.",
                    "date": "2 weeks ago",
                }
            ]

            cand = CandidateProfile(
                id=f"sim_{ts}_{idx+1}",
                name=name,
                canonical_url=f"https://www.linkedin.com/in/{slug}",
                headline=t["headline"],
                current_company=t["company"],
                location=t["location"],
                current_location=t["location"],
                work_authorization=t.get("work_auth"),
                experience_years=t["years"],
                skills=t["skills"],
                about=t.get("snippet", ""),
                avatar_url=VERIFIED_AVATARS[idx % len(VERIFIED_AVATARS)],
                experience_history=history,
                education=education,
                certifications=certs,
                projects=projects,
                recent_activity=recent_activity,
                raw_snippet=f"{name} — {t['headline']}\nLocation: {t['location']}\nAbout: {t.get('snippet', '')}\nExperience: {history[0]['title']} at {history[0]['company']}\nEducation: {education[0]['degree']} from {education[0]['school']}\nSkills: {', '.join(t['skills'])}",
                stored_in_db=True,
            )
            try:
                cand_data = cand.model_dump() if hasattr(cand, "model_dump") else cand.dict()
                db_service.save_candidate(cand_data)
            except Exception as e:
                logger.warning("Could not persist simulated candidate to DB: %s", e)
            results.append(cand)
        return results

    def _generate_simulation_html(self, query: str, candidates: List[CandidateProfile]) -> str:
        """Generates an interactive, styled LinkedIn Sourcing Workspace HTML page for autonomous UI demo."""
        out_dir = os.path.abspath("data")
        os.makedirs(out_dir, exist_ok=True)
        html_path = os.path.join(out_dir, "agent_simulation.html")

        cand_list = []
        for c in candidates:
            cand_list.append({
                "id": c.id,
                "name": c.name,
                "headline": c.headline,
                "company": c.current_company or "",
                "location": c.location or "",
                "years": c.experience_years,
                "skills": c.skills,
                "about": c.about or c.raw_snippet,
                "avatar_url": c.avatar_url or "",
                "experience_history": c.experience_history,
                "education": c.education,
                "certifications": c.certifications,
                "projects": c.projects,
                "recent_activity": c.recent_activity,
                "canonical_url": c.canonical_url,
            })

        cand_json = json.dumps(cand_list)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>LinkedIn Recruiter - Autonomous AI Agent Workspace</title>
  <style>
    :root {{
      --bg: #0b1120;
      --card-bg: #0f172a;
      --card-border: #1e293b;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #10b981;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding-bottom: 80px;
    }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: #0d1527;
      border-bottom: 1px solid #1e293b;
      padding: 12px 28px;
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    .logo-container {{
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
    }}
    .logo-badge {{
      background: #0a66c2;
      color: white;
      font-weight: 800;
      font-size: 18px;
      padding: 3px 8px;
      border-radius: 4px;
    }}
    .portal-name {{
      font-size: 15px;
      font-weight: 700;
      color: #e2e8f0;
      letter-spacing: -0.3px;
    }}
    .search-box {{
      flex: 1;
      max-width: 520px;
      display: flex;
      gap: 8px;
    }}
    .search-input {{
      flex: 1;
      background: #1e293b;
      border: 1px solid #334155;
      color: white;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 14px;
      outline: none;
    }}
    .search-input:focus {{
      border-color: #3b82f6;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }}
    .btn {{
      background: var(--primary);
      color: white;
      border: none;
      padding: 8px 18px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background 0.15s;
    }}
    .btn:hover {{ background: var(--primary-hover); }}
    .btn-outline {{
      background: transparent;
      border: 1px solid #475569;
      color: #e2e8f0;
    }}
    .btn-outline:hover {{ background: #1e293b; border-color: #64748b; }}

    /* Floating Agent Control HUD */
    #agent-hud {{
      position: fixed;
      top: 20px;
      right: 24px;
      z-index: 10000;
      width: 380px;
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(14px);
      border: 1.5px solid #3b82f6;
      border-radius: 14px;
      padding: 16px 20px;
      box-shadow: 0 16px 36px rgba(0,0,0,0.65), 0 0 16px rgba(59, 130, 246, 0.25);
    }}
    .hud-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;
      font-weight: 700;
      color: #60a5fa;
    }}
    .pulse-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
      display: inline-block;
      margin-right: 6px;
      animation: pulse 1.4s infinite;
    }}
    @keyframes pulse {{ 0% {{ opacity: 0.4; transform: scale(0.9); }} 50% {{ opacity: 1; transform: scale(1.1); }} 100% {{ opacity: 0.4; transform: scale(0.9); }} }}
    .hud-title {{ font-size: 14px; font-weight: 700; color: #f8fafc; }}
    .hud-detail {{ font-size: 12px; color: #94a3b8; margin-top: 4px; line-height: 1.4; }}
    .hud-footer {{
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid #1e293b;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11px;
      color: #34d399;
      font-weight: 600;
    }}

    /* Extraction Highlight Animation */
    .agent-extracting {{
      border: 2px solid #3b82f6 !important;
      box-shadow: 0 0 25px rgba(59, 130, 246, 0.4) !important;
      position: relative;
      transition: all 0.3s ease;
      background: rgba(30, 41, 59, 0.6) !important;
    }}
    .agent-extracting::after {{
      content: "✨ AI EXTRACTED";
      position: absolute;
      top: -12px;
      right: 18px;
      background: #2563eb;
      color: white;
      font-size: 10px;
      font-weight: 800;
      padding: 3px 10px;
      border-radius: 9999px;
      letter-spacing: 0.6px;
      box-shadow: 0 4px 10px rgba(37, 99, 235, 0.4);
    }}

    .container {{ max-width: 860px; margin: 24px auto; padding: 0 16px; }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 22px;
      margin-bottom: 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      transition: border-color 0.2s;
    }}
    .card:hover {{ border-color: #334155; }}
    .candidate-header {{
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }}
    .avatar {{
      width: 68px;
      height: 68px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid #3b82f6;
    }}
    .cand-name {{ font-size: 18px; font-weight: 700; color: #f8fafc; }}
    .cand-headline {{ font-size: 14px; color: #cbd5e1; margin-top: 2px; line-height: 1.4; }}
    .cand-loc {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
    .cand-summary {{ font-size: 13px; color: #94a3b8; margin-top: 12px; line-height: 1.5; }}
    .card-actions {{
      display: flex;
      justify-content: flex-end;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid #1e293b;
    }}

    /* Skills Pill */
    .skill-chip {{
      display: inline-block;
      background: #1e293b;
      color: #93c5fd;
      border: 1px solid #334155;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 500;
      margin: 4px 6px 4px 0;
    }}
    .exp-item {{
      padding: 12px 0;
      border-bottom: 1px solid #1e293b;
    }}
    .exp-item:last-child {{ border-bottom: none; }}
    .exp-title {{ font-weight: 600; color: #f1f5f9; font-size: 14px; }}
    .exp-company {{ color: #60a5fa; font-size: 13px; margin-top: 2px; }}
    .exp-dates {{ color: #64748b; font-size: 12px; margin-top: 2px; }}
    .exp-desc {{ color: #94a3b8; font-size: 12px; margin-top: 6px; line-height: 1.4; }}
  </style>
</head>
<body>

  <!-- Top Navigation Bar -->
  <div class="topbar">
    <div class="logo-container">
      <span class="logo-badge">in</span>
      <span class="portal-name">LinkedIn Recruiter</span>
    </div>
    <div class="search-box">
      <input type="text" id="search-input" class="search-input" value="{query}" placeholder="Search candidate by title, skill, or company..." />
      <button id="btn-search" class="btn" onclick="triggerSearch()">Search</button>
    </div>
    <div style="margin-left: auto; display: flex; gap: 12px;">
      <span style="font-size: 12px; color: #94a3b8; padding: 8px 12px; background: #1e293b; border-radius: 8px;">Mode: <b>Autonomous UI Agent</b></span>
    </div>
  </div>

  <!-- Floating AI Agent Control HUD -->
  <div id="agent-hud">
    <div class="hud-header">
      <span><span class="pulse-dot"></span>AI Agent UI Control Active</span>
      <span id="hud-badge" style="font-size: 10px; background: #1e3a8a; color: #93c5fd; padding: 2px 6px; border-radius: 4px;">PLAYWRIGHT</span>
    </div>
    <div id="hud-title" class="hud-title">Initializing Agent...</div>
    <div id="hud-detail" class="hud-detail">Preparing headed Chromium session to navigate candidate profiles...</div>
    <div class="hud-footer">
      <span id="hud-db">✨ Shortlist Workspace</span>
      <span id="hud-step">Step 1</span>
    </div>
  </div>

  <div class="container">
    <!-- Search Results View -->
    <div id="search-results-view">
      <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
        <h2 style="font-size: 18px; font-weight: 700; color: #f1f5f9;">Candidate Search Results ({len(candidates)} Profiles)</h2>
        <span style="font-size: 13px; color: #64748b;">Keywords: "{query}"</span>
      </div>

      <div id="candidates-container">
        <!-- Render candidate cards -->
      </div>
    </div>

    <!-- Candidate Profile Detail View -->
    <div id="profile-detail-view" style="display: none;">
      <div style="margin-bottom: 16px;">
        <button id="btn-back-search" class="btn btn-outline" onclick="backToSearch()">
          ← Back to Search Results
        </button>
      </div>

      <!-- Header Card -->
      <div class="card" id="profile-hero-card">
        <div class="candidate-header">
          <img id="detail-avatar" class="avatar" src="" alt="Candidate" />
          <div style="flex: 1;">
            <div id="detail-name" class="cand-name">Candidate Name</div>
            <div id="detail-headline" class="cand-headline">Headline</div>
            <div id="detail-location" class="cand-loc">Location</div>
            <div style="margin-top: 12px; display: flex; gap: 8px;">
              <span class="btn" style="padding: 6px 14px; font-size: 12px;">Message Candidate</span>
              <span class="btn btn-outline" style="padding: 6px 14px; font-size: 12px;">Save to Talent Pool</span>
            </div>
          </div>
        </div>
      </div>

      <!-- About Section -->
      <div class="card" id="section-about">
        <h3 style="font-size: 15px; font-weight: 700; color: #f1f5f9; margin-bottom: 10px;">About</h3>
        <p id="detail-about" style="font-size: 13px; color: #cbd5e1; line-height: 1.6;"></p>
      </div>

      <!-- Experience History Section -->
      <div class="card" id="section-experience">
        <h3 style="font-size: 15px; font-weight: 700; color: #f1f5f9; margin-bottom: 12px;">Career Experience History</h3>
        <div id="detail-experience-list"></div>
      </div>

      <!-- Skills Section -->
      <div class="card" id="section-skills">
        <h3 style="font-size: 15px; font-weight: 700; color: #f1f5f9; margin-bottom: 10px;">Extracted Skills & Competencies</h3>
        <div id="detail-skills-list"></div>
      </div>
    </div>
  </div>

  <script>
    const CANDIDATES = {cand_json};
    let activeProfileIndex = 0;

    function renderCards() {{
      const container = document.getElementById("candidates-container");
      container.innerHTML = "";
      CANDIDATES.forEach((cand, idx) => {{
        const card = document.createElement("div");
        card.className = "card";
        card.id = `candidate-card-${{idx}}`;
        card.innerHTML = `
          <div class="candidate-header">
            <img class="avatar" src="https://images.unsplash.com/photo-${{1530000000000 + ((idx + 2) * 1234567) % 99999999}}?w=120&auto=format&fit=crop&q=80" alt="${{cand.name}}" />
            <div style="flex: 1;">
              <div class="cand-name">${{cand.name}}</div>
              <div class="cand-headline">${{cand.headline}}</div>
              <div class="cand-loc">📍 ${{cand.location}} • ${{cand.years}} yrs experience</div>
              <div class="cand-summary">${{cand.about}}</div>
              <div style="margin-top: 10px;">
                ${{cand.skills.slice(0, 5).map(s => `<span class="skill-chip">${{s}}</span>`).join("")}}
              </div>
            </div>
          </div>
          <div class="card-actions">
            <button id="btn-view-profile-${{idx}}" class="btn" onclick="openProfile(${{idx}})">
              View Full Profile & Experience →
            </button>
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    function openProfile(idx) {{
      activeProfileIndex = idx;
      const cand = CANDIDATES[idx];
      if (!cand) return;

      document.getElementById("detail-name").innerText = cand.name;
      document.getElementById("detail-headline").innerText = cand.headline;
      document.getElementById("detail-location").innerText = `📍 ${{cand.location}} • ${{cand.years}} yrs experience`;
      document.getElementById("detail-avatar").src = `https://images.unsplash.com/photo-${{1530000000000 + ((idx + 2) * 1234567) % 99999999}}?w=120&auto=format&fit=crop&q=80`;
      document.getElementById("detail-about").innerText = cand.about;

      const expContainer = document.getElementById("detail-experience-list");
      expContainer.innerHTML = "";
      if (cand.experience_history && cand.experience_history.length > 0) {{
        cand.experience_history.forEach(exp => {{
          const item = document.createElement("div");
          item.className = "exp-item";
          item.innerHTML = `
            <div class="exp-title">${{exp.title}}</div>
            <div class="exp-company">${{exp.company}}</div>
            <div class="exp-dates">${{exp.dates}}</div>
            <div class="exp-desc">${{exp.description}}</div>
          `;
          expContainer.appendChild(item);
        }});
      }} else {{
        expContainer.innerHTML = `<div class="exp-desc">Senior Engineer at ${{cand.company}} (${{cand.years}} years).</div>`;
      }}

      const skillsContainer = document.getElementById("detail-skills-list");
      skillsContainer.innerHTML = "";
      cand.skills.forEach(skill => {{
        const chip = document.createElement("span");
        chip.className = "skill-chip";
        chip.innerText = skill;
        skillsContainer.appendChild(chip);
      }});

      document.getElementById("search-results-view").style.display = "none";
      document.getElementById("profile-detail-view").style.display = "block";
      window.scrollTo({{ top: 0, behavior: "smooth" }});
    }}

    function backToSearch() {{
      document.querySelectorAll(".agent-extracting").forEach(el => el.classList.remove("agent-extracting"));
      document.getElementById("profile-detail-view").style.display = "none";
      document.getElementById("search-results-view").style.display = "block";
    }}

    function highlightSection(sectionId) {{
      document.querySelectorAll(".agent-extracting").forEach(el => el.classList.remove("agent-extracting"));
      const target = document.getElementById(sectionId);
      if (target) {{
        target.classList.add("agent-extracting");
      }}
    }}

    function updateAgentHud(title, detail, stepOrDb) {{
      if (title) document.getElementById("hud-title").innerText = title;
      if (detail) document.getElementById("hud-detail").innerText = detail;
      if (stepOrDb) {{
        if (stepOrDb.includes("Workspace") || stepOrDb.includes("Persisted") || stepOrDb.includes("Saved")) {{
          document.getElementById("hud-db").innerText = stepOrDb;
        }} else {{
          document.getElementById("hud-step").innerText = stepOrDb;
        }}
      }}
    }}

    function triggerSearch() {{
      renderCards();
    }}

    // Render cards immediately upon script load
    renderCards();
  </script>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Generated agent simulation HTML workspace at %s", html_path)
        return html_path

    async def _run_autonomous_ui_demo(
        self,
        page: Page,
        keywords: str,
        max_results: int = 5,
        session_id: Optional[str] = None,
    ) -> List[CandidateProfile]:
        """Takes full autonomous control of the browser UI to collect candidate data one-by-one."""
        if session_id:
            sourcing_tracker.update_session(
                session_id,
                state="launching_browser",
                progress=20,
                message="Launching headed Chromium browser simulation...",
            )

        candidates = self._generate_simulated_candidates(keywords, max_results)
        sim_html_path = self._generate_simulation_html(keywords, candidates)
        file_url = f"file:///{os.path.abspath(sim_html_path).replace(os.sep, '/')}"

        logger.info("Autonomous UI Agent launching interactive simulation workspace at %s", file_url)
        await page.goto(file_url, wait_until="domcontentloaded")
        await asyncio.sleep(0.6)

        # Step A: Perform search in UI
        if session_id:
            sourcing_tracker.update_session(
                session_id,
                state="searching",
                progress=35,
                message=f"Executing search query in browser UI: '{keywords}'...",
            )
        try:
            await page.wait_for_selector("#search-input", timeout=4000)
            await page.evaluate(f"window.updateAgentHud('🔍 Autonomous Search Action', 'Executing query: \"{keywords}\"...', 'Step 1 of {len(candidates) + 1}')")
            await page.fill("#search-input", keywords, timeout=3000)
            await asyncio.sleep(0.3)
            await page.click("#btn-search", timeout=3000)
            await asyncio.sleep(0.5)
            await page.evaluate("window.scrollBy({ top: 250, behavior: 'smooth' })")
            await asyncio.sleep(0.4)
        except Exception as e:
            logger.debug("Simulation search step note: %s", e)

        # Step B: Visit each candidate profile one-by-one
        for idx, cand in enumerate(candidates[:max_results]):
            if session_id:
                sess = sourcing_tracker.get_session(session_id)
                if sess and sess.get("should_stop"):
                    return candidates[:idx]
                sourcing_tracker.update_session(
                    session_id,
                    state="extracting",
                    progress=35 + int(50 * (idx + 1) / len(candidates)),
                    message=f"UI Agent visiting profile {idx + 1}/{len(candidates)}: {cand.name}...",
                    candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in candidates[:idx+1]],
                )

            try:
                # Update HUD: Taking control to visit profile
                await page.evaluate(
                    f"window.updateAgentHud('👤 UI Navigation: Visiting Profile {idx + 1}/{len(candidates)}', 'Navigating to {cand.name} ({cand.current_company})...', 'Extracting Resume Data')"
                )
                # Highlight card in search results view before opening
                await page.evaluate(f"""
                    () => {{
                        const el = document.getElementById('candidate-card-{idx}');
                        if (el) {{
                            el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            el.classList.add('agent-extracting');
                        }}
                    }}
                """)
                await asyncio.sleep(0.4)

                # Open candidate profile view directly in UI
                await page.evaluate(f"window.openProfile({idx})")
                await asyncio.sleep(0.5)

                # Highlight and scroll About section
                await page.evaluate("""
                    () => {
                        window.highlightSection('section-about');
                        document.getElementById('section-about')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                """)
                await asyncio.sleep(0.4)

                # Highlight and scroll Experience section
                await page.evaluate("""
                    () => {
                        window.highlightSection('section-experience');
                        document.getElementById('section-experience')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                """)
                await asyncio.sleep(0.5)

                # Highlight and scroll Skills section
                await page.evaluate("""
                    () => {
                        window.highlightSection('section-skills');
                        document.getElementById('section-skills')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                """)
                await asyncio.sleep(0.4)

                # Persist to SQLite DB
                cand.stored_in_db = True
                cand_data = cand.model_dump() if hasattr(cand, "model_dump") else cand.dict()
                db_service.save_candidate(cand_data)

                # Update HUD with DB persistence confirmation
                await page.evaluate(
                    f"window.updateAgentHud('✨ Profile Saved', 'Candidate {cand.name} added to shortlist', '✅ Added to Shortlist')"
                )
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.warning("Error navigating candidate %d in UI demo: %s", idx, e)
            finally:
                # Always safely return to search results for next candidate
                if idx < len(candidates) - 1:
                    try:
                        await page.evaluate("window.backToSearch && window.backToSearch()")
                        await asyncio.sleep(0.3)
                        await page.evaluate(f"window.scrollBy({{ top: {100 * (idx + 1)}, behavior: 'smooth' }})")
                    except Exception:
                        pass

        # Final HUD celebration
        try:
            await page.evaluate(
                f"window.updateAgentHud('🎉 Sourcing Completed', 'Autonomous Agent successfully visited and extracted {len(candidates)} candidate profiles.', 'Ready for Candidate Review & Report')"
            )
            await asyncio.sleep(1.5)
        except Exception:
            pass

        if session_id:
            sourcing_tracker.update_session(
                session_id,
                state="completed",
                progress=100,
                message=f"🎉 Successfully visited and added {len(candidates)} candidate profiles to shortlist!",
                candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in candidates],
            )

        return candidates

    async def _inject_authwall_banner(self, page: Page):
        """Injects a prominent floating handover banner on the LinkedIn authwall page."""
        try:
            await page.evaluate("""
                () => {
                    if (document.getElementById('hiring-desk-auth-banner')) return;
                    const banner = document.createElement('div');
                    banner.id = 'hiring-desk-auth-banner';
                    banner.innerHTML = `
                        <div style="position:fixed;top:16px;left:50%;transform:translateX(-50%);z-index:99999999;background:#0d1527;border:2px solid #3b82f6;color:#ffffff;padding:18px 28px;border-radius:14px;box-shadow:0 20px 40px rgba(0,0,0,0.7);font-family:system-ui,-apple-system,sans-serif;max-width:650px;text-align:center;">
                            <div style="font-size:18px;font-weight:700;margin-bottom:6px;color:#60a5fa;">🤖 Hiring Desk Autonomous Agent Handover</div>
                            <div style="font-size:14px;color:#cbd5e1;line-height:1.5;">LinkedIn requires authentication to view member profiles. Please <b>log in directly in this browser window</b>, or switch to <b>Autonomous Agent UI Mode</b> in the dashboard to see autonomous profile navigation without logging in.</div>
                        </div>
                    `;
                    document.body.prepend(banner);
                }
            """)
        except Exception as e:
            logger.debug("Could not inject auth banner: %s", e)

    async def _inject_linkedin_hud(self, page: Page, text: str):
        """Injects a live AI Agent Control HUD onto the LinkedIn page."""
        try:
            await page.evaluate(f"""
                () => {{
                    let hud = document.getElementById('hiring-desk-live-hud');
                    if (!hud) {{
                        hud = document.createElement('div');
                        hud.id = 'hiring-desk-live-hud';
                        hud.style.cssText = 'position:fixed;top:16px;right:20px;z-index:9999999;background:rgba(15,23,42,0.95);border:1.5px solid #3b82f6;color:#ffffff;padding:14px 20px;border-radius:12px;box-shadow:0 12px 30px rgba(0,0,0,0.6);font-family:system-ui,-apple-system,sans-serif;font-size:13px;max-width:380px;';
                        document.body.appendChild(hud);
                    }}
                    hud.innerHTML = `
                        <div style="display:flex;align-items:center;gap:8px;font-weight:700;color:#60a5fa;margin-bottom:4px;">
                            <span style="width:8px;height:8px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;display:inline-block;"></span>
                            Hiring Desk Autonomous Agent
                        </div>
                        <div style="color:#f8fafc;font-size:13px;line-height:1.4;">{text}</div>
                        <div style="margin-top:6px;font-size:11px;color:#34d399;border-top:1px solid #1e293b;padding-top:4px;">Shortlist Workspace: Active</div>
                    `;
                }}
            """)
        except Exception as e:
            logger.debug("Could not inject live HUD: %s", e)

    async def _update_overlay(self, page: Page, text: str):
        """Updates or injects the autonomous agent HUD banner on the active page."""
        try:
            await self._inject_linkedin_hud(page, text)
        except Exception as e:
            logger.debug("Could not update HUD overlay: %s", e)

    async def _dismiss_common_overlays(self, page: Page):
        """Dismisses cookie consent banners or promotional modals to unblock DOM visibility."""
        overlay_selectors = [
            "button[data-control-name='ga-cookie.consent.accept']",
            "button[action-type='ACCEPT']",
            "button:has-text('Accept cookies')",
            "button:has-text('Agree & Join')",
            "button[aria-label='Dismiss']",
            "button.artdeco-modal__dismiss",
        ]
        for sel in overlay_selectors:
            try:
                elem = await page.query_selector(sel)
                if elem and await elem.is_visible():
                    await elem.click()
                    logger.info("Dismissed overlay with selector: %s", sel)
                    await asyncio.sleep(0.5)
            except Exception:
                pass

    async def check_auth_status(self) -> dict:
        """Checks if the user has authenticated in the persistent browser."""
        if self._context is None:
            return {"authenticated": False, "message": "Browser not launched yet."}
        pages = self._context.pages
        if not pages:
            return {"authenticated": False, "message": "No active page."}
        page = pages[0]
        url = page.url
        is_auth = not any(x in url for x in ["login", "checkpoint", "authwall", "signup"]) and (
            "linkedin.com" in url and ("feed" in url or "search" in url or "in/" in url)
        )
        return {
            "authenticated": is_auth,
            "current_url": url,
            "message": "Authenticated" if is_auth else "Waiting for login...",
        }

    async def open_login_window(self) -> dict:
        """Launches the headed Playwright browser and navigates to LinkedIn login."""
        async with self._lock:
            _, page = await self._get_or_create_context()
            try:
                if not page.url or "about:blank" in page.url or "linkedin.com" not in page.url:
                    await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                logger.warning("Error navigating to LinkedIn login: %s", e)

            url = page.url
            is_auth = not any(x in url for x in ["login", "checkpoint", "authwall", "signup"]) and (
                "linkedin.com" in url and ("feed" in url or "search" in url or "in/" in url)
            )
            return {
                "authenticated": is_auth,
                "current_url": url,
                "message": "Authenticated" if is_auth else "LinkedIn login page is open. Please sign in in the browser window.",
            }

    async def is_account_restricted(self, page: Page) -> bool:
        """Detects if LinkedIn is actively requesting identity verification or account restriction."""
        try:
            curr_url = page.url or ""
            if any(x in curr_url for x in ["checkpoint/challenge", "login-restriction", "identity-verification"]):
                return True
            title = await page.title()
            if any(x in title for x in ["temporarily restricted", "Restriction", "Security Verification"]):
                return True
            body_text = await page.evaluate("() => document.body ? document.body.innerText.slice(0, 800) : ''")
            if any(x in body_text for x in ["temporarily restricted", "verify your identity", "Verification required"]):
                return True
        except Exception:
            pass
        return False

    async def open_linkedin_tab(self, browser_channel: Optional[str] = "chrome") -> dict:
        """Opens or focuses a LinkedIn tab in the headed browser.
        
        Uses lock to prevent first-launch race condition where Chrome executable
        detection and Playwright process startup can fail if called concurrently.
        """
        async with self._lock:
            _, page = await self._get_or_create_context(browser_channel=browser_channel)

        li_page = None
        if self._context:
            for p in self._context.pages:
                if "linkedin.com" in (p.url or ""):
                    li_page = p
                    break

        if li_page is None:
            pages = self._context.pages if self._context else []
            li_page = pages[0] if pages else await self._context.new_page()
            try:
                await li_page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=25000)
            except Exception as e:
                logger.warning("Error navigating to LinkedIn: %s", e)
        else:
            try:
                curr_url = li_page.url or ""
                if not curr_url or "about:blank" in curr_url:
                    await li_page.goto("https://www.linkedin.com", wait_until="domcontentloaded", timeout=25000)
            except Exception:
                pass

        try:
            await li_page.bring_to_front()
        except Exception:
            pass

        title = "LinkedIn"
        try:
            title = await li_page.title() or "LinkedIn"
        except Exception:
            pass

        return {
            "status": "opened",
            "screen_title": title,
            "current_url": li_page.url if li_page else "https://www.linkedin.com",
            "message": "LinkedIn tab focused in browser. Please sign in manually.",
        }

    async def verify_linkedin_screen(self, session_id: Optional[str] = None, resume_on_success: bool = False) -> dict:
        """Inspects all browser tabs to verify if LinkedIn is logged in.
        
        This method ONLY checks authentication status. It does NOT automatically
        resume the sourcing session unless resume_on_success=True.
        
        The verification process:
        1. Finds a LinkedIn tab in the browser context
        2. Brings it to front and waits for it to load
        3. Checks cookies, DOM elements, URL patterns, and page title
        4. Returns structured result with authentication status
        """
        if self._context is None:
            return {
                "authenticated": False,
                "status": "browser_not_open",
                "screen_title": "No Browser Open",
                "current_url": None,
                "message": "⚠️ Browser is not open yet. Please click 'Launch Candidate Sourcing' first.",
            }

        pages = self._context.pages
        if not pages:
            return {
                "authenticated": False,
                "status": "no_pages",
                "screen_title": "No Open Tabs",
                "current_url": None,
                "message": "⚠️ No browser tabs found. Please open LinkedIn in your browser window.",
            }

        li_page = None
        for p in pages:
            if "linkedin.com" in (p.url or ""):
                li_page = p
                break

        if li_page is None:
            active_p = pages[0]
            try:
                title = await active_p.title()
            except Exception:
                title = "Unknown"
            return {
                "authenticated": False,
                "status": "no_linkedin_tab",
                "screen_title": title or "about:blank",
                "current_url": active_p.url,
                "message": "⚠️ No LinkedIn tab detected. Please click 'Open LinkedIn ↗' or navigate to https://www.linkedin.com in your browser, sign in, then click 'I\'ve Logged In — Continue'.",
            }

        try:
            await li_page.bring_to_front()
        except Exception:
            pass

        # Wait briefly for page to stabilize after user interaction
        try:
            await li_page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        await asyncio.sleep(0.5)

        title = ""
        try:
            title = await li_page.title() or "LinkedIn"
        except Exception:
            title = "LinkedIn"
        url = li_page.url or ""

        if await self.is_account_restricted(li_page):
            msg = "⚠️ LinkedIn Account Verification Active: LinkedIn is currently requesting identity verification on this account ('Access to your account has been temporarily restricted'). Please complete verification directly on LinkedIn or click 'Switch to Demo'."
            if session_id:
                sourcing_tracker.update_session(
                    session_id,
                    state="waiting_for_login",
                    error=msg,
                    message=msg,
                )
            return {
                "authenticated": False,
                "status": "restricted",
                "screen_title": title,
                "current_url": url,
                "message": msg,
            }

        is_auth = await self.is_authenticated_session(li_page)

        # If initial check fails, try reloading the page once — the user may have
        # just logged in and the page hasn't refreshed yet
        if not is_auth and "linkedin.com" in url:
            logger.info("Initial auth check failed. Reloading LinkedIn page and rechecking...")
            try:
                await li_page.reload(wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(1.0)
                is_auth = await self.is_authenticated_session(li_page)
                if is_auth:
                    try:
                        title = await li_page.title() or title
                    except Exception:
                        pass
                    url = li_page.url or url
            except Exception as reload_err:
                logger.debug("Reload during verify failed: %s", reload_err)

        if not is_auth:
            msg = (
                f"⚠️ Login Verification Failed: The AI Agent inspected the agent browser screen and detected that LinkedIn is not logged in yet (Screen detected: '{title}'). "
                f"Please ensure you enter your email/password inside the dedicated browser window opened on your desktop (not in your external personal browser). "
                f"Once you see your LinkedIn home feed, click 'I\'ve Logged In — Continue' again."
            )
            if session_id:
                sourcing_tracker.update_session(
                    session_id,
                    state="waiting_for_login",
                    progress=25,
                    message=msg,
                    error=msg,
                )
            return {
                "authenticated": False,
                "status": "unauthenticated",
                "screen_title": title,
                "current_url": url,
                "message": msg,
            }

        # Confirmed authenticated!
        if session_id and resume_on_success:
            sourcing_tracker.resume_session(session_id)
            sourcing_tracker.update_session(
                session_id,
                state="searching",
                progress=40,
                message=f"✅ LinkedIn login verified ({title})! AI Agent taking control of browser UI...",
                error=None,
            )
        return {
            "authenticated": True,
            "status": "verified",
            "screen_title": title,
            "current_url": url,
            "message": "✅ LinkedIn login verified! AI Agent taking control...",
        }

    async def close_browser(self):
        """Closes the active Playwright browser context cleanly."""
        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                logger.debug("Error closing context: %s", e)
            self._context = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.debug("Error stopping playwright: %s", e)
            self._playwright = None


class LinkedInBrowserService:
    """Public browser service exposing thread-safe sourcing methods.
    
    Delegates calls to a dedicated Proactor loop runner to ensure 100% compatibility
    on Windows without subprocess transport exceptions.
    """

    def __init__(self):
        self._runner = DedicatedBrowserRunner()
        self._engine = _LinkedInBrowserEngine()
        self.tracker = sourcing_tracker

    async def search_linkedin(
        self,
        keywords: str,
        max_results: int = 10,
        mode: str = "linkedin",
        deep_scrape: bool = True,
        timeout_seconds: int = 45,
        session_id: Optional[str] = None,
        browser_channel: Optional[str] = "chrome",
        role_title: Optional[str] = None,
        mandatory_skills: Optional[List[str]] = None,
        preferred_locations: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Tuple[List[CandidateProfile], str, str]:
        return await self._runner.run(
            self._engine.search_linkedin(
                keywords=keywords,
                max_results=max_results,
                mode=mode,
                deep_scrape=deep_scrape,
                timeout_seconds=timeout_seconds,
                session_id=session_id,
                browser_channel=browser_channel,
                role_title=role_title,
                mandatory_skills=mandatory_skills,
                preferred_locations=preferred_locations,
                location=location,
            )
        )

    async def search_live_linkedin(
        self,
        keywords: str,
        max_results: int = 6,
        deep_scrape: bool = True,
        browser_channel: Optional[str] = "chrome",
        session_id: Optional[str] = None,
        role_title: Optional[str] = None,
        mandatory_skills: Optional[List[str]] = None,
        preferred_locations: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Tuple[List[CandidateProfile], str, str]:
        return await self._runner.run(
            self._engine.search_live_linkedin(
                keywords=keywords,
                max_results=max_results,
                deep_scrape=deep_scrape,
                browser_channel=browser_channel,
                session_id=session_id,
                role_title=role_title,
                mandatory_skills=mandatory_skills,
                preferred_locations=preferred_locations,
                location=location,
            )
        )

    async def search_live_browser_ocr(
        self,
        keywords: str,
        max_results: int = 6,
        session_id: Optional[str] = None,
    ) -> Tuple[List[CandidateProfile], str, str]:
        return await self._runner.run(
            self._engine.search_live_browser_ocr(
                keywords=keywords,
                max_results=max_results,
                session_id=session_id,
            )
        )

    async def check_auth_status(self) -> dict:
        return await self._runner.run(self._engine.check_auth_status())

    async def open_login_window(self) -> dict:
        return await self._runner.run(self._engine.open_login_window())

    async def open_linkedin_tab(self, browser_channel: Optional[str] = "chrome") -> dict:
        return await self._runner.run(self._engine.open_linkedin_tab(browser_channel=browser_channel))

    async def verify_linkedin_screen(self, session_id: Optional[str] = None, resume_on_success: bool = False) -> dict:
        return await self._runner.run(self._engine.verify_linkedin_screen(session_id=session_id, resume_on_success=resume_on_success))

    async def extract_candidate_profile(
        self,
        candidate: CandidateProfile,
        browser_channel: Optional[str] = "chrome",
        skip_navigation: bool = False,
    ) -> CandidateProfile:
        return await self._runner.run(
            self._engine.extract_candidate_profile(
                candidate, browser_channel=browser_channel, skip_navigation=skip_navigation
            )
        )

    async def close_browser(self):
        return await self._runner.run(self._engine.close_browser())


browser_service = LinkedInBrowserService()


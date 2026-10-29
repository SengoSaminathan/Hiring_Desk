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
from backend.app.services.db_service import db_service

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
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="PlaywrightWorker")
        self._thread.start()
        self._ready.wait()

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
                    "--no-sandbox",
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
        encoded_query = urllib.parse.quote_plus(keywords.strip())
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

                # Step 2: Agent takes control of UI and navigates directly to LinkedIn Search
                if session_id:
                    sourcing_tracker.update_session(
                        session_id,
                        state="searching",
                        progress=40,
                        message=f"Agent taking control of UI: Navigating directly to LinkedIn search for '{keywords}'...",
                        error=None,
                    )

                logger.info("Agent taking control: Navigating directly to LinkedIn search URL: %s", search_url)
                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    logger.warning("Search goto warning: %s. Continuing...", e)

                # Check if search navigation got trapped by authwall or security checkpoint!
                curr_url = page.url or ""
                if any(x in curr_url for x in ["login", "checkpoint", "authwall", "signup"]):
                    logger.warning("Authwall or login checkpoint detected during search navigation! URL: %s", curr_url)
                    if session_id:
                        sourcing_tracker.update_session(
                            session_id,
                            state="waiting_for_login",
                            progress=25,
                            message="LinkedIn verification checkpoint or sign-in required. Please complete it in the browser window, then click Proceed.",
                            error="LinkedIn checkpoint or login required.",
                        )
                    await self._inject_login_handover_banner(page, channel_name)
                    # Loop until cleared
                    while True:
                        if session_id:
                            sess = sourcing_tracker.get_session(session_id)
                            if sess and sess.get("should_stop"):
                                return [], curr_url, "Sourcing session stopped by user."
                        resumed = session_id and sourcing_tracker.is_resumed(session_id)
                        is_ok = await self.is_authenticated_session(page)
                        if (resumed or is_ok) and not any(x in (page.url or "") for x in ["login", "checkpoint", "authwall", "signup"]):
                            break
                        if resumed and not is_ok:
                            sourcing_tracker.reset_resume(session_id)
                            await self._inject_login_warning_banner(page)
                        await asyncio.sleep(1.0)

                    # Re-navigate to search URL after clearance
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                # Dismiss common modal/cookie overlays
                await self._dismiss_common_overlays(page)

                # Inject HUD indicating Agent is actively controlling UI
                await self._inject_linkedin_hud(page, f"🤖 HiringDesk Agent: UI Control Active. Searching candidate profiles for: '{keywords}'...")

                # Smooth scroll to trigger dynamic loading of search cards
                try:
                    await page.evaluate("window.scrollBy({ top: 400, behavior: 'smooth' })")
                    await asyncio.sleep(1.2)
                except Exception:
                    pass

                # Step 3: Extract Candidate Cards from DOM
                if session_id:
                    sourcing_tracker.update_session(
                        session_id,
                        state="extracting",
                        progress=55,
                        message="Harvesting candidate profiles from LinkedIn search results...",
                    )

                candidates = await self._extract_candidate_cards(page, max_results)

                if not candidates:
                    logger.info("Direct DOM extraction found 0 cards on LinkedIn search for query: '%s'.", keywords)
                    if await self.is_account_restricted(page):
                        raise RuntimeError("LinkedIn Account Verification Required: LinkedIn is currently requesting security/identity verification. Please complete verification directly in the opened browser window.")
                    curr_p_url = page.url or ""
                    if any(x in curr_p_url for x in ["login", "checkpoint", "authwall", "signup"]):
                        raise RuntimeError(f"LinkedIn session unauthenticated (current page: {curr_p_url}). Please log in to view candidate search results.")
                    
                    if session_id:
                        sourcing_tracker.update_session(
                            session_id,
                            state="completed",
                            progress=100,
                            message=f"LinkedIn search returned 0 matching candidate profiles for query: '{keywords}'. Try broader keywords in the JD editor.",
                            candidates=[],
                        )
                    return [], search_url, f"LinkedIn returned 0 results for query '{keywords}'."

                # Step 4: Autonomous UI Agent Loop — Visit profiles one-by-one to extract detailed resumes & avatars
                if deep_scrape:
                    enriched_candidates = []
                    for idx, cand in enumerate(candidates[:max_results]):
                        if session_id:
                            sess = sourcing_tracker.get_session(session_id)
                            if sess and sess.get("should_stop"):
                                break
                            prog = 60 + int((idx / max(1, len(candidates[:max_results]))) * 25)
                            sourcing_tracker.update_session(
                                session_id,
                                state="extracting",
                                progress=prog,
                                message=f"Agent taking control: Profiling candidate {idx+1}/{len(candidates)}: {cand.name}...",
                            )

                        if cand.canonical_url and "linkedin.com/in/" in cand.canonical_url and not cand.canonical_url.endswith("-1"):
                            logger.info("Agent UI navigation: Visiting %d/%d: %s (%s)", idx + 1, len(candidates), cand.name, cand.canonical_url)
                            await self._inject_linkedin_hud(page, f"👤 Profiling Candidate {idx + 1}/{len(candidates)}: {cand.name} — Extracting Experience & Skills...")
                            cand = await self._visit_and_extract_profile(page, cand)

                        if not cand.avatar_url:
                            cand.avatar_url = VERIFIED_AVATARS[idx % len(VERIFIED_AVATARS)]

                        cand.stored_in_db = True
                        cand_data = cand.model_dump() if hasattr(cand, "model_dump") else cand.dict()
                        db_service.save_candidate(cand_data)
                        enriched_candidates.append(cand)

                        if session_id:
                            sourcing_tracker.update_session(
                                session_id,
                                candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in enriched_candidates],
                            )
                        await asyncio.sleep(1.2)
                    candidates = enriched_candidates
                else:
                    for idx, cand in enumerate(candidates):
                        if not cand.avatar_url:
                            cand.avatar_url = VERIFIED_AVATARS[idx % len(VERIFIED_AVATARS)]
                        cand.stored_in_db = True
                        cand_data = cand.model_dump() if hasattr(cand, "model_dump") else cand.dict()
                        db_service.save_candidate(cand_data)

                # Step 5: Finalize & Persist to SQLite
                if session_id:
                    sourcing_tracker.update_session(
                        session_id,
                        state="persisting",
                        progress=90,
                        message=f"Persisting {len(candidates)} candidate profiles to SQLite database (hiring_desk.db)...",
                        candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in candidates],
                    )

                for cand in candidates:
                    try:
                        cand_data = cand.model_dump() if hasattr(cand, "model_dump") else cand.dict()
                        db_service.save_candidate(cand_data)
                    except Exception as err:
                        logger.warning("Could not persist candidate to DB: %s", err)

                # Step 6: Inform user in browser HUD and return to Hiring Desk portal
                await self._inject_linkedin_hud(
                    page,
                    f"🎉 Sourcing Complete! Harvested {len(candidates)} candidate profiles into SQLite database. 🔄 Returning to Hiring Desk Portal in 3s..."
                )

                if session_id:
                    sourcing_tracker.update_session(
                        session_id,
                        state="completed",
                        progress=100,
                        message=f"🎉 Successfully harvested {len(candidates)} candidates directly from LinkedIn! Returning to Hiring Desk portal...",
                        candidates=[c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in candidates],
                    )

                # Wait 2.5 seconds so user reads completion HUD
                await asyncio.sleep(2.5)

                # Redirect browser back to the Hiring Desk portal
                portal_url = "http://localhost:3000"
                try:
                    logger.info("Redirecting browser back to portal: %s", portal_url)
                    await page.goto(portal_url, wait_until="domcontentloaded", timeout=12000)
                    welcome_script = f"""
                    (() => {{
                        let toast = document.createElement('div');
                        toast.id = 'hiring-desk-portal-toast';
                        toast.style.position = 'fixed';
                        toast.style.top = '24px';
                        toast.style.right = '24px';
                        toast.style.zIndex = '9999999';
                        toast.style.background = '#0f172a';
                        toast.style.color = '#ffffff';
                        toast.style.border = '2px solid #10b981';
                        toast.style.borderRadius = '16px';
                        toast.style.padding = '16px 24px';
                        toast.style.boxShadow = '0 10px 35px rgba(0,0,0,0.6), 0 0 25px rgba(16,185,129,0.5)';
                        toast.style.fontFamily = 'system-ui, -apple-system, sans-serif';
                        toast.style.maxWidth = '380px';
                        toast.innerHTML = `
                            <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                                <span style="font-size:20px;">🎉</span>
                                <strong style="color:#34d399; font-size:15px;">Welcome Back to Hiring Desk!</strong>
                            </div>
                            <div style="color:#cbd5e1; font-size:12px; line-height:1.5;">
                                Sourcing complete! Harvested <strong>{len(candidates)}</strong> candidate profiles into your SQLite database. Your shortlist is ready for review.
                            </div>
                        `;
                        document.body.appendChild(toast);
                        setTimeout(() => {{ if (toast) toast.remove(); }}, 8000);
                    }})();
                    """
                    await page.evaluate(welcome_script)
                except Exception as e:
                    logger.debug("Portal redirect exception: %s", e)

                return (
                    candidates,
                    search_url,
                    f"SUCCESS_LIVE_LINKEDIN: Autonomous agent sourced {len(candidates)} candidate profiles directly from LinkedIn into SQLite database and returned to portal.",
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
                # Clean badges like "1st", "2nd", "View profile"
                name = re.sub(r"\b(1st|2nd|3rd|View profile)\b", "", name, flags=re.IGNORECASE).strip()
                if not name or name.lower() in ("linkedin member", "view profile"):
                    name = f"LinkedIn Candidate #{len(candidates)+1}"

                # Headline
                sub_elem = await card.query_selector(
                    ".entity-result__primary-subtitle, .subline-level-1, .artdeco-entity-lockup__subtitle, div.t-14.t-black"
                )
                headline = (await sub_elem.inner_text()).strip() if sub_elem else "Software Professional"
                headline = re.sub(r"\s+", " ", headline).strip()

                # Location
                loc_elem = await card.query_selector(
                    ".entity-result__secondary-subtitle, .subline-level-2, .artdeco-entity-lockup__caption, div.t-12.t-black--light"
                )
                location = (await loc_elem.inner_text()).strip() if loc_elem else "Location not specified"
                location = re.sub(r"\s+", " ", location).strip()

                # Summary / Snippet
                snippet_elem = await card.query_selector(".entity-result__summary, p.entity-result__summary, p.t-12")
                snippet = (await snippet_elem.inner_text()).strip() if snippet_elem else f"{name} - {headline}"

                company = None
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
                    raw_snippet=snippet,
                    skills=[],
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
                    clean_name = re.sub(r"\s+", " ", text).split("\n")[0].strip()
                    if not clean_name or len(clean_name) < 2 or clean_name.lower() in ("linkedin member", "view profile", "connect", "message"):
                        continue
                    ts = int(time.time() * 1000)
                    candidates.append(CandidateProfile(
                        id=f"cand_{ts}_{len(candidates)+1}",
                        name=clean_name,
                        canonical_url=canonical_url,
                        headline="Professional on LinkedIn",
                        location="Location on Profile",
                        raw_snippet=f"{clean_name} — Profile found on LinkedIn",
                        skills=[],
                    ))
                except Exception:
                    pass

        return candidates

    async def _visit_and_extract_profile(self, page: Page, candidate: CandidateProfile) -> CandidateProfile:
        """Autonomous Agent UI Action: Navigates to candidate profile, scrolls, and extracts detailed resume sections."""
        try:
            logger.info("Agent UI navigation: Visiting %s", candidate.canonical_url)
            await page.goto(candidate.canonical_url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(1.2)
            await self._dismiss_common_overlays(page)

            # Autonomous UI Action: Smooth scrolling down to trigger lazy loading of profile sections
            for scroll_step in [500, 900, 1400]:
                await page.evaluate(f"window.scrollBy({{ top: {scroll_step}, behavior: 'smooth' }})")
                await asyncio.sleep(0.6)

            # Try to click "see more" / "Show all" buttons in About & Experience
            try:
                see_more_btns = await page.query_selector_all(
                    "button.inline-show-more-text__button, button[aria-label*='more'], button:has-text('see more')"
                )
                for btn in see_more_btns[:3]:
                    if await btn.is_visible():
                        await btn.click()
                        await asyncio.sleep(0.2)
            except Exception:
                pass

            # 1. Extract About / Summary
            about_text = ""
            about_elem = await page.query_selector(
                "section.artdeco-card:has(#about) div.inline-show-more-text, div#about ~ div span[aria-hidden='true'], section[data-section='about'] p"
            )
            if about_elem:
                about_text = (await about_elem.inner_text()).strip()

            # 2. Extract Experience records
            experience_items = []
            exp_cards = await page.query_selector_all(
                "section.artdeco-card:has(#experience) ul.pvs-list > li, div#experience ~ div ul.pvs-list > li, section[data-section='experience'] ul > li"
            )
            for card in exp_cards[:5]:
                try:
                    title_elem = await card.query_selector("span[aria-hidden='true'], div.display-flex span[aria-hidden='true']")
                    title_text = (await title_elem.inner_text()).strip() if title_elem else "Role"
                    company_elem = await card.query_selector("span.t-14.t-normal span[aria-hidden='true']")
                    comp_text = (await company_elem.inner_text()).strip() if company_elem else ""
                    date_elem = await card.query_selector("span.t-black--light span[aria-hidden='true']")
                    date_text = (await date_elem.inner_text()).strip() if date_elem else ""
                    desc_elem = await card.query_selector("div.pvs-entity__sub-components span[aria-hidden='true'], div.inline-show-more-text")
                    desc_text = (await desc_elem.inner_text()).strip() if desc_elem else ""
                    if title_text:
                        experience_items.append({
                            "title": title_text,
                            "company": comp_text,
                            "dates": date_text,
                            "description": desc_text,
                        })
                except Exception:
                    continue

            # 3. Extract Skills
            extracted_skills = list(candidate.skills)
            skill_elems = await page.query_selector_all(
                "section.artdeco-card:has(#skills) ul.pvs-list > li span[aria-hidden='true'], div#skills ~ div ul > li span[aria-hidden='true']"
            )
            for se in skill_elems[:12]:
                stext = (await se.inner_text()).strip()
                if stext and len(stext) < 35 and stext not in extracted_skills:
                    extracted_skills.append(stext)

            # Build enriched resume snippet
            snippet_parts = []
            if about_text:
                snippet_parts.append(f"About: {about_text}")
            if experience_items:
                exp_summary = " | ".join(f"{e['title']} at {e['company']} ({e.get('dates', '')})" for e in experience_items)
                snippet_parts.append(f"Experience: {exp_summary}")
            if extracted_skills:
                snippet_parts.append(f"Skills: {', '.join(extracted_skills)}")

            full_snippet = "\n".join(snippet_parts) if snippet_parts else candidate.raw_snippet

            candidate.about = about_text or candidate.about
            candidate.experience_history = experience_items if experience_items else candidate.experience_history
            candidate.skills = extracted_skills if extracted_skills else candidate.skills
            candidate.raw_snippet = full_snippet
            candidate.stored_in_db = True

            return candidate
        except Exception as e:
            logger.warning("Error deep-extracting profile %s: %s", candidate.canonical_url, e)
            candidate.stored_in_db = True
            return candidate

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
                    "name": "David Kim",
                    "headline": "Lead AI Systems Engineer at Scale AI | Python, FastAPI, Playwright, LLM Orchestration",
                    "company": "Scale AI",
                    "location": "San Francisco, CA",
                    "years": 8.0,
                    "skills": ["Python", "FastAPI", "Playwright", "LLM Orchestration", "AsyncIO", "PostgreSQL"],
                    "snippet": "Specializing in autonomous agent state machines, Playwright web automation, and resilient multi-model pipelines.",
                    "history": [
                        {"title": "Lead AI Systems Engineer", "company": "Scale AI", "dates": "2021 - Present (3.5 yrs)", "description": "Architected autonomous web extraction pipelines using Playwright and asynchronous task orchestrators."},
                        {"title": "Senior Backend Engineer", "company": "Twilio", "dates": "2017 - 2021 (4.0 yrs)", "description": "Built distributed telephony webhook dispatch engine handling 50k requests/sec."}
                    ]
                },
                {
                    "name": "Ananya Patel",
                    "headline": "Senior Backend & Agent Engineer at Anthropic | Python, FastAPI, Distributed Systems",
                    "company": "Anthropic",
                    "location": "Seattle, WA",
                    "years": 7.0,
                    "skills": ["Python", "FastAPI", "AsyncIO", "LLM Orchestration", "Docker", "Playwright"],
                    "snippet": "7+ years architecting high-throughput backend services and state-aware LLM reasoning agents with self-healing fallback loops.",
                    "history": [
                        {"title": "Senior Backend & Agent Engineer", "company": "Anthropic", "dates": "2022 - Present (2.5 yrs)", "description": "Created tool evaluation runtime and safe browser interaction sandboxes for AI agents."},
                        {"title": "Backend Systems Engineer", "company": "Uber", "dates": "2018 - 2022 (4.0 yrs)", "description": "Engineered real-time driver dispatch matching algorithms in Python and Go."}
                    ]
                },
                {
                    "name": "Carlos Mendez",
                    "headline": "Principal Distributed Systems Engineer at Databricks | Python, AsyncIO, SQLite, REST",
                    "company": "Databricks",
                    "location": "Denver, CO",
                    "years": 9.0,
                    "skills": ["Python", "FastAPI", "AsyncIO", "SQLite", "Distributed Systems", "REST APIs"],
                    "snippet": "Distributed systems engineer building reliable, local-first database replication engines and high-concurrency microservices.",
                    "history": [
                        {"title": "Principal Systems Engineer", "company": "Databricks", "dates": "2020 - Present (4.0 yrs)", "description": "Designed local cache persistence and transactional WAL coordination mechanisms."},
                        {"title": "Senior Infrastructure Developer", "company": "Red Hat", "dates": "2016 - 2020 (4.0 yrs)", "description": "Maintained core Linux container orchestration plugins."}
                    ]
                },
                {
                    "name": "Samantha Brooks",
                    "headline": "Senior Python & AI Infrastructure Engineer at Meta | FastAPI, LLMs, Playwright",
                    "company": "Meta",
                    "location": "Menlo Park, CA",
                    "years": 6.5,
                    "skills": ["Python", "FastAPI", "Playwright", "LLMs", "LangChain", "Docker"],
                    "snippet": "Specialist in autonomous browser control, LLM benchmark evaluation, and robust Python web services.",
                    "history": [
                        {"title": "Senior AI Infrastructure Engineer", "company": "Meta", "dates": "2021 - Present (3.0 yrs)", "description": "Built browser automation agent workflows for evaluating multi-modal AI models."},
                        {"title": "Software Engineer", "company": "Lyft", "dates": "2018 - 2021 (3.0 yrs)", "description": "Developed backend fleet telemetry pipelines in Python and FastAPI."}
                    ]
                },
                {
                    "name": "Rohan Verma",
                    "headline": "Lead Backend Architect at Razorpay | Python, FastAPI, High-Throughput REST APIs",
                    "company": "Razorpay",
                    "location": "Bengaluru, India",
                    "years": 7.5,
                    "skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs", "AsyncIO", "System Design"],
                    "snippet": "7+ years designing financial transaction gateways and resilient distributed APIs with strict schema validation.",
                    "history": [
                        {"title": "Lead Backend Architect", "company": "Razorpay", "dates": "2020 - Present (4.0 yrs)", "description": "Scaled payment capture engine to 25k TPS with 99.999% availability."},
                        {"title": "Software Engineer II", "company": "Flipkart", "dates": "2017 - 2020 (3.5 yrs)", "description": "Built inventory reservation service with distributed locking."}
                    ]
                },
                {
                    "name": "Maya Lin",
                    "headline": "Staff AI Workflow Engineer at OpenAI | Autonomous Agents, Python, FastAPI, Browser Control",
                    "company": "OpenAI",
                    "location": "San Francisco, CA",
                    "years": 8.5,
                    "skills": ["Python", "FastAPI", "Playwright", "Autonomous Agents", "LLM Orchestration"],
                    "snippet": "Pioneering state-machine browser automation agents, structured output JSON extraction, and desktop agent interfaces.",
                    "history": [
                        {"title": "Staff AI Workflow Engineer", "company": "OpenAI", "dates": "2022 - Present (2.0 yrs)", "description": "Engineered autonomous browsing safety layers and structured entity extraction."},
                        {"title": "Lead Automation Architect", "company": "Dropbox", "dates": "2017 - 2022 (5.0 yrs)", "description": "Led desktop client automated test harnesses and end-to-end telemetry."}
                    ]
                }
            ]

        results = []
        ts = int(time.time() * 1000)
        for idx, t in enumerate(templates[:count]):
            slug = t["name"].lower().replace(" ", "-")
            history = t.get("history") or [
                {
                    "title": t["headline"].split(" at ")[0].strip(),
                    "company": t["company"],
                    "dates": f"{int(t['years'])} years",
                    "description": t["snippet"],
                }
            ]
            cand = CandidateProfile(
                id=f"sim_{ts}_{idx+1}",
                name=t["name"],
                canonical_url=f"https://www.linkedin.com/in/{slug}",
                headline=t["headline"],
                current_company=t["company"],
                location=t["location"],
                experience_years=t["years"],
                skills=t["skills"],
                about=t.get("snippet", ""),
                avatar_url=VERIFIED_AVATARS[idx % len(VERIFIED_AVATARS)],
                experience_history=history,
                raw_snippet=t["snippet"],
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
                "company": c.current_company or "Technology Co.",
                "location": c.location,
                "years": c.experience_years,
                "skills": c.skills,
                "about": c.about or c.raw_snippet,
                "avatar_url": c.avatar_url or "",
                "experience_history": c.experience_history,
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
      <span id="hud-db">💾 SQLite: data/hiring_desk.db</span>
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
        if (stepOrDb.includes("SQLite") || stepOrDb.includes("Persisted")) {{
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
                    f"window.updateAgentHud('💾 Profile Saved to Database', 'Candidate {cand.name} successfully written to data/hiring_desk.db', '✅ Persisted in SQLite')"
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
                f"window.updateAgentHud('🎉 Sourcing Completed', 'Autonomous Agent successfully visited and extracted {len(candidates)} candidate profiles into SQLite database.', 'Ready for Candidate Review & Report')"
            )
            await asyncio.sleep(1.5)
        except Exception:
            pass

        if session_id:
            sourcing_tracker.update_session(
                session_id,
                state="completed",
                progress=100,
                message=f"🎉 Successfully visited and persisted {len(candidates)} candidate profiles to SQLite!",
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
                        <div style="margin-top:6px;font-size:11px;color:#34d399;border-top:1px solid #1e293b;padding-top:4px;">Persistence: data/hiring_desk.db</div>
                    `;
                }}
            """)
        except Exception as e:
            logger.debug("Could not inject live HUD: %s", e)

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
            )
        )

    async def search_live_linkedin(
        self,
        keywords: str,
        max_results: int = 6,
        deep_scrape: bool = True,
        browser_channel: Optional[str] = "chrome",
        session_id: Optional[str] = None,
    ) -> Tuple[List[CandidateProfile], str, str]:
        return await self._runner.run(
            self._engine.search_live_linkedin(
                keywords=keywords,
                max_results=max_results,
                deep_scrape=deep_scrape,
                browser_channel=browser_channel,
                session_id=session_id,
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

    async def close_browser(self):
        return await self._runner.run(self._engine.close_browser())


browser_service = LinkedInBrowserService()


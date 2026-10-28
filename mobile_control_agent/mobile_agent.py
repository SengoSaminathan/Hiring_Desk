"""Mobile Agent - Autonomous Android Automation with State-Aware Observe-Plan-Act-Verify,
Intelligent Loop Detection, Autonomous Recovery, and Payment Handover.
"""

import asyncio
from datetime import datetime, timezone
import io
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from PIL import Image

# Import Modular Architectural Components
from models_and_state import (
    NavigationIntent,
    ScreenObservation,
    ActionRecord,
    TaskState,
    compute_visual_hash,
    visual_hash_distance,
)
from screen_classifier import ScreenClassifier
from loop_detector import LoopDetector, LoopDetectionResult
from llm_service import LLMService
from recovery_controller import RecoveryController
from payment_service import payment_service
from order_verifier import OrderVerifier, VerificationResult

# Optional OTP helpers from project
try:
    from gmail_otp import fetch_gmail_otp
except ImportError:
    fetch_gmail_otp = None

try:
    from mongo_otp import find_sms_otp
except ImportError:
    find_sms_otp = None

load_dotenv()

COMMON_APP_PACKAGES = {
    "flipkart": "com.flipkart.android",
    "amazon": "com.amazon.mShop.android.shopping",
    "swiggy": "in.swiggy.android",
    "zomato": "com.application.zomato",
    "whatsapp": "com.whatsapp",
    "chrome": "com.android.chrome",
    "browser": "com.android.chrome",
    "youtube": "com.google.android.youtube",
    "playstore": "com.android.vending",
    "play store": "com.android.vending",
    "settings": "com.android.settings",
    "gmail": "com.google.android.gm",
    "maps": "com.google.android.apps.maps",
    "camera": "com.android.camera",
    "gpay": "com.google.android.apps.nbu.paisa.user",
    "google pay": "com.google.android.apps.nbu.paisa.user",
    "phonepe": "com.phonepe.app",
    "paytm": "net.one97.paytm",
    "bhim": "in.org.npci.upiapp",
}

MAIN_SYSTEM_INSTRUCTION = """You are an expert autonomous Android mobile device agent.
Your goal is to complete the user's task by observing the screen and choosing the single next best action.

Coordinate System:
- All coordinates are normalized integers between 0 and 1000.
- y: 0 is top edge, 1000 is bottom edge.
- x: 0 is left edge, 1000 is right edge.
- Example: center is [500, 500].

Available Actions:
1. "launch": Directly start an app by name or package.
   {"thought": "...", "action": "launch", "app": "flipkart", "expected_postcondition": "Flipkart home opens"}
2. "tap": Tap at a specific point on the screen.
   {"thought": "...", "action": "tap", "point": [y, x], "expected_postcondition": "Item selected or screen changes"}
3. "type": Type text into an already focused input field.
   {"thought": "...", "action": "type", "text": "die cast cars", "press_enter": true, "expected_postcondition": "Search executed"}
4. "swipe": Swipe or scroll the screen.
   direction: "up" (scrolls content down), "down" (scrolls content up), "left", "right".
   {"thought": "...", "action": "swipe", "direction": "up", "expected_postcondition": "More items revealed"}
5. "key": Press a hardware/system navigation key: "back", "home", "enter", "app_switch".
   {"thought": "...", "action": "key", "key": "back", "expected_postcondition": "Returns to previous screen"}
6. "wait": Wait 2 seconds for page or app to finish loading.
   {"thought": "...", "action": "wait", "expected_postcondition": "Loading completes"}
7. "otp": The screen is asking for an OTP/verification code. Request OTP auto-fetch.
   {"thought": "...", "action": "otp", "expected_postcondition": "OTP typed and submitted"}
8. "initiate_payment": A payment screen is visible that requires user authorization.
   {"thought": "...", "action": "initiate_payment", "amount": 499.0, "currency": "INR", "payee_name": "Flipkart", "scenario": "GATEWAY_ORDER"}
9. "done": The task has been successfully achieved or verified.
   {"thought": "...", "action": "done", "summary": "Detailed explanation of the observable result."}

Strict Guidelines:
- Pay close attention to the Current Screen Classification and Target vs Forbidden sections.

- FLIPKART MINUTES vs REGULAR STORE (CRITICAL):
    * If screen type is FLIPKART_MINUTES, MINUTES_SEARCH_RESULTS, or MINUTES_SEARCH_SUGGESTIONS — you are in the WRONG mode.
    * DO NOT type, search, tap product cards, or scroll while inside Minutes.
    * Immediately use "key": "back" OR tap the bottom-left Shop tab OR call "launch" for flipkart.
    * When the search bar opens after escaping, type the query AND set press_enter=true. NEVER tap a suggestion — suggestions redirect back to Minutes.
    * A suggestion is forbidden if its label contains: "in Minutes", "Deliver in", "10 mins", "15 mins".
    * IMPORTANT: Delivery labels like "Get in 8 mins" inside regular product cards are shipping estimates, NOT Minutes mode. Trust the Screen Classification above all else.

- CHECKOUT RULES (CRITICAL — read carefully):
    * When asked to purchase or checkout a SPECIFIC product:
      1. Navigate to that product's detail page first.
      2. Tap "Buy Now" directly on the product page. This buys ONLY that item.
      3. NEVER use "Add to Cart" followed by "Proceed to Buy" from the cart — the cart may contain other items the user did not ask to buy.
      4. "Proceed to Buy" from the Cart page = buying ALL items in cart = strictly forbidden unless the user explicitly said "checkout my cart" or "buy everything in cart".
    * If the user said "add to cart" (not checkout): use "Add to Cart", then stop. Do NOT proceed to payment.
    * If the user said "checkout" or "purchase" or "buy": use "Buy Now" on the product page.

- PAYMENT RULE:
    * NEVER enter UPI PIN, MPIN, OTP, CVV, or any credential. Call "initiate_payment" instead.
    * Do NOT add the "app" field to initiate_payment for Flipkart/Amazon/Swiggy/Zomato — they handle payment natively.
    * Only add "app": "gpay" or "app": "phonepe" when the current app does NOT have its own payment flow.

- Always output strictly valid JSON matching this schema.
"""


class AndroidDevice:
    """Manages low-level ADB communication with the connected phone."""

    def __init__(self, adb_path: Optional[str] = None):
        self.adb = adb_path or self._find_adb()
        self.width = 1080
        self.height = 2400
        self.serial: Optional[str] = None
        self._init_device()

    def _find_adb(self) -> str:
        sdk_adb = r"C:\Users\sengo\AppData\Local\Android\Sdk\platform-tools\adb.exe"
        if os.path.exists(sdk_adb):
            return sdk_adb

        import shutil
        which_adb = shutil.which("adb")
        if which_adb:
            return which_adb

        return "adb"

    def _run_adb(self, *args, check_output: bool = True) -> subprocess.CompletedProcess:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=check_output, text=False, timeout=25)

    def _run_adb_text(self, *args) -> str:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        try:
            res = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="ignore", timeout=25,
            )
            return res.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"[ADB] Command timed out: {' '.join(args[:3])}")
            return ""

    def _init_device(self) -> None:
        devices_out = self._run_adb_text("devices")
        lines = [line.strip() for line in devices_out.splitlines() if line.strip()]
        connected = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                connected.append(parts[0])

        if not connected:
            raise RuntimeError(
                "No authorized Android device found.\n"
                "Please connect your phone with USB Debugging enabled:\n"
                "  1. Go to Settings -> Developer Options -> Turn on USB Debugging.\n"
                "  2. Unlock your phone and accept 'Always allow from this computer' prompt.\n"
                "  3. Run 'adb devices' to verify."
            )

        self.serial = connected[0]

        # Get device screen size
        size_str = self._run_adb_text("shell", "wm", "size")
        match = re.search(r"(\d+)x(\d+)", size_str)
        if match:
            self.width = int(match.group(1))
            self.height = int(match.group(2))

        model = self._run_adb_text("shell", "getprop", "ro.product.model")
        print(f"Connected to Android device: {model} ({self.serial}) - Resolution: {self.width}x{self.height}")

    def capture_screenshot(self) -> Image.Image:
        """Capture screenshot via ADB and return as PIL Image."""
        res = self._run_adb("exec-out", "screencap", "-p")
        if not res.stdout or len(res.stdout) < 1000:
            raise RuntimeError("Failed to capture screenshot from Android device. Check USB connection.")
        return Image.open(io.BytesIO(res.stdout))

    def get_foreground_focus(self) -> Tuple[str, str]:
        """Extracts current foreground (package, activity)."""
        try:
            # 1. Try dumpsys activity activities
            out = self._run_adb_text("shell", "dumpsys", "activity", "activities")
            match = re.search(
                r"(?:mResumedActivity|topResumedActivity):\s+ActivityRecord\{[^\s]+\s+[^\s]+\s+([^/\s]+)/([^/\s\}]+)",
                out,
            )
            if match:
                return match.group(1), match.group(2)

            # 2. Fallback to dumpsys window
            w_out = self._run_adb_text("shell", "dumpsys", "window")
            w_match = re.search(r"(?:mCurrentFocus|mFocusedApp)=.*?([^/\s]+)/([^/\s\}]+)", w_out)
            if w_match:
                return w_match.group(1), w_match.group(2)
        except Exception:
            pass
        return "unknown", "unknown"

    def is_keyboard_visible(self) -> bool:
        """Detects if software keyboard is active on screen."""
        try:
            out = self._run_adb_text("shell", "dumpsys", "input_method")
            return "mInputShown=true" in out
        except Exception:
            return False

    def get_visible_texts(self) -> List[str]:
        """Extracts text and content-desc from UIAutomator dump."""
        try:
            # uiautomator dump can occasionally hang — always enforce a timeout
            self._run_adb("shell", "uiautomator", "dump", "/data/local/tmp/uidump.xml")
            xml_data = self._run_adb_text("shell", "cat", "/data/local/tmp/uidump.xml")
            if not xml_data or "<hierarchy" not in xml_data:
                return []
            texts = re.findall(r'(?:text|content-desc)="([^"]+)"', xml_data)
            seen = set()
            result = []
            for t in texts:
                t_clean = t.strip()
                if t_clean and t_clean not in seen:
                    seen.add(t_clean)
                    result.append(t_clean)
            return result
        except (subprocess.TimeoutExpired, Exception):
            # If uiautomator hangs or fails, return empty list — don't crash
            return []

    def capture_observation(self, intent: NavigationIntent) -> ScreenObservation:
        """Collects multi-modal observation and classifies the screen."""
        img = self.capture_screenshot()
        v_hash = compute_visual_hash(img)
        pkg, act = self.get_foreground_focus()
        kb_shown = self.is_keyboard_visible()
        texts = self.get_visible_texts()

        screen_type, is_forbidden, conf = ScreenClassifier.classify(
            package=pkg,
            activity=act,
            visible_texts=texts,
            keyboard_visible=kb_shown,
            intent=intent,
        )

        return ScreenObservation(
            timestamp=time.time(),
            image=img,
            foreground_package=pkg,
            foreground_activity=act,
            keyboard_visible=kb_shown,
            visible_texts=texts,
            screen_type=screen_type,
            visual_hash=v_hash,
            is_forbidden_section=is_forbidden,
            confidence=conf,
        )

    def tap(self, norm_y: int, norm_x: int) -> None:
        """Tap at normalized [y, x] coordinate (0-1000)."""
        x = int(norm_x * self.width / 1000)
        y = int(norm_y * self.height / 1000)
        self._run_adb("shell", "input", "tap", str(x), str(y))

    def swipe(self, direction: str) -> None:
        """Perform directional swipe/scroll."""
        mid_x = self.width // 2
        mid_y = self.height // 2

        if direction == "up":  # Scroll down (content moves up)
            start_y = int(self.height * 0.75)
            end_y = int(self.height * 0.25)
            self._run_adb("shell", "input", "swipe", str(mid_x), str(start_y), str(mid_x), str(end_y), "500")
        elif direction == "down":  # Scroll up (content moves down)
            start_y = int(self.height * 0.25)
            end_y = int(self.height * 0.75)
            self._run_adb("shell", "input", "swipe", str(mid_x), str(start_y), str(mid_x), str(end_y), "500")
        elif direction == "left":
            start_x = int(self.width * 0.8)
            end_x = int(self.width * 0.2)
            self._run_adb("shell", "input", "swipe", str(start_x), str(mid_y), str(end_x), str(mid_y), "500")
        elif direction == "right":
            start_x = int(self.width * 0.2)
            end_x = int(self.width * 0.8)
            self._run_adb("shell", "input", "swipe", str(start_x), str(mid_y), str(end_x), str(mid_y), "500")

    def type_text(self, text: str, press_enter: bool = False) -> None:
        """Type text into the currently active element.

        Clears any pre-existing field content first, then types.
        For search submission, sends keyevent 84 (KEYCODE_SEARCH) which
        correctly triggers Flipkart/Amazon/Swiggy search bars, with a
        fallback to keyevent 66 (ENTER) if the keyboard stays visible.
        """
        # Clear existing field content: select-all then delete
        self._run_adb("shell", "input", "keyevent", "KEYCODE_CTRL_A")
        time.sleep(0.15)
        self._run_adb("shell", "input", "keyevent", "KEYCODE_DEL")
        time.sleep(0.15)

        escaped = (
            text.replace(" ", "%s")
            .replace("&", r"\&")
            .replace("<", r"\<")
            .replace(">", r"\>")
            .replace('"', r'\"')
            .replace("'", r"\'")
            .replace("(", r"\(")
            .replace(")", r"\)")
        )
        self._run_adb("shell", "input", "text", escaped)

        if press_enter:
            time.sleep(0.4)
            # keyevent 84 = KEYCODE_SEARCH — triggers search bars in shopping apps
            self._run_adb("shell", "input", "keyevent", "84")
            time.sleep(0.5)
            # If keyboard still visible, also send ENTER as safety fallback
            kb_check = self._run_adb_text("shell", "dumpsys", "input_method")
            if "mInputShown=true" in kb_check:
                self._run_adb("shell", "input", "keyevent", "66")

    def press_key(self, key: str) -> None:
        """Press Android hardware/system navigation keys."""
        key_map = {
            "back": "4",
            "home": "3",
            "enter": "66",
            "search": "84",
            "app_switch": "187",
            "del": "67",
        }
        code = key_map.get(key.lower(), "4")
        self._run_adb("shell", "input", "keyevent", code)

    def launch_app(self, app_identifier: str) -> bool:
        """Launch app by package name or common keyword."""
        target_pkg = COMMON_APP_PACKAGES.get(app_identifier.lower().strip(), app_identifier)
        res = self._run_adb_text("shell", "monkey", "-p", target_pkg, "-c", "android.intent.category.LAUNCHER", "1")
        if "No activities found" in res or "monkey aborted" in res:
            out = self._run_adb_text("shell", "pm", "list", "packages", app_identifier)
            packages = [p.replace("package:", "").strip() for p in out.splitlines() if p.startswith("package:")]
            if packages:
                self._run_adb("shell", "monkey", "-p", packages[0], "-c", "android.intent.category.LAUNCHER", "1")
                return True
            return False
        return True

    def launch_upi_intent(self, upi_uri: str, preferred_package: Optional[str] = None) -> bool:
        """Launches standard Android UPI Intent (ACTION_VIEW with upi://pay URI)."""
        pkg = COMMON_APP_PACKAGES.get(preferred_package.lower().strip(), preferred_package) if preferred_package else None
        cmd = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", upi_uri]
        if pkg:
            cmd.extend(["-p", pkg])
        res = self._run_adb_text(*cmd)
        if "Error" in res or "not found" in res:
            if pkg:
                fallback_res = self._run_adb_text("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", upi_uri)
                return "Error" not in fallback_res
            return False
        return True


class MobileAgent:
    """State-Aware Vision Agent with Observe-Plan-Act-Verify & Autonomous Recovery."""

    def __init__(self, device: AndroidDevice):
        self.device = device
        self.llm = LLMService()
        self.loop_detector = LoopDetector(max_identical_actions=2, max_no_progress_steps=3)
        self.recovery = RecoveryController(self.llm)

    async def run_task(self, task: str, max_steps: int = 25) -> str:
        intent = NavigationIntent.from_task(task)
        state = TaskState(goal=task, intent=intent, max_task_steps=max_steps)

        print("\n" + "=" * 65)
        print(f"  [Task Started] '{task}'")
        print(f"  App: {intent.application} | Target: {intent.target_section}")
        print(f"  Forbidden Sections: {intent.forbidden_sections or 'None'}")
        print(f"  Cart Actions Allowed: {intent.allow_cart_actions}")
        print("=" * 65 + "\n")

        task_started_at = datetime.now(timezone.utc)
        step = 0

        while state.status == "running" and state.remaining_task_steps() > 0:
            step += 1
            print(f"\n>>> Step {step}/{max_steps} (Remaining Task Steps: {state.remaining_task_steps()}, Recovery Budget: {state.remaining_recovery_budget()})")

            # ---------------------------------------------------------
            # 1. OBSERVE: Capture structured multi-modal screen state
            # ---------------------------------------------------------
            current_obs = self.device.capture_observation(state.intent)
            previous_obs = state.current_observation
            state.record_observation(current_obs)

            print(f"[Observation] Screen: {current_obs.screen_type} (Forbidden: {current_obs.is_forbidden_section})")
            print(f"              Activity: {current_obs.foreground_activity}")
            print(f"              Keyboard: {current_obs.keyboard_visible} | Visible texts: {len(current_obs.visible_texts)} items")

            # ---------------------------------------------------------
            # 1.5 SECURITY SHIELD: Never interact inside banking apps
            # ---------------------------------------------------------
            banking_pkgs = (
                "com.google.android.apps.nbu.paisa.user",
                "com.google.nbu.paisa",
                "com.phonepe.app",
                "net.one97.paytm",
                "in.org.npci.upiapp",
            )
            if any(bp in current_obs.foreground_package.lower() for bp in banking_pkgs):
                print(f"\n[SECURITY SHIELD] Phone is on banking/payment app ({current_obs.foreground_package}).")
                print("[SECURITY SHIELD] Automated interaction inside banking apps is strictly PROHIBITED.")
                print(f"Automatically switching back to target application '{state.intent.application}'...")
                self.device.launch_app(state.intent.application)
                time.sleep(2.5)
                continue

            # ---------------------------------------------------------
            # 2. VERIFY: Compare with previous screen & Detect Loops
            # ---------------------------------------------------------
            if state.action_history and previous_obs:
                last_action = state.action_history[-1]
                v_dist = visual_hash_distance(current_obs.visual_hash, previous_obs.visual_hash)
                act_changed = current_obs.foreground_activity != previous_obs.foreground_activity
                type_changed = current_obs.screen_type != previous_obs.screen_type
                progress_made = v_dist > 12 or act_changed or type_changed

                last_action.made_progress = progress_made
                last_action.observed_outcome = f"Screen: {current_obs.screen_type}, VisualDiff: {v_dist}"

                if not progress_made and last_action.action != "wait":
                    state.consecutive_no_progress += 1
                    print(f"[Verification] No measurable screen change detected (Consecutive No-Progress: {state.consecutive_no_progress})")
                else:
                    state.consecutive_no_progress = 0
                    print(f"[Verification] State transition verified (VisualDiff: {v_dist})")

            # Run intelligent loop detector
            loop_result = self.loop_detector.check(
                current_obs=current_obs,
                previous_obs=previous_obs,
                action_history=state.action_history,
                screen_fingerprints=state.screen_fingerprints,
                consecutive_no_progress=state.consecutive_no_progress,
            )

            # ---------------------------------------------------------
            # RECOVERY CONTROLLER: Intercept if Loop/Forbidden State
            # ---------------------------------------------------------
            if loop_result and loop_result.is_loop:
                print(f"\n[LOOP WARNING] Type: {loop_result.loop_type}")
                print(f"               Details: {loop_result.description}")

                if state.remaining_recovery_budget() <= 0:
                    state.status = "failed"
                    state.summary = f"Aborted: Recovery budget exhausted while attempting to resolve {loop_result.loop_type}."
                    print(f"\n[RECOVERY ABORT] {state.summary}\n")
                    return state.summary

                print(f"[RECOVERY MODE] Invoking Autonomous Recovery Controller (Budget left: {state.remaining_recovery_budget()})...")
                state.recovery_attempts += 1

                rec_decision = self.recovery.plan_recovery(state, loop_result)
                if not rec_decision:
                    state.status = "failed"
                    state.summary = "Recovery failed: Unable to generate alternative navigation strategy."
                    return state.summary

                if rec_decision.get("should_terminate"):
                    state.status = "failed"
                    state.summary = rec_decision.get("summary", "Recovery terminated safely.")
                    print(f"\n[RECOVERY TERMINATION] {state.summary}\n")
                    return state.summary

                # Execute recovery action
                strat = rec_decision.get("selected_recovery_strategy", "recovery_action")
                state.failed_strategies.append(strat)
                print(f"[Executing Recovery Strategy: '{strat}'] Action: {rec_decision.get('action')}")
                self._execute_action(rec_decision, state, is_recovery=True)
                time.sleep(1.5)
                continue  # Loop back to OBSERVE resulting state immediately

            # ---------------------------------------------------------
            # PRE-LLM FORBIDDEN SECTION HARD ESCAPE
            # When is_forbidden_section is True and no loop was caught yet
            # (e.g., first time entering Minutes), escape deterministically
            # WITHOUT calling the expensive LLM first.
            # ---------------------------------------------------------
            if current_obs.is_forbidden_section or "MINUTES" in current_obs.screen_type:
                print(f"\n[FORBIDDEN ESCAPE] Detected forbidden screen: {current_obs.screen_type}")
                print("[FORBIDDEN ESCAPE] Applying deterministic escape — skipping LLM call to save tokens.")
                from loop_detector import LoopDetectionResult as _LDR
                synthetic_trigger = _LDR(
                    is_loop=True,
                    loop_type="FORBIDDEN_SECTION",
                    description=f"Pre-LLM forbidden escape: {current_obs.screen_type}",
                    recommended_recovery_category="SWITCH_STORE_MODE",
                )
                state.recovery_attempts += 1
                rec_decision = self.recovery._deterministic_fallback(state, synthetic_trigger)
                if rec_decision.get("should_terminate"):
                    state.status = "failed"
                    state.summary = rec_decision.get("summary", "Terminated: could not escape forbidden section.")
                    return state.summary
                strat = rec_decision.get("selected_recovery_strategy", "forbidden_escape")
                print(f"[Forbidden Escape Strategy: '{strat}'] Action: {rec_decision.get('action')}")
                self._execute_action(rec_decision, state, is_recovery=True)
                time.sleep(1.5)
                continue

            # ---------------------------------------------------------
            # 3. PLAN: Main Task Planning
            # ---------------------------------------------------------
            display_img = current_obs.image.copy()
            display_img.thumbnail((720, 1600))

            prompt = f"""Task Goal: {state.goal}
Step: {step}/{max_steps}
Target Section: {state.intent.target_section}
Forbidden Sections: {state.intent.forbidden_sections}
Cart Actions Allowed: {state.intent.allow_cart_actions}

Current Observation:
- Screen Classification: {current_obs.screen_type}
- Foreground Activity: {current_obs.foreground_activity}
- Keyboard Visible: {current_obs.keyboard_visible}
- Visible UI Texts: {current_obs.visible_texts[:20]}

Recent Actions History:
{json.dumps([{"action": a.action, "params": a.params, "progress": a.made_progress} for a in state.action_history[-3:]], indent=2) if state.action_history else "None (first step)"}

Analyze screen and output the single best next action strictly matching the schema."""

            decision = self.llm.generate_action(
                contents=[display_img, prompt],
                system_instruction=MAIN_SYSTEM_INSTRUCTION,
                temperature=0.2,
            )

            if not decision:
                print("[Planner Error] LLM returned no action. Triggering safe wait...")
                decision = {"thought": "Waiting for screen stability after transient LLM failure.", "action": "wait"}

            # ---------------------------------------------------------
            # TASK BOUNDARY & PERMISSION GUARD
            # ---------------------------------------------------------
            # Guard 0 [ANTI-HALLUCINATION]: Trust the classifier over the LLM.
            # The LLM sometimes reads delivery text like "8 mins" or "Get in 10 min"
            # inside regular product cards and falsely believes it is in Flipkart Minutes.
            # If the classifier has confirmed REGULAR_SEARCH_RESULTS (Forbidden=False),
            # NEVER allow the LLM to press Back or relaunch — that undoes real progress.
            if (
                current_obs.screen_type == "REGULAR_SEARCH_RESULTS"
                and not current_obs.is_forbidden_section
                and decision.get("action") in ("key", "launch")
                and decision.get("key") == "back"
            ):
                # Check if LLM thought it was in Minutes
                thought_lower = decision.get("thought", "").lower()
                if any(kw in thought_lower for kw in ("minutes", "8 min", "10 min", "15 min", "wrong mode", "exit", "forbidden")):
                    print(
                        "[Anti-Hallucination Guard] Classifier confirmed REGULAR_SEARCH_RESULTS "
                        f"(Forbidden=False) but LLM tried to press Back thinking it was in Minutes. "
                        "Overriding to 'wait' and trusting classifier."
                    )
                    decision = {
                        "thought": "Classifier confirms regular store. Waiting 1s for full results to load.",
                        "action": "wait",
                        "expected_postcondition": "Results fully loaded in regular marketplace.",
                    }

            # Guard 1: Premature completion check
            if decision.get("action") == "done":
                # Verify that observable evidence supports success
                if state.intent.objective == "search_products" and current_obs.screen_type not in ("REGULAR_SEARCH_RESULTS", "PRODUCT_DETAILS"):
                    print("[Guard Warning] Agent claimed 'done' but screen is not showing regular search results. Overriding.")
                    decision = {"thought": "Must navigate to regular marketplace results before claiming done.", "action": "wait"}
                elif current_obs.is_forbidden_section:
                    print("[Guard Warning] Cannot complete task while in forbidden section. Overriding to recovery.")
                    decision = {"thought": "Currently in forbidden section. Must exit first.", "action": "key", "key": "back"}

            # Guard 2: "Proceed to Buy" from Cart = buying ALL cart items
            # This guard fires when Cart Actions are allowed but the agent tries to
            # checkout via the cart page (which buys ALL items, not just the one requested).
            # The correct flow for single-item purchase is: Product Page → "Buy Now".
            if state.intent.allow_cart_actions and current_obs.screen_type == "CART":
                thought_lower = decision.get("thought", "").lower()
                action_lower = decision.get("action", "")
                # If the agent is about to tap 'Proceed to Buy' / 'Place Order' on the cart
                # AND the task did not explicitly say "checkout cart" or "all items"
                goal_lower = state.goal.lower()
                cart_explicit = any(kw in goal_lower for kw in (
                    "my cart", "all items", "everything in cart", "checkout cart", "the cart"
                ))
                if not cart_explicit and action_lower == "tap":
                    thought_has_proceed = any(
                        kw in thought_lower
                        for kw in ("proceed to buy", "place order", "proceed", "checkout all")
                    )
                    if thought_has_proceed:
                        print(
                            "[Cart Guard] Agent tried to 'Proceed to Buy' from Cart page — "
                            "this would buy ALL cart items. Redirecting to product page 'Buy Now'."
                        )
                        decision = {
                            "thought": "Cart checkout would buy all items. Pressing back to return to product page and use Buy Now instead.",
                            "action": "key",
                            "key": "back",
                            "expected_postcondition": "Returns to product detail page where Buy Now is available.",
                        }

            # Guard 3: Unauthorized Cart Additions
            if not state.intent.allow_cart_actions:
                text_target = str(decision.get("text", "")).lower()
                thought_text = str(decision.get("thought", "")).lower()
                if any(kw in thought_text or kw in text_target for kw in ("add to cart", "buy now", "place order")):
                    print("[Boundary Enforcement] User did not authorize cart additions or purchases. Overriding action.")
                    decision = {"thought": "Displaying products only; cart addition not authorized.", "action": "done", "summary": "Identified relevant regular marketplace products."}

            # ---------------------------------------------------------
            # 4. ACT: Execute Selected Action
            # ---------------------------------------------------------
            action_result = self._execute_action(decision, state, is_recovery=False)
            if action_result is not None:
                return action_result

            time.sleep(1.2)

        if state.status == "running":
            state.status = "failed"
            state.summary = f"Stopped: Reached maximum execution step budget ({max_steps} steps)."

        return state.summary

    def _execute_action(self, decision: Dict[str, Any], state: TaskState, is_recovery: bool = False) -> Optional[str]:
        thought = decision.get("thought", "")
        action = decision.get("action", "")
        expected = decision.get("expected_postcondition", "")

        print(f"[{'RECOVERY' if is_recovery else 'PLANNER'}] Action: {action} -> {json.dumps({k: v for k, v in decision.items() if k not in ('thought', 'action')})}")
        print(f"            Reasoning: {thought}")

        params = {k: v for k, v in decision.items() if k not in ("thought", "action", "expected_postcondition")}
        record = ActionRecord(
            step=len(state.action_history) + 1,
            is_recovery=is_recovery,
            thought=thought,
            action=action,
            params=params,
            expected_postcondition=expected,
        )
        state.record_action(record)

        if action == "done":
            summary = decision.get("summary", "Task completed.")
            state.status = "completed"
            state.summary = summary
            print(f"\n[Task Completed Successfully] {summary}\n")
            return summary

        elif action == "launch":
            app = decision.get("app", "")
            self.device.launch_app(app)

        elif action == "tap":
            point = decision.get("point", [500, 500])
            if isinstance(point, list) and len(point) == 2:
                self.device.tap(point[0], point[1])

        elif action == "type":
            text = decision.get("text", "")
            press_enter = decision.get("press_enter", True)
            self.device.type_text(text, press_enter=press_enter)

        elif action == "swipe":
            direction = decision.get("direction", "up")
            self.device.swipe(direction)

        elif action == "key":
            key = decision.get("key", "back")
            self.device.press_key(key)

        elif action == "wait":
            time.sleep(2.0)

        elif action == "otp":
            print("Fetching OTP from SMS and Gmail...")
            code = None
            task_started = datetime.now(timezone.utc)
            for _ in range(15):
                if find_sms_otp:
                    code = find_sms_otp(None, task_started)
                if not code and fetch_gmail_otp:
                    code = fetch_gmail_otp(None, task_started)
                if code:
                    break
                time.sleep(3)
            if code:
                print(f"Auto-fetched OTP: {code}. Typing into screen...")
                self.device.type_text(str(code), press_enter=True)
            else:
                print("Could not find OTP automatically. Please enter it manually.")

        elif action == "initiate_payment":
            return self._handle_payment(decision, state)

        return None

    def _handle_payment(self, decision: Dict[str, Any], state: TaskState) -> Optional[str]:
        amount = float(decision.get("amount", 0.0))
        currency = decision.get("currency", "INR")
        payee = decision.get("payee_name", "Merchant")
        scenario = decision.get("scenario", "GATEWAY_ORDER")
        app_pref = decision.get("app", None)   # None for native checkout merchants
        merchant_key = state.intent.application.lower()

        # Native checkout merchants handle payment entirely within their own app.
        # We must NEVER generate or show a familyos.pay@icici UPI URI for these —
        # it would appear in the user's payment app (GPay/PhonePe) as the payee.
        NATIVE_CHECKOUT_MERCHANTS = frozenset(("flipkart", "amazon", "swiggy", "zomato", "myntra", "meesho"))
        is_native_checkout = merchant_key in NATIVE_CHECKOUT_MERCHANTS

        print("\n" + "=" * 65)
        print("  [SECURITY SHIELD] Payment Requirement Detected")
        print(f"  Target: {payee} | Amount: \u20b9{amount:.2f} {currency}")
        print(f"  Mode: {'Native App Checkout' if is_native_checkout else 'UPI Intent'}")
        print("  UI Automation & Screen Capturing are strictly SUSPENDED.")
        print("=" * 65)

        # ── Pre-payment order fingerprint (captures existing order IDs) ──────
        order_fingerprint = None
        try:
            order_fingerprint = OrderVerifier.pre_payment_snapshot(merchant_key)
        except Exception as e:
            print(f"[OrderVerifier] Pre-snapshot failed (non-critical): {e}")

        # ── Payment record ──────────────────────────────────────────────
        if is_native_checkout:
            # For native checkout: create a LOCAL-ONLY tracking record.
            # Do NOT generate a familyos.pay@icici UPI URI — it would appear
            # in the user's payment app if launched accidentally.
            payment_id = f"native_{merchant_key}_{int(time.time())}"
            print(f"\n[Native Checkout] {payee} processes payment directly in their app.")
            print("  Please select your payment method on screen (Google Pay / PhonePe / COD / Net Banking).")
            print("  The agent will NOT intervene in the payment process.")
        else:
            # For non-native apps: generate UPI intent and launch it
            order = payment_service.create_payment_order(
                task_id=f"task_{int(time.time())}",
                order_id=f"ord_{int(time.time()*1000)}",
                amount=amount,
                currency=currency,
                payee_name=payee,
                scenario=scenario,
            )
            payment_id = order["payment_id"]
            print(f"\nLaunching payment app via UPI Intent:\n  {order['upi_intent_uri']}")
            self.device.launch_upi_intent(order["upi_intent_uri"], preferred_package=app_pref)
            payment_service.mark_pending(payment_id)

        handover_at = datetime.now(timezone.utc)

        print("\n" + "-" * 65)
        print("  HANDOVER TO USER: Authorize securely in Google Pay / PhonePe on your phone.")
        print("-" * 65)
        print("\nSelect the outcome once finished on your phone:")
        print("  1) Payment Authorized & Completed (Verify via Order Confirmation)")
        print("  2) Payment Cancelled / Declined")
        print("  3) [Developer/Test Mode] Simulate Successful Gateway Webhook")

        try:
            choice = input("Payment Handover Choice [1/2/3]> ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "2"

        if choice == "3":
            # ── Simulate a gateway webhook (only for non-native / test mode) ──
            if not is_native_checkout and payment_id in payment_service.records:
                payment_service.process_gateway_webhook(
                    payment_id=payment_id,
                    event_name="payment.captured",
                    status="SUCCESS",
                    gateway_payment_id=f"pay_sim_{int(time.time())}",
                    utr=f"UTR{int(time.time()*1000)}",
                )
                rec = payment_service.records.get(payment_id)
                print(f"\n[Verified] Gateway verified SUCCESS! Ref: {rec.transaction_reference if rec else 'N/A'}")
            else:
                print(f"\n[Verified] Native checkout simulated as SUCCESS (no gateway record needed).")
            print(f"Switching back to '{state.intent.application}' to verify order completion...")
            self.device.launch_app(state.intent.application)
            time.sleep(2.5)

        elif choice == "2":
            # ── User cancelled ──────────────────────────────────────────
            if not is_native_checkout and payment_id in payment_service.records:
                payment_service.records[payment_id].payment_status = "CANCELLED"
                payment_service._save_records()
            state.status = "cancelled"
            print("\n[Payment Cancelled] User aborted payment authorization.")
            print("Safely rolling back: dismissing payment screens and returning to phone Home screen...")
            self.device.press_key("back")
            time.sleep(1.0)
            self.device.press_key("home")
            time.sleep(0.5)
            state.summary = (
                f"Task safely cancelled: Payment of \u20b9{amount:.2f} was declined by the user. "
                "Dismissed payment screen and cleanly returned device to Home screen."
            )
            print(f"\n[Safe Rollback Complete] {state.summary}\n")
            return state.summary

        else:
            # ── User claims payment authorized ──────────────────────────
            if scenario == "DIRECT_TRANSFER":
                utr = input("Optional: Enter transaction reference / UTR: ").strip()
                payment_service.confirm_direct_transfer(payment_id, utr_hint=utr or None)
            else:
                if not is_native_checkout:
                    verified = payment_service.verify_payment_status(payment_id, timeout_seconds=10)
                    if verified.get("payment_status") != "SUCCESS":
                        return f"Task stopped: Payment not verified ({verified.get('payment_status')})."

            # Bring target app back to foreground
            print(f"Switching back to '{state.intent.application}' to verify order completion...")
            self.device.launch_app(state.intent.application)
            time.sleep(2.5)

            # ── STEP 2: Post-payment order confirmation verification ─────
            # This is the authoritative check: did a new confirmation email
            # or SMS appear after the handover that wasn't there before?
            if order_fingerprint is not None:
                print("\n[OrderVerifier] Checking for new order confirmation in Gmail / SMS...")
                try:
                    verify_result = OrderVerifier.post_payment_verify(
                        fingerprint=order_fingerprint,
                        expected_amount=amount,
                    )
                    self._report_order_verification(verify_result, payment_id, amount)
                except Exception as e:
                    print(f"[OrderVerifier] Verification error (non-critical): {e}")
            else:
                # Fallback: quick one-shot check with no baseline
                try:
                    verify_result = OrderVerifier.quick_check(
                        merchant=merchant_key,
                        since=handover_at,
                        expected_amount=amount,
                    )
                    self._report_order_verification(verify_result, payment_id, amount)
                except Exception as e:
                    print(f"[OrderVerifier] Quick-check error (non-critical): {e}")

        return None

    def _report_order_verification(
        self,
        result: VerificationResult,
        payment_id: str,
        amount: float,
    ) -> None:
        """Print a human-readable order verification summary."""
        icon = "\u2713" if result.verified else "\u26a0"
        print(f"\n  [{icon}] Order Verification: {result.confidence}")
        print(f"       Method:  {result.method}")
        print(f"       Details: {result.details}")
        if result.new_evidence:
            for ev in result.new_evidence[:2]:  # Show at most 2 pieces of evidence
                print(f"       Evidence [{ev.channel}]: Order ID={ev.order_id}, Amount=\u20b9{ev.amount}")
        if result.verified and result.confidence in ("HIGH", "MEDIUM"):
            # Update payment record with order confirmation reference
            rec = payment_service.records.get(payment_id)
            if rec and result.new_evidence:
                ev = result.new_evidence[0]
                if ev.order_id and not rec.transaction_reference:
                    rec.transaction_reference = f"ORD:{ev.order_id}"
                    payment_service._save_records()
                    print(f"       Payment record updated with merchant order ref: {rec.transaction_reference}")
        elif not result.verified:
            print(
                "\n  [OrderVerifier] Order confirmation not yet received. "
                "Check your email / SMS for confirmation. "
                f"Task continues; payment of \u20b9{amount:.2f} was user-authorized."
            )


def main():
    print("=" * 65)
    print("  State-Aware Mobile Agent (Powered by Gemini Vision)")
    print("  Observe-Plan-Act-Verify | Loop Detection | Autonomous Recovery")
    print("=" * 65)
    print("Ensure your phone is connected with USB Debugging enabled.")

    try:
        device = AndroidDevice()
    except Exception as e:
        print(f"\n[Error] {e}")
        sys.exit(1)

    agent = MobileAgent(device)

    print("\nType your task in plain English:")
    print('  "Open Flipkart and search for die cast cars in normal store, not minutes"')
    print('  "Open Swiggy and find top rated pizza places"')
    print("Type 'exit' or 'quit' to end session.\n")

    while True:
        try:
            task = input("Phone-Task> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not task:
            continue
        if task.lower() in ("exit", "quit"):
            print("Session ended.")
            break

        asyncio.run(agent.run_task(task))


if __name__ == "__main__":
    main()

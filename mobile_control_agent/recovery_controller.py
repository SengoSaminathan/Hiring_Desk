"""Autonomous Recovery Controller for Android Mobile Agent.

Implements dedicated recovery planning when actions fail, navigation loops
occur, or forbidden application sections are entered.
"""

import json
from typing import Any, Dict, List, Optional
from PIL import Image

from models_and_state import TaskState, ScreenObservation, ActionRecord
from loop_detector import LoopDetectionResult
from llm_service import LLMService

RECOVERY_SYSTEM_PROMPT = """You are the recovery controller for an Android automation agent.

Your job is to recover from unexpected screens, failed actions, navigation loops, and ambiguous application states.
The user's original objective remains the source of truth.

Always inspect the latest available screen evidence before selecting an action. Review recent actions and their observed outcomes.

Never repeat an action sequence that has already failed under materially identical conditions without identifying new evidence that justifies trying it again.

If the current screen is unchanged, determine whether the previous action failed, the application is loading, or the screen transition was delayed.

If a recovery action does not produce the expected state transition, update your hypothesis and select a meaningfully different strategy.

Respect the user's intended application section. Do not silently switch to a different marketplace, application mode, or service.

FLIPKART MINUTES vs REGULAR STORE — critical rules:
  - If you are inside Flipkart Minutes (screen_type contains MINUTES), you must EXIT immediately.
  - Preferred exit sequence (in order):
      1. Press the "Shop" or "Home" tab in the bottom navigation bar (tap bottom-left area).
      2. If no tab switch is available, press BACK once.
      3. If back returns to Minutes, KILL and RELAUNCH the Flipkart app via monkey.
      4. On relaunch, IMMEDIATELY type the search query directly into the search bar and press Enter.
         Do NOT tap autocomplete suggestions — they may redirect back to Minutes.
  - NEVER call "search" or "type" while still inside the Minutes interface.
  - NEVER re-enter minutes by tapping any suggestion labelled "in Minutes" or "Deliver in 10 mins".

Do not perform additional purchases, cart modifications, payments, or other consequential actions unless authorized by the original user request.

Choose one safe, verifiable action at a time. Specify the expected result and a fallback.

If available evidence is insufficient, request another observation rather than guessing.

If recovery becomes unsafe, impossible, or unproductive, stop and return an accurate failure report.

Never claim that an action succeeded without verifying the resulting state.

Coordinate System:
- All coordinates are normalized [y, x] integers between 0 and 1000.

Output Schema (STRICT JSON):
{
  "state_assessment": "Explanation of where the agent currently is",
  "failure_hypothesis": "Why the previous action or navigation failed",
  "selected_recovery_strategy": "Name of the unique strategy being attempted",
  "thought": "Step-by-step reasoning for the recovery action",
  "action": "tap" | "key" | "type" | "launch" | "wait" | "done",
  "point": [y, x], // if action is tap
  "key": "back" | "home" | "enter", // if action is key
  "app": "package name", // if action is launch
  "text": "text to type", // if action is type
  "press_enter": true, // if action is type and should submit
  "expected_postcondition": "What screen or state must appear after this action",
  "fallback_strategy": "What to do if this recovery action fails",
  "should_terminate": false // true only if recovery is impossible
}
"""


class RecoveryController:
    """Orchestrates recovery planning using vision LLM and deterministic fallbacks."""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def plan_recovery(
        self,
        state: TaskState,
        trigger: LoopDetectionResult,
    ) -> Optional[Dict[str, Any]]:
        """Generates a recovery action when a loop or failure is detected."""
        obs = state.current_observation
        if not obs:
            return None

        # Format recent action failure history
        recent_actions = [
            {
                "step": a.step,
                "action": a.action,
                "params": a.params,
                "outcome": a.observed_outcome,
                "made_progress": a.made_progress,
            }
            for a in state.action_history[-4:]
        ]

        prompt = f"""RECOVERY TRIGGER: {trigger.loop_type}
Details: {trigger.description}
Recommended Focus: {trigger.recommended_recovery_category}

User Goal: {state.goal}
Target Application Section: {state.intent.target_section}
Forbidden Sections: {state.intent.forbidden_sections}

Current Observation:
- Screen Classification: {obs.screen_type}
- Foreground Activity: {obs.foreground_activity}
- Keyboard Visible: {obs.keyboard_visible}
- Visible UI Texts: {obs.visible_texts[:15]}

Previously Failed Strategies:
{json.dumps(state.failed_strategies, indent=2) if state.failed_strategies else "None yet"}

Recent Actions:
{json.dumps(recent_actions, indent=2)}

Generate a recovery plan that selects a MEANINGFULLY DIFFERENT strategy.
DO NOT repeat any strategy in 'Previously Failed Strategies'.
Output ONLY valid JSON."""

        # Resize image for fast inference
        display_img = obs.image.copy()
        display_img.thumbnail((720, 1600))

        decision = self.llm.generate_action(
            contents=[display_img, prompt],
            system_instruction=RECOVERY_SYSTEM_PROMPT,
            temperature=0.3,
        )

        # Check if model gave a valid recovery decision
        if decision:
            strategy_name = decision.get("selected_recovery_strategy", "")
            # Ensure it's not a known failed strategy
            if strategy_name not in state.failed_strategies:
                return decision

        # Deterministic Fallback if model fails or suggests duplicate strategy
        return self._deterministic_fallback(state, trigger)

    def _deterministic_fallback(
        self,
        state: TaskState,
        trigger: LoopDetectionResult,
    ) -> Dict[str, Any]:
        """Guaranteed rule-based recovery ordered from cheapest to most drastic.

        Minutes-specific escape chain (in order, never repeating a strategy):
          1. press_back_from_forbidden   — press Back once
          2. tap_shop_tab                — tap the "Shop" / "Home" bottom nav tab
          3. relaunch_main_app           — kill + relaunch Flipkart via monkey
          4. search_bypass_after_relaunch— immediately type + Enter in search bar
                                          WITHOUT tapping autocomplete suggestions
          5. terminate_safely            — give up cleanly
        """
        obs = state.current_observation
        assert obs is not None
        failed = set(state.failed_strategies)
        search_query = getattr(state.intent, "search_query", "") or ""
        app = state.intent.application or "flipkart"

        # ── Rule 0: Dismiss keyboard first if it's blocking the screen ─────
        if obs.keyboard_visible and "dismiss_keyboard" not in failed:
            state.failed_strategies.append("dismiss_keyboard")
            return {
                "state_assessment": "Keyboard is open and obstructing view.",
                "failure_hypothesis": "Active keyboard prevented direct navigation.",
                "selected_recovery_strategy": "dismiss_keyboard",
                "thought": "Dismissing keyboard by pressing back key once.",
                "action": "key",
                "key": "back",
                "expected_postcondition": "Keyboard hidden and full screen visible.",
                "fallback_strategy": "tap_shop_tab",
                "should_terminate": False,
            }

        is_forbidden_trigger = (
            obs.is_forbidden_section
            or trigger.loop_type == "FORBIDDEN_SECTION"
            or "MINUTES" in obs.screen_type
        )

        # ── Rule 1: Press Back to exit Minutes ─────────────────────────────
        if is_forbidden_trigger and "press_back_from_forbidden" not in failed:
            state.failed_strategies.append("press_back_from_forbidden")
            return {
                "state_assessment": f"Inside forbidden section: {obs.screen_type}.",
                "failure_hypothesis": "Navigation led into Flipkart Minutes instead of regular marketplace.",
                "selected_recovery_strategy": "press_back_from_forbidden",
                "thought": "Pressing Back once to exit Flipkart Minutes interface.",
                "action": "key",
                "key": "back",
                "expected_postcondition": "Exit Minutes and return to regular Flipkart screen.",
                "fallback_strategy": "tap_shop_tab",
                "should_terminate": False,
            }

        # ── Rule 2: Tap the 'Shop' / 'Home' bottom nav tab ─────────────────
        # Flipkart's bottom nav: Home(shop) tab is bottom-left ≈ [975, 100]
        if is_forbidden_trigger and "tap_shop_tab" not in failed:
            state.failed_strategies.append("tap_shop_tab")
            return {
                "state_assessment": "Still in Flipkart Minutes after pressing Back.",
                "failure_hypothesis": "Back returned to Minutes Home. Bottom-nav tab switch needed.",
                "selected_recovery_strategy": "tap_shop_tab",
                "thought": (
                    "Tapping the Shop/Home tab in the Flipkart bottom navigation bar "
                    "to switch from the Minutes section to the regular marketplace."
                ),
                "action": "tap",
                "point": [975, 100],   # bottom-left = Home/Shop tab in Flipkart
                "expected_postcondition": "Regular Flipkart marketplace home screen appears.",
                "fallback_strategy": "relaunch_main_app",
                "should_terminate": False,
            }

        # ── Rule 3: Kill + relaunch the app completely ─────────────────────
        if "relaunch_main_app" not in failed:
            state.failed_strategies.append("relaunch_main_app")
            return {
                "state_assessment": "Back + tab switch both failed; Minutes persists.",
                "failure_hypothesis": "App state is cached in Minutes mode. Full relaunch needed.",
                "selected_recovery_strategy": "relaunch_main_app",
                "thought": "Relaunching main Flipkart app to completely reset navigation state.",
                "action": "launch",
                "app": app,
                "expected_postcondition": "Flipkart main shopping home appears (not Minutes).",
                "fallback_strategy": "search_bypass_after_relaunch",
                "should_terminate": False,
            }

        # ── Rule 4: After relaunch — immediately search without autocomplete ─
        # CRITICAL: Do NOT tap suggestions. Type and press Enter directly.
        # This bypasses the Minutes suggestion that gets injected by Flipkart.
        if search_query and "search_bypass_after_relaunch" not in failed:
            state.failed_strategies.append("search_bypass_after_relaunch")
            return {
                "state_assessment": "App relaunched. Now on Flipkart Home. Must search directly.",
                "failure_hypothesis": (
                    "Tapping autocomplete suggestions previously redirected to Minutes. "
                    "Typing + Enter directly bypasses this."
                ),
                "selected_recovery_strategy": "search_bypass_after_relaunch",
                "thought": (
                    f"Tapping search bar and typing '{search_query}' directly, then pressing Enter. "
                    "Bypassing all autocomplete suggestions to land in the regular marketplace."
                ),
                "action": "type",
                "text": search_query,
                "press_enter": True,
                "expected_postcondition": "Regular Flipkart search results page for the query.",
                "fallback_strategy": "terminate_safely",
                "should_terminate": False,
            }

        # ── Rule 5: General stuck-screen recovery (non-Minutes) ────────────
        if "press_back_to_reset" not in failed:
            state.failed_strategies.append("press_back_to_reset")
            return {
                "state_assessment": "Stuck on unchanged screen (not Minutes-related).",
                "failure_hypothesis": "Action had no effect; screen state is blocked.",
                "selected_recovery_strategy": "press_back_to_reset",
                "thought": "Pressing Back key to navigate to previous known state.",
                "action": "key",
                "key": "back",
                "expected_postcondition": "Previous screen loads.",
                "fallback_strategy": "terminate_safely",
                "should_terminate": False,
            }

        # ── Final: Terminate safely ────────────────────────────────────────
        return {
            "state_assessment": "All viable recovery options exhausted.",
            "failure_hypothesis": "Navigation path blocked or target application state unreachable.",
            "selected_recovery_strategy": "terminate_safely",
            "thought": "Stopping execution to prevent further token waste.",
            "action": "done",
            "summary": (
                "Recovery exhausted after trying: back, shop-tab, relaunch, direct-search. "
                "Unable to reach regular Flipkart marketplace without repeating failed strategies."
            ),
            "expected_postcondition": "Session terminates safely.",
            "fallback_strategy": "none",
            "should_terminate": True,
        }

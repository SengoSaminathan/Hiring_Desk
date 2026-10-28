"""Intelligent loop detection and progress verification.

Detects:
- Same screen after consecutive actions (unchanged screen).
- Identical actions attempted repeatedly without success.
- Multi-step oscillation loops (e.g., Screen A -> Screen B -> Screen A -> Screen B).
- Consecutive actions without measurable progress.
- Entry into forbidden sections (e.g., Flipkart Minutes).
"""

from dataclasses import dataclass
from typing import List, Optional
from models_and_state import ScreenObservation, ActionRecord, visual_hash_distance


@dataclass
class LoopDetectionResult:
    is_loop: bool
    loop_type: str  # "UNCHANGED_SCREEN", "REPEATED_ACTION", "NAVIGATION_OSCILLATION", "NO_PROGRESS_LIMIT", "FORBIDDEN_SECTION"
    description: str
    recommended_recovery_category: str


class LoopDetector:
    """Monitors task state and history to identify navigation stalls and loops."""

    def __init__(
        self,
        max_identical_actions: int = 2,
        max_no_progress_steps: int = 3,
        visual_similarity_threshold: int = 12,  # Hamming distance <= 12 considered identical
    ):
        self.max_identical_actions = max_identical_actions
        self.max_no_progress_steps = max_no_progress_steps
        self.visual_similarity_threshold = visual_similarity_threshold

    def check(
        self,
        current_obs: ScreenObservation,
        previous_obs: Optional[ScreenObservation],
        action_history: List[ActionRecord],
        screen_fingerprints: List[str],
        consecutive_no_progress: int,
    ) -> Optional[LoopDetectionResult]:
        """Evaluates whether the agent is trapped in a loop or unviable state."""

        # 1. Immediate check: Entered a forbidden section (e.g. Flipkart Minutes)
        if current_obs.is_forbidden_section:
            return LoopDetectionResult(
                is_loop=True,
                loop_type="FORBIDDEN_SECTION",
                description=f"Agent navigated into forbidden section: {current_obs.screen_type}.",
                recommended_recovery_category="SWITCH_STORE_MODE",
            )

        if not action_history or not previous_obs:
            return None

        last_action = action_history[-1]

        # 2. Check for Repeated Identical Actions
        if len(action_history) >= self.max_identical_actions:
            recent_actions = action_history[-self.max_identical_actions:]
            sigs = [a.signature() for a in recent_actions]
            if len(set(sigs)) == 1 and not any(a.made_progress for a in recent_actions):
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type="REPEATED_ACTION",
                    description=f"Action '{last_action.action}' repeated {self.max_identical_actions} times without progress.",
                    recommended_recovery_category="ALTERNATIVE_ACTION",
                )

        # 3. Check for Unchanged Screen (different actions executed, but screen is visually and textually identical)
        dist = visual_hash_distance(current_obs.visual_hash, previous_obs.visual_hash)
        same_activity = current_obs.foreground_activity == previous_obs.foreground_activity
        same_type = current_obs.screen_type == previous_obs.screen_type

        # If visual distance is tiny and same activity, screen did not meaningfully change
        if dist <= self.visual_similarity_threshold and same_activity and same_type:
            # If the action was 'wait', waiting without change is acceptable up to 1-2 times
            if last_action.action != "wait":
                # Check how many recent actions produced unchanged screen
                unchanged_count = 1
                for act in reversed(action_history[:-1]):
                    if not act.made_progress:
                        unchanged_count += 1
                    else:
                        break

                if unchanged_count >= 2:
                    return LoopDetectionResult(
                        is_loop=True,
                        loop_type="UNCHANGED_SCREEN",
                        description=f"Screen remained unchanged after {unchanged_count} actions (last: {last_action.action}).",
                        recommended_recovery_category="DISMISS_KEYBOARD_OR_RELAUNCH",
                    )

        # 4. Check for Oscillation Cycle (e.g., A -> B -> A -> B)
        # Look at the last 4 to 6 screen classifications and activities
        if len(screen_fingerprints) >= 4:
            # Length 2 cycle: [-1] == [-3] and [-2] == [-4]
            fp = screen_fingerprints
            if fp[-1] == fp[-3] and fp[-2] == fp[-4] and fp[-1] != fp[-2]:
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type="NAVIGATION_OSCILLATION",
                    description="Detected 2-state oscillation cycle between screens (A -> B -> A -> B).",
                    recommended_recovery_category="BREAK_CYCLE_RETURN_HOME",
                )

        if len(screen_fingerprints) >= 6:
            # Length 3 cycle: [-1] == [-4] and [-2] == [-5] and [-3] == [-6]
            if fp[-1] == fp[-4] and fp[-2] == fp[-5] and fp[-3] == fp[-6]:
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type="NAVIGATION_OSCILLATION",
                    description="Detected 3-state oscillation cycle across screens.",
                    recommended_recovery_category="BREAK_CYCLE_RETURN_HOME",
                )

        # 5. Check consecutive no-progress limit
        if consecutive_no_progress >= self.max_no_progress_steps:
            return LoopDetectionResult(
                is_loop=True,
                loop_type="NO_PROGRESS_LIMIT",
                description=f"Executed {consecutive_no_progress} consecutive actions without measurable progress.",
                recommended_recovery_category="RESET_TO_APP_ROOT",
            )

        return None

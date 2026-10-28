"""Data models and state representations for the Android Mobile Agent.

Defines:
- NavigationIntent: Explicit targets and forbidden sections.
- ScreenObservation: Multi-modal snapshot combining visual, activity, and UI hierarchy.
- ActionRecord: Log of executed action, predicted postcondition, and observed outcome.
- TaskState: Persistent in-memory state tracking steps, budgets, and recovery memory.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import time
from typing import Any, Dict, List, Optional
from PIL import Image


def compute_visual_hash(img: Image.Image) -> str:
    """Computes a 256-bit perceptual average hash of an image."""
    small = img.resize((16, 16), Image.Resampling.BILINEAR).convert("L")
    raw = small.tobytes()
    avg = sum(raw) / len(raw)
    return "".join("1" if b > avg else "0" for b in raw)


def visual_hash_distance(h1: str, h2: str) -> int:
    """Returns Hamming distance between two binary hash strings."""
    if not h1 or not h2 or len(h1) != len(h2):
        return 999
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


@dataclass
class NavigationIntent:
    """Represents the user's high-level goal and boundaries."""
    application: str  # e.g., "flipkart"
    target_section: str  # e.g., "regular_marketplace"
    forbidden_sections: List[str] = field(default_factory=list)  # e.g., ["flipkart_minutes", "grocery"]
    objective: str = "search_products"  # "search_products", "view_details", "cart_checkout"
    query: str = ""
    allow_cart_actions: bool = False  # Strict boundary: do not add to cart unless explicitly asked

    @classmethod
    def from_task(cls, task: str) -> "NavigationIntent":
        """Infers navigation intent and boundaries from a natural language prompt."""
        task_lower = task.lower()

        # Target application
        app = "flipkart" if "flipkart" in task_lower else ("amazon" if "amazon" in task_lower else "generic")

        # Check for forbidden sections (e.g. "not minutes", "not grocery")
        forbidden = []
        if "minutes" in task_lower or "minute" in task_lower:
            if "not" in task_lower or "regular" in task_lower or "normal" in task_lower or "avoid" in task_lower:
                forbidden.append("flipkart_minutes")
        else:
            # Default safeguard: if searching Flipkart products without mentioning minutes, forbid minutes
            if app == "flipkart":
                forbidden.append("flipkart_minutes")

        # Cart boundary check: only allow cart actions if explicitly requested.
        # Handles natural phrasing: "add one toy to the cart", "put in cart", "add a product"
        import re as _re
        _cart_patterns = [
            r"add.{0,15}(?:to|in(?:to)?) (?:the )?(?:cart|basket|bag)",
            r"put.{0,15}(?:in(?:to)?|to) (?:the )?(?:cart|basket|bag)",
            r"(?:buy|purchase) (?:it|one|this|the)",
            r"(?:place |confirm )?(?:the )?order",
            r"(?:proceed to |go to )?checkout",
            r"buy now",
        ]
        allow_cart = any(
            _re.search(p, task_lower) for p in _cart_patterns
        )

        # Objective detection
        if allow_cart:
            objective = "cart_checkout"
        elif any(kw in task_lower for kw in ("search", "find", "look for", "list")):
            objective = "search_products"
        else:
            objective = "general_task"

        # Query extraction heuristic
        query = task
        for prefix in ("open flipkart and search for", "search for", "find me", "look for", "find"):
            if prefix in task_lower:
                idx = task_lower.find(prefix) + len(prefix)
                query = task[idx:].strip()
                # Strip trailing constraint qualifiers
                for suffix in (
                    "and add", "and put", "and buy",  # cart suffix
                    "in the normal", "in normal", "not in", "not flipkart", "avoiding",
                ):
                    s_idx = query.lower().find(suffix)
                    if s_idx != -1:
                        query = query[:s_idx].strip()
                break

        return cls(
            application=app,
            target_section="regular_marketplace",
            forbidden_sections=forbidden,
            objective=objective,
            query=query,
            allow_cart_actions=allow_cart,
        )

    @property
    def search_query(self) -> str:
        """Alias for .query — used by recovery_controller for search bypass."""
        return self.query



@dataclass
class ScreenObservation:
    """Structured observation of the current Android screen."""
    timestamp: float
    image: Image.Image
    foreground_package: str
    foreground_activity: str
    keyboard_visible: bool
    visible_texts: List[str]
    screen_type: str  # Screen classification
    visual_hash: str
    is_forbidden_section: bool = False
    confidence: float = 1.0

    @property
    def fingerprint(self) -> str:
        """Composite multi-signal fingerprint for loop detection."""
        # Combines activity + top text elements + visual hash prefix
        text_signature = "|".join(sorted(set(t.strip().lower() for t in self.visible_texts if len(t.strip()) > 3))[:6])
        return f"{self.foreground_activity}:{self.screen_type}:{self.visual_hash[:32]}:{text_signature}"


@dataclass
class ActionRecord:
    """Record of an executed action and its verification outcome."""
    step: int
    is_recovery: bool
    thought: str
    action: str
    params: Dict[str, Any]
    expected_postcondition: str
    observed_outcome: str = ""
    made_progress: bool = False
    transition_verified: bool = False

    def signature(self) -> str:
        """Returns a stable signature for action repetition tracking."""
        param_str = json_repr(self.params)
        return f"{self.action}:{param_str}"


def json_repr(d: Dict[str, Any]) -> str:
    """Deterministic string representation of params."""
    items = []
    for k in sorted(d.keys()):
        v = d[k]
        if isinstance(v, list) and len(v) == 2 and isinstance(v[0], (int, float)):
            # Bucket normalized points to ~50px granularity to detect near-identical taps
            items.append(f"{k}:[{round(v[0]/50)*50},{round(v[1]/50)*50}]")
        else:
            items.append(f"{k}:{v}")
    return ",".join(items)


@dataclass
class TaskState:
    """Persistent in-memory state tracking task execution and recovery."""
    goal: str
    intent: NavigationIntent
    current_observation: Optional[ScreenObservation] = None
    previous_observation: Optional[ScreenObservation] = None
    action_history: List[ActionRecord] = field(default_factory=list)
    screen_fingerprints: List[str] = field(default_factory=list)
    failed_strategies: List[str] = field(default_factory=list)
    recovery_attempts: int = 0
    consecutive_no_progress: int = 0
    max_task_steps: int = 25
    max_recovery_attempts: int = 4
    max_no_progress_steps: int = 3
    status: str = "running"  # "running", "completed", "failed", "cancelled"
    summary: str = ""

    def record_action(self, record: ActionRecord) -> None:
        self.action_history.append(record)

    def record_observation(self, obs: ScreenObservation) -> None:
        self.previous_observation = self.current_observation
        self.current_observation = obs
        self.screen_fingerprints.append(obs.fingerprint)

    def remaining_task_steps(self) -> int:
        return max(0, self.max_task_steps - len(self.action_history))

    def remaining_recovery_budget(self) -> int:
        return max(0, self.max_recovery_attempts - self.recovery_attempts)

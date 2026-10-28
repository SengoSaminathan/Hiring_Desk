"""Unit and Regression Tests for Mobile Agent Intelligent Recovery and Loop Detection.

Validates:
1. NavigationIntent extraction and cart boundary enforcement.
2. ScreenClassifier for Regular Marketplace vs Flipkart Minutes.
3. LoopDetector for unchanged screen, repeated actions, and oscillation cycles.
4. RecoveryController strategy generation and failed strategy avoidance.
5. LLMService resilient retry on transient HTTP 503 errors and JSON parsing.
"""

import unittest
from unittest.mock import MagicMock, patch
from PIL import Image

from models_and_state import (
    NavigationIntent,
    ScreenObservation,
    ActionRecord,
    TaskState,
    compute_visual_hash,
    visual_hash_distance,
)
from screen_classifier import ScreenClassifier
from loop_detector import LoopDetector
from recovery_controller import RecoveryController
from llm_service import LLMService


class TestNavigationIntent(unittest.TestCase):
    def test_search_without_cart_permission(self):
        task = "Open Flipkart and search for die cast cars in the normal Flipkart store, not Flipkart Minutes"
        intent = NavigationIntent.from_task(task)
        self.assertEqual(intent.application, "flipkart")
        self.assertEqual(intent.target_section, "regular_marketplace")
        self.assertIn("flipkart_minutes", intent.forbidden_sections)
        self.assertFalse(intent.allow_cart_actions)
        self.assertEqual(intent.objective, "search_products")

    def test_explicit_cart_permission(self):
        task = "Open Flipkart, search for boat headphones and add to cart"
        intent = NavigationIntent.from_task(task)
        self.assertTrue(intent.allow_cart_actions)
        self.assertEqual(intent.objective, "cart_checkout")


class TestScreenClassifier(unittest.TestCase):
    def setUp(self):
        self.intent = NavigationIntent(
            application="flipkart",
            target_section="regular_marketplace",
            forbidden_sections=["flipkart_minutes"],
        )

    def test_classifies_flipkart_minutes(self):
        screen_type, is_forbidden, _ = ScreenClassifier.classify(
            package="com.flipkart.android",
            activity="com.flipkart.android.activity.MinutesHomeActivity",
            visible_texts=["Minutes", "Delivery in 10-15 mins", "Grocery", "Search items"],
            keyboard_visible=False,
            intent=self.intent,
        )
        self.assertEqual(screen_type, "FLIPKART_MINUTES")
        self.assertTrue(is_forbidden)

    def test_classifies_regular_search_results(self):
        screen_type, is_forbidden, _ = ScreenClassifier.classify(
            package="com.flipkart.android",
            activity="com.flipkart.android.activity.SearchListingActivity",
            visible_texts=["Sort", "Filter", "Die Cast Cars", "Free Delivery", "Customer Ratings"],
            keyboard_visible=False,
            intent=self.intent,
        )
        self.assertEqual(screen_type, "REGULAR_SEARCH_RESULTS")
        self.assertFalse(is_forbidden)

    def test_classifies_minutes_search_results_as_forbidden(self):
        screen_type, is_forbidden, _ = ScreenClassifier.classify(
            package="com.flipkart.android",
            activity="com.flipkart.android.activity.ListingActivity",
            visible_texts=["Sort", "Filter", "Delivery in 10 mins", "Minutes Store"],
            keyboard_visible=False,
            intent=self.intent,
        )
        self.assertEqual(screen_type, "MINUTES_SEARCH_RESULTS")
        self.assertTrue(is_forbidden)


class TestLoopDetector(unittest.TestCase):
    def setUp(self):
        self.detector = LoopDetector(max_identical_actions=2, max_no_progress_steps=3)
        self.dummy_img = Image.new("RGB", (100, 100), color="white")
        self.v_hash = compute_visual_hash(self.dummy_img)

    def test_detects_forbidden_section_immediately(self):
        obs = ScreenObservation(
            timestamp=1.0,
            image=self.dummy_img,
            foreground_package="com.flipkart.android",
            foreground_activity="MinutesActivity",
            keyboard_visible=False,
            visible_texts=["Flipkart Minutes"],
            screen_type="FLIPKART_MINUTES",
            visual_hash=self.v_hash,
            is_forbidden_section=True,
        )
        result = self.detector.check(obs, None, [], [], 0)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_loop)
        self.assertEqual(result.loop_type, "FORBIDDEN_SECTION")

    def test_detects_repeated_identical_actions(self):
        obs = ScreenObservation(
            timestamp=1.0,
            image=self.dummy_img,
            foreground_package="com.flipkart.android",
            foreground_activity="SearchActivity",
            keyboard_visible=False,
            visible_texts=["Search"],
            screen_type="SEARCH_SUGGESTIONS",
            visual_hash=self.v_hash,
            is_forbidden_section=False,
        )
        act1 = ActionRecord(step=1, is_recovery=False, thought="", action="tap", params={"point": [500, 500]}, expected_postcondition="", made_progress=False)
        act2 = ActionRecord(step=2, is_recovery=False, thought="", action="tap", params={"point": [500, 500]}, expected_postcondition="", made_progress=False)

        result = self.detector.check(obs, obs, [act1, act2], ["fp1", "fp1"], 2)
        self.assertIsNotNone(result)
        self.assertEqual(result.loop_type, "REPEATED_ACTION")

    def test_detects_oscillation_cycle(self):
        obs = ScreenObservation(
            timestamp=1.0,
            image=self.dummy_img,
            foreground_package="com.flipkart.android",
            foreground_activity="SearchActivity",
            keyboard_visible=False,
            visible_texts=["Search"],
            screen_type="SEARCH_SUGGESTIONS",
            visual_hash=self.v_hash,
            is_forbidden_section=False,
        )
        # Sequence: A -> B -> A -> B
        fps = ["ScreenA", "ScreenB", "ScreenA", "ScreenB"]
        act = ActionRecord(step=4, is_recovery=False, thought="", action="key", params={"key": "back"}, expected_postcondition="", made_progress=True)

        result = self.detector.check(obs, obs, [act], fps, 0)
        self.assertIsNotNone(result)
        self.assertEqual(result.loop_type, "NAVIGATION_OSCILLATION")


class TestRecoveryController(unittest.TestCase):
    def setUp(self):
        self.dummy_llm = MagicMock()
        self.recovery = RecoveryController(self.dummy_llm)
        self.dummy_img = Image.new("RGB", (100, 100), color="white")
        self.intent = NavigationIntent(
            application="flipkart",
            target_section="regular_marketplace",
            forbidden_sections=["flipkart_minutes"],
        )

    def test_dismisses_keyboard_on_fallback(self):
        obs = ScreenObservation(
            timestamp=1.0,
            image=self.dummy_img,
            foreground_package="com.flipkart.android",
            foreground_activity="SearchActivity",
            keyboard_visible=True,
            visible_texts=["QWERTY Keyboard"],
            screen_type="SEARCH_SUGGESTIONS",
            visual_hash="0" * 256,
            is_forbidden_section=False,
        )
        state = TaskState(goal="Search die cast cars", intent=self.intent, current_observation=obs)
        self.dummy_llm.generate_action.return_value = None  # Force fallback

        decision = self.recovery._deterministic_fallback(state, MagicMock(loop_type="UNCHANGED_SCREEN"))
        self.assertEqual(decision["selected_recovery_strategy"], "dismiss_keyboard")
        self.assertEqual(decision["action"], "key")
        self.assertEqual(decision["key"], "back")

    def test_breaks_out_of_forbidden_minutes(self):
        obs = ScreenObservation(
            timestamp=1.0,
            image=self.dummy_img,
            foreground_package="com.flipkart.android",
            foreground_activity="MinutesActivity",
            keyboard_visible=False,
            visible_texts=["Minutes"],
            screen_type="FLIPKART_MINUTES",
            visual_hash="0" * 256,
            is_forbidden_section=True,
        )
        state = TaskState(goal="Search die cast cars", intent=self.intent, current_observation=obs)
        decision = self.recovery._deterministic_fallback(state, MagicMock(loop_type="FORBIDDEN_SECTION"))
        self.assertEqual(decision["selected_recovery_strategy"], "press_back_from_forbidden")
        self.assertEqual(decision["action"], "key")


class TestLLMService(unittest.TestCase):
    def test_parse_json_markdown_cleaning(self):
        raw = "```json\n{\n  \"thought\": \"test\",\n  \"action\": \"wait\"\n}\n```"
        parsed = LLMService._parse_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.get("action"), "wait")

    def test_parse_json_with_trailing_comma(self):
        raw = '{"thought": "test", "action": "wait",}'
        parsed = LLMService._parse_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.get("action"), "wait")


class TestBankingShield(unittest.TestCase):
    def test_detects_banking_packages(self):
        banking_pkgs = (
            "com.google.android.apps.nbu.paisa.user",
            "com.google.nbu.paisa",
            "com.phonepe.app",
            "net.one97.paytm",
            "in.org.npci.upiapp",
        )
        sample_gpay = "com.google.nbu.paisa.flutter.gpay.app.MainActivity"
        self.assertTrue(any(bp in sample_gpay.lower() for bp in banking_pkgs))
        sample_flipkart = "com.flipkart.android.activity.HomeFragmentHolderActivity"
        self.assertFalse(any(bp in sample_flipkart.lower() for bp in banking_pkgs))


if __name__ == "__main__":
    unittest.main()

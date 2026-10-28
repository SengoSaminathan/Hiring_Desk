"""Screen classification and navigation intent verification.

Distinguishes between:
- Android Home screen
- Regular Flipkart Shopping Home
- Flipkart Minutes interface / Minutes search results
- Search Suggestions (and detects store-specific tags in suggestions)
- Regular Marketplace Product Results
- Product Details
- Shopping Cart / Checkout / Order Confirmation
- Dialogs / Popups / Keyboards

Minutes Detection Rules (tightened to reduce false positives):
  A screen is classified as Minutes ONLY when at least 2 of the following
  strong signals are present, OR one strong + one weak signal. This prevents
  product names like "RC Car in Minutes" from triggering Minutes mode.

  STRONG signals (one is enough with another strong/weak):
    - Activity name contains "minutes" or "grocery"
    - Tabs/headers: "flipkart minutes", "minutes home", "grocery & more"
    - Delivery promise: "deliver in 10", "deliver in 15", "10-15 mins",
                        "get it in 10", "order in minutes"
    - Explicit "flipkart minutes" label in texts

  WEAK signals (require at least one strong signal alongside):
    - Word "minutes" appears anywhere in visible text
    - "instant delivery" / "quick delivery" in corpus
    - "supermart" in corpus
"""

from typing import List, Tuple
from models_and_state import NavigationIntent


# ---------------------------------------------------------------------------
# Minutes detection signal sets
# ---------------------------------------------------------------------------

# Any one of these = strong Minutes signal (needs at least one more strong/weak)
_MINUTES_STRONG_SIGNALS = (
    "flipkart minutes",
    "grocery & more",
    "minutes home",
    "deliver in 10",
    "deliver in 15",
    "delivery in 10",
    "delivery in 15",
    "10-15 mins",
    "get it in 10",
    "get it in 15",
    "order in minutes",
    "in 10 minutes",
    "in 15 minutes",
    "delivered in 10",
    "delivered in 15",
    # Bottom-nav tab label used in Minutes interface
    "minutes tab",
    "switch to minutes",
)

# These alone are NOT enough — must appear alongside a strong signal
_MINUTES_WEAK_SIGNALS = (
    "instant delivery",
    "quick delivery",
    "supermart",
    "grocery in",
    "grocery delivery",
)

# These activity name substrings = strong Minutes signal regardless of text
_MINUTES_ACTIVITY_NAMES = (
    "minutes",
    "grocery",
    "supermart",
    "quickcommerce",
    "instant",
)

# Screen types that unambiguously mean regular marketplace
_REGULAR_MARKETPLACE_SCREENS = (
    "REGULAR_SEARCH_RESULTS",
    "PRODUCT_DETAILS",
    "CART",
    "CHECKOUT_ADDRESS",
    "CHECKOUT_PAYMENT",
    "ORDER_CONFIRMATION",
    "FLIPKART_HOME",
)


def _is_minutes_screen(full_text: str, act_lower: str) -> bool:
    """
    Returns True only when there is enough evidence that this is the
    Flipkart Minutes interface — not just a product that mentions "minutes"
    somewhere in its name or description.

    Algorithm:
      1. If the activity name is a Minutes-specific activity → True
      2. Count strong signals in full text
      3. Count weak signals in full text
      4. Return True if:
           - strong_count >= 2, OR
           - strong_count >= 1 AND weak_count >= 1
    """
    # Rule 1: Activity-name based (most reliable)
    if any(s in act_lower for s in _MINUTES_ACTIVITY_NAMES):
        return True

    # Rule 2: Text signal counting
    strong_count = sum(1 for sig in _MINUTES_STRONG_SIGNALS if sig in full_text)
    weak_count = sum(1 for sig in _MINUTES_WEAK_SIGNALS if sig in full_text)

    return strong_count >= 2 or (strong_count >= 1 and weak_count >= 1)


class ScreenClassifier:
    """Classifies Android screens using activity names and visible UI texts."""

    @staticmethod
    def classify(
        package: str,
        activity: str,
        visible_texts: List[str],
        keyboard_visible: bool,
        intent: NavigationIntent,
    ) -> Tuple[str, bool, float]:
        """Returns (screen_type, is_forbidden, confidence).

        is_forbidden is only True when:
          - The screen type is in intent.forbidden_sections mapping, AND
          - The Minutes detection confidence is HIGH (not a false positive).
        """
        texts_lower = [t.lower().strip() for t in visible_texts if t.strip()]
        full_text_corpus = " ".join(texts_lower)
        act_lower = activity.lower()
        pkg_lower = package.lower()

        # ------------------------------------------------------------------
        # 1. Android Launcher / Home screen
        # ------------------------------------------------------------------
        if any(
            launcher in pkg_lower
            for launcher in ("launcher", "systemui", "nexuslauncher", "pixel", "desktop")
        ):
            return "ANDROID_HOME", False, 0.95

        # ------------------------------------------------------------------
        # 2. Dialogs / Popups / Permission Overlays
        #    (only when text count is low — avoids misclassifying product pages)
        # ------------------------------------------------------------------
        dialog_keywords = (
            "allow", "deny", "while using the app", "permission",
            "update now", "remind me later", "location access",
            "enable location", "don't ask again",
        )
        if any(kw in full_text_corpus for kw in dialog_keywords) and len(visible_texts) < 12:
            return "DIALOG_POPUP", False, 0.9

        # ------------------------------------------------------------------
        # 3. Flipkart application screens
        # ------------------------------------------------------------------
        if "flipkart" not in pkg_lower:
            return "UNKNOWN", False, 0.5

        # -- Minutes detection (tightened) ----------------------------------
        is_minutes = _is_minutes_screen(full_text_corpus, act_lower)
        is_forbidden = is_minutes and ("flipkart_minutes" in intent.forbidden_sections)

        # -- Cart screen ----------------------------------------------------
        cart_keywords = ("my cart", "price details", "place order", "total amount", "proceed to buy")
        if any(kw in full_text_corpus for kw in cart_keywords):
            return "CART", False, 0.95

        # -- Checkout: Address selection ------------------------------------
        checkout_address_kws = (
            "select delivery address", "deliver to", "add new address",
            "pincode", "change address", "delivery address",
        )
        if any(kw in full_text_corpus for kw in checkout_address_kws):
            return "CHECKOUT_ADDRESS", False, 0.93

        # -- Checkout: Payment screen ---------------------------------------
        checkout_payment_kws = (
            "upi", "net banking", "credit card", "debit card",
            "pay now", "emi", "cod", "cash on delivery",
            "google pay", "phonepe", "paytm",
        )
        # Must also have a price/order context to avoid false matches
        has_price_context = any(
            kw in full_text_corpus
            for kw in ("order total", "total payable", "pay ₹", "amount payable", "₹")
        )
        if sum(1 for kw in checkout_payment_kws if kw in full_text_corpus) >= 2 and has_price_context:
            return "CHECKOUT_PAYMENT", False, 0.93

        # -- Order Confirmation screen --------------------------------------
        confirm_kws = (
            "order placed", "order confirmed", "thank you for your order",
            "order id", "expected delivery", "arriving by", "track your order",
        )
        if any(kw in full_text_corpus for kw in confirm_kws):
            return "ORDER_CONFIRMATION", False, 0.97

        # -- Product Details screen ----------------------------------------
        product_detail_kws = ("add to cart", "buy now", "ratings & reviews", "specifications", "highlights")
        # Ensure we're not on a search suggestions page
        is_suggestion_page = keyboard_visible or any(
            kw in full_text_corpus for kw in ("recent searches", "search for products")
        )
        if any(kw in full_text_corpus for kw in product_detail_kws) and not is_suggestion_page:
            return "PRODUCT_DETAILS", False, 0.92

        # -- Search Input / Suggestions screen ------------------------------
        is_searching = keyboard_visible or any(
            kw in full_text_corpus
            for kw in ("search for products", "search for items", "recent searches", "trending searches")
        )
        has_suggestions = any(
            kw in full_text_corpus
            for kw in ("trending", "discover more", "popular searches", "top searches")
        ) or ("suggestion" in act_lower or ("search" in act_lower and len(texts_lower) > 5))

        if is_searching or has_suggestions:
            if any(kw in full_text_corpus for kw in ("search", "find", "cancel")):
                if is_minutes and "in minutes" in full_text_corpus:
                    return "MINUTES_SEARCH_SUGGESTIONS", is_forbidden, 0.85
                return "SEARCH_SUGGESTIONS", False, 0.85

        # -- Product listing / Results screens  ----------------------------
        result_kws = (
            "sort", "filter", "filters", "customer ratings",
            "free delivery", "results for", "sponsored",
        )
        has_results = (
            any(kw in full_text_corpus for kw in result_kws)
            or "listing" in act_lower
            or "browse" in act_lower
            or "search" in act_lower
        )
        if has_results:
            if is_minutes:
                return "MINUTES_SEARCH_RESULTS", is_forbidden, 0.90
            return "REGULAR_SEARCH_RESULTS", False, 0.90

        # -- Flipkart Minutes Home / Landing --------------------------------
        if is_minutes:
            return "FLIPKART_MINUTES", is_forbidden, 0.90

        # -- Regular Flipkart Shopping Home ---------------------------------
        home_kws = ("categories", "explore", "account", "supercoin", "top picks", "deals of the day")
        if any(kw in full_text_corpus for kw in home_kws):
            return "FLIPKART_HOME", False, 0.85

        return "FLIPKART_PAGE", False, 0.6

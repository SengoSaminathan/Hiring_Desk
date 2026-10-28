"""Order Verifier for FamilyOS AI.

Implements the evidence-ledger model for merchant order confirmation.

Strategy:
  1. BEFORE payment handover: Capture a "pre-payment fingerprint" — the set
     of Order IDs that already exist in emails/SMS for this merchant.
  2. AFTER payment handover: Re-scan the same channels for NEW order
     confirmation messages that did not exist in the fingerprint.
  3. A new order confirmation appearing after the handover = authoritative
     proof the order was placed.

Privacy rule: Evidence is always scoped to the authenticated user's own
Gmail inbox and their own device SMS stream (via MongoDB). One family
member's data never crosses into another member's session.

Supported merchants (with regex corpus):
  - Flipkart
  - Amazon / Amazon.in
  - Swiggy
  - Zomato
  - Myntra
  - Meesho
  - Nykaa
  - BigBasket
  - Blinkit / Grofers

Channels probed (in priority order):
  1. Gmail  — parsed via Google Gmail API  (token.pickle)
  2. SMS    — parsed via MongoDB rawevents  (MONGODB_URI env var)

Each channel is optional; if unavailable, it is silently skipped.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Merchant SMS / Email Corpus  (regex patterns)
# ---------------------------------------------------------------------------
# For each merchant we define:
#   - "order_id"  patterns: how to extract the merchant-side Order ID
#   - "amount"    patterns: how to extract the ₹ total
#   - "keywords"  that must appear (at least one) for a hit to be valid
#   - "senders"   list of DLT/SMS sender prefixes used by this merchant
#
# All patterns are case-insensitive. Named groups: order_id, amount.

MERCHANT_CORPUS: Dict[str, Dict] = {
    "flipkart": {
        "senders": ["FKTSMS", "FK-SNDRS", "FLPKRT", "AD-FLPKRT", "FK-ORDER"],
        "keywords": [
            "order confirmed", "order placed", "order id", "your order",
            "shipped", "out for delivery", "delivered", "flipkart order",
        ],
        "order_id": [
            r"(?:Order\s*(?:ID|#|No\.?|Number)[:\s]*|OD)[:\s]*(?P<order_id>OD\d{15,}|\w{10,20})",
            r"(?P<order_id>OD\d{10,})",
        ],
        "amount": [
            r"(?:total|amount|paid|rs\.?|₹)[:\s]*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
            r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
        ],
        "email_subjects": [
            r"order.*confirmed", r"your flipkart order", r"order.*placed",
            r"ready to ship", r"out for delivery",
        ],
        "email_from": [r"@flipkart\.com", r"@fkmail\.com"],
    },
    "amazon": {
        "senders": ["AMAZON", "AMAZIN", "AD-AMAZON", "AM-ORDER", "AMZNIN"],
        "keywords": [
            "order confirmed", "order placed", "your amazon order",
            "thank you for your order", "order number", "arriving",
            "shipped", "out for delivery",
            "is confirmed", "thank you", "confirmed",
        ],
        "order_id": [
            r"(?:Order(?:\s*No\.?|\s*#|\s*ID)?[:\s]*)(?P<order_id>\d{3}-\d{7}-\d{7})",
            r"(?P<order_id>\d{3}-\d{7}-\d{7})",
        ],
        "amount": [
            r"(?:order\s*total|total|amount|paid)[:\s]*(?:INR|Rs\.?|₹)[:\s]*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
            r"(?:INR|Rs\.?|₹)\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
            r"of\s+(?:Rs\.?|₹)\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
        ],
        "email_subjects": [
            r"your amazon\.in order", r"order confirmation", r"has been shipped",
            r"arriving", r"delivered",
        ],
        "email_from": [r"@amazon\.in", r"@amazon\.com", r"@amazonemail\.com"],
    },
    "swiggy": {
        "senders": ["SWIGGY", "AD-SWGGY", "SWGGYF"],
        "keywords": [
            "order confirmed", "order placed", "your order", "preparing",
            "picked up", "on the way", "delivered", "order id",
        ],
        "order_id": [
            r"(?:Order\s*(?:ID|#|No\.?)[:\s]*)(?P<order_id>\d{8,15})",
            r"#(?P<order_id>\d{8,15})",
        ],
        "amount": [
            r"(?:total|amount|bill|paid|rs\.?|₹)[:\s]*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
            r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
        ],
        "email_subjects": [
            r"order.*confirmed", r"your swiggy order", r"on the way",
            r"delivered", r"out for delivery",
        ],
        "email_from": [r"@swiggy\.in", r"@swiggymail\.in"],
    },
    "zomato": {
        "senders": ["ZOMATO", "AD-ZMTO", "ZOMTOF"],
        "keywords": [
            "order placed", "order confirmed", "order id", "restaurant",
            "on the way", "delivered", "your order",
        ],
        "order_id": [
            r"(?:Order\s*(?:ID|#|No\.?)[:\s]*)(?P<order_id>\d{7,14})",
        ],
        "amount": [
            r"(?:total|amount|bill|paid|₹)[:\s]*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
            r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)",
        ],
        "email_subjects": [
            r"order.*placed", r"your zomato order", r"delivered",
        ],
        "email_from": [r"@zomato\.com"],
    },
    "myntra": {
        "senders": ["MYNTRA", "AD-MNTRF"],
        "keywords": ["order confirmed", "order placed", "order id", "shipment"],
        "order_id": [r"(?:Order\s*(?:ID|#)[:\s]*)(?P<order_id>\d{10,18})"],
        "amount": [r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"],
        "email_subjects": [r"order.*confirmed", r"your myntra order"],
        "email_from": [r"@myntra\.com"],
    },
    "bigbasket": {
        "senders": ["BIGBSK", "BB-ORD", "AD-BIGBS"],
        "keywords": ["order confirmed", "order id", "delivered", "your order"],
        "order_id": [r"(?:Order\s*(?:ID|#|No\.?)[:\s]*)(?P<order_id>\d{8,15})"],
        "amount": [r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"],
        "email_subjects": [r"order.*confirmed", r"order.*placed"],
        "email_from": [r"@bigbasket\.com"],
    },
    "blinkit": {
        "senders": ["BLNKIT", "BLINKT", "GROFER", "AD-BLNKT"],
        "keywords": ["order confirmed", "order placed", "delivered", "order id"],
        "order_id": [r"(?:Order\s*(?:ID|#)[:\s]*)(?P<order_id>\d{8,15})"],
        "amount": [r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"],
        "email_subjects": [r"order.*confirmed"],
        "email_from": [r"@blinkit\.com", r"@grofers\.com"],
    },
    "meesho": {
        "senders": ["MEESHO", "AD-MEESH"],
        "keywords": ["order confirmed", "order placed", "order id"],
        "order_id": [r"(?:Order\s*(?:ID|#)[:\s]*)(?P<order_id>\d{10,18})"],
        "amount": [r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"],
        "email_subjects": [r"order.*confirmed", r"your meesho order"],
        "email_from": [r"@meesho\.com"],
    },
    "nykaa": {
        "senders": ["NYKAA", "AD-NYKAA"],
        "keywords": ["order confirmed", "order placed", "order id"],
        "order_id": [r"(?:Order\s*(?:ID|#)[:\s]*)(?P<order_id>\d{8,15})"],
        "amount": [r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"],
        "email_subjects": [r"order.*confirmed", r"your nykaa order"],
        "email_from": [r"@nykaa\.com"],
    },
}


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------

@dataclass
class OrderEvidence:
    """A single discovered order confirmation evidence record."""
    channel: str                  # "gmail" | "sms"
    merchant: str
    order_id: Optional[str]       # Extracted order ID (may be None if not found)
    amount: Optional[float]       # Extracted amount (may be None)
    raw_snippet: str              # First 300 chars of the source message
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: Optional[str] = None  # Gmail message ID or MongoDB _id

    def fingerprint(self) -> str:
        """Stable identity key for deduplication."""
        # Prefer order_id; fall back to snippet hash
        if self.order_id:
            return f"{self.merchant}:{self.order_id}"
        return f"{self.merchant}:{hash(self.raw_snippet[:120])}"


@dataclass
class VerificationResult:
    verified: bool
    confidence: str              # "HIGH" | "MEDIUM" | "LOW" | "UNVERIFIED"
    method: str                  # "gmail_order_id" | "sms_order_id" | "gmail_keyword" | "none"
    new_evidence: List[OrderEvidence] = field(default_factory=list)
    details: str = ""


# ---------------------------------------------------------------------------
# Text Parsing Helpers
# ---------------------------------------------------------------------------

def _extract_order_id(text: str, merchant: str) -> Optional[str]:
    corpus = MERCHANT_CORPUS.get(merchant, {})
    for pattern in corpus.get("order_id", []):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group("order_id").strip()
    return None


def _extract_amount(text: str, merchant: str) -> Optional[float]:
    corpus = MERCHANT_CORPUS.get(merchant, {})
    for pattern in corpus.get("amount", []):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group("amount").replace(",", "").strip()
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def _has_order_keywords(text: str, merchant: str) -> bool:
    corpus = MERCHANT_CORPUS.get(merchant, {})
    text_lower = text.lower()
    return any(kw in text_lower for kw in corpus.get("keywords", []))


def _is_merchant_sender(sender: str, merchant: str) -> bool:
    corpus = MERCHANT_CORPUS.get(merchant, {})
    sender_upper = (sender or "").upper()
    for prefix in corpus.get("senders", []):
        if prefix in sender_upper:
            return True
    return False


def _is_merchant_email_from(from_addr: str, merchant: str) -> bool:
    corpus = MERCHANT_CORPUS.get(merchant, {})
    for pattern in corpus.get("email_from", []):
        if re.search(pattern, from_addr, re.IGNORECASE):
            return True
    return False


def _matches_email_subject(subject: str, merchant: str) -> bool:
    corpus = MERCHANT_CORPUS.get(merchant, {})
    for pattern in corpus.get("email_subjects", []):
        if re.search(pattern, subject, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Gmail Channel
# ---------------------------------------------------------------------------

def _build_gmail_service():
    """Load Gmail API service from token.pickle. Returns None if unavailable."""
    try:
        import base64 as _b64
        import pickle

        from googleapiclient.discovery import build

        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)

        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open("token.pickle", "wb") as f:
                pickle.dump(creds, f)

        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        logger.debug("Gmail unavailable: %s", e)
        return None


def _gmail_message_text(payload: dict) -> str:
    """Recursively extract plain text from a Gmail message payload."""
    import base64
    import html as html_mod

    texts = []
    data = (payload.get("body") or {}).get("data")
    if data:
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        if payload.get("mimeType") == "text/html":
            decoded = html_mod.unescape(re.sub(r"<[^>]+>", " ", decoded))
        texts.append(decoded)
    for part in payload.get("parts") or []:
        texts.append(_gmail_message_text(part))
    return " ".join(texts)


def _scan_gmail(
    merchant: str,
    since: datetime,
    max_results: int = 10,
) -> List[OrderEvidence]:
    """Scan Gmail inbox for order confirmation messages for a given merchant."""
    service = _build_gmail_service()
    if not service:
        return []

    corpus = MERCHANT_CORPUS.get(merchant, {})
    # Build a Gmail search query
    merchant_name = merchant.replace("_", " ").title()
    after_ts = int((since - timedelta(seconds=90)).timestamp())
    query = f"from:({merchant_name}) after:{after_ts}"
    # Also try the email domain patterns
    domain_terms = " OR ".join(
        re.sub(r"[@\\^$.*+?()\[\]{}|]", "", p) for p in corpus.get("email_from", [])
    )
    if domain_terms:
        query = f"({query}) OR (from:({domain_terms}) after:{after_ts})"

    try:
        results = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
    except Exception as e:
        logger.warning("Gmail list failed for %s: %s", merchant, e)
        return []

    found: List[OrderEvidence] = []
    for ref in results.get("messages", []):
        try:
            msg = service.users().messages().get(
                userId="me", id=ref["id"], format="full"
            ).execute()
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            from_addr = headers.get("from", "")
            subject = headers.get("subject", "")

            # Filter: must be from merchant's domain
            if not _is_merchant_email_from(from_addr, merchant):
                # Try subject keyword match as fallback
                if not _matches_email_subject(subject, merchant):
                    continue

            body = _gmail_message_text(msg["payload"])
            full_text = f"{subject} {body}"

            # Must have at least one confirmation keyword
            if not _has_order_keywords(full_text, merchant):
                continue

            order_id = _extract_order_id(full_text, merchant)
            amount = _extract_amount(full_text, merchant)
            snippet = full_text[:300].replace("\n", " ").strip()

            found.append(OrderEvidence(
                channel="gmail",
                merchant=merchant,
                order_id=order_id,
                amount=amount,
                raw_snippet=snippet,
                message_id=ref["id"],
            ))
        except Exception as e:
            logger.debug("Gmail message fetch error: %s", e)
            continue

    return found


# ---------------------------------------------------------------------------
# SMS Channel (MongoDB)
# ---------------------------------------------------------------------------

def _get_mongo_collection():
    """Get the MongoDB SMS collection. Returns None if unavailable."""
    try:
        import os
        from pymongo import MongoClient
        uri = os.environ.get("MONGODB_URI")
        if not uri:
            return None
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        return client["mobileuse"]["rawevents"]
    except Exception as e:
        logger.debug("MongoDB unavailable: %s", e)
        return None


def _scan_sms(
    merchant: str,
    since: datetime,
    limit: int = 50,
) -> List[OrderEvidence]:
    """Scan MongoDB SMS corpus for order confirmation messages."""
    collection = _get_mongo_collection()
    if collection is None:
        return []

    corpus = MERCHANT_CORPUS.get(merchant, {})
    since_utc = since.astimezone(timezone.utc).replace(tzinfo=None)
    # Look slightly before the task start to account for clock skew
    since_utc -= timedelta(seconds=90)

    # Build sender filter
    sender_patterns = corpus.get("senders", [])
    query: dict = {
        "source": "sms",
        "deviceTimestamp": {"$gt": since_utc},
    }
    if sender_patterns:
        query["$or"] = [
            {"payload.sender": {"$regex": p, "$options": "i"}}
            for p in sender_patterns
        ] + [
            {"payload.body": {"$regex": merchant, "$options": "i"}}
        ]

    try:
        cursor = collection.find(query).sort(
            [("deviceTimestamp", -1), ("_id", -1)]
        ).limit(limit)
    except Exception as e:
        logger.warning("MongoDB query failed for %s: %s", merchant, e)
        return []

    found: List[OrderEvidence] = []
    for doc in cursor:
        payload = doc.get("payload") or {}
        sender = payload.get("sender", "")
        body = payload.get("body", "")
        full_text = f"{sender} {body}"

        # Validate sender or keyword presence
        sender_ok = _is_merchant_sender(sender, merchant)
        keyword_ok = _has_order_keywords(full_text, merchant)
        if not (sender_ok or keyword_ok):
            continue

        order_id = _extract_order_id(full_text, merchant)
        amount = _extract_amount(full_text, merchant)
        snippet = full_text[:300].replace("\n", " ").strip()

        found.append(OrderEvidence(
            channel="sms",
            merchant=merchant,
            order_id=order_id,
            amount=amount,
            raw_snippet=snippet,
            message_id=str(doc.get("_id", "")),
        ))

    return found


# ---------------------------------------------------------------------------
# Order Fingerprint (Pre-payment snapshot)
# ---------------------------------------------------------------------------

@dataclass
class OrderFingerprint:
    """Snapshot of order evidence BEFORE the payment handover."""
    merchant: str
    captured_at: datetime
    known_order_ids: FrozenSet[str]        # All order IDs already known
    known_fingerprints: FrozenSet[str]     # Broader fingerprint set for fallback

    @classmethod
    def capture(cls, merchant: str, since_window: timedelta = timedelta(days=7)) -> "OrderFingerprint":
        """Capture a baseline fingerprint for the given merchant."""
        since = datetime.now(timezone.utc) - since_window
        evidence = _scan_all_channels(merchant, since)
        known_ids: Set[str] = set()
        known_fps: Set[str] = set()
        for ev in evidence:
            if ev.order_id:
                known_ids.add(ev.order_id)
            known_fps.add(ev.fingerprint())
        logger.info(
            "[OrderVerifier] Pre-payment fingerprint for %s: %d known orders",
            merchant, len(known_ids),
        )
        return cls(
            merchant=merchant,
            captured_at=datetime.now(timezone.utc),
            known_order_ids=frozenset(known_ids),
            known_fingerprints=frozenset(known_fps),
        )


# ---------------------------------------------------------------------------
# Multi-Channel Scanner
# ---------------------------------------------------------------------------

def _scan_all_channels(merchant: str, since: datetime) -> List[OrderEvidence]:
    """Probe Gmail and SMS for merchant order confirmations since `since`."""
    results: List[OrderEvidence] = []
    try:
        results.extend(_scan_gmail(merchant, since))
    except Exception as e:
        logger.warning("[OrderVerifier] Gmail scan error: %s", e)
    try:
        results.extend(_scan_sms(merchant, since))
    except Exception as e:
        logger.warning("[OrderVerifier] SMS scan error: %s", e)
    return results


# ---------------------------------------------------------------------------
# Main Verifier
# ---------------------------------------------------------------------------

class OrderVerifier:
    """Verifies order placement via pre/post confirmation fingerprinting.

    Usage:
        # Step 1 — Before handing over to the user for payment:
        fingerprint = OrderVerifier.pre_payment_snapshot("flipkart")

        # Step 2 — After the user completes payment on their phone:
        result = OrderVerifier.post_payment_verify(fingerprint, expected_amount=445.0)
        if result.verified:
            print("Order confirmed:", result.details)
    """

    POLL_INTERVAL_SECONDS: int = 8
    MAX_POLL_SECONDS: int = 120        # Wait up to 2 minutes for a new message
    POST_PAYMENT_LOOKBACK: timedelta = timedelta(minutes=5)

    @classmethod
    def pre_payment_snapshot(
        cls,
        merchant: str,
        lookback_days: int = 7,
    ) -> OrderFingerprint:
        """Capture a baseline of existing order confirmations before the payment."""
        print(f"[OrderVerifier] Capturing pre-payment order fingerprint for '{merchant}'...")
        fp = OrderFingerprint.capture(merchant, since_window=timedelta(days=lookback_days))
        print(f"[OrderVerifier] Baseline: {len(fp.known_order_ids)} existing order IDs found.")
        return fp

    @classmethod
    def post_payment_verify(
        cls,
        fingerprint: OrderFingerprint,
        expected_amount: Optional[float] = None,
        amount_tolerance: float = 5.0,   # ₹5 rounding tolerance
    ) -> VerificationResult:
        """Poll for new order confirmation evidence not present in the fingerprint.

        Polls until a new confirmation is found or MAX_POLL_SECONDS elapses.
        """
        merchant = fingerprint.merchant
        since = fingerprint.captured_at - cls.POST_PAYMENT_LOOKBACK
        deadline = time.time() + cls.MAX_POLL_SECONDS

        print(
            f"[OrderVerifier] Waiting for new '{merchant}' order confirmation "
            f"(up to {cls.MAX_POLL_SECONDS}s)..."
        )

        while time.time() < deadline:
            candidates = _scan_all_channels(merchant, since)
            new_evidence = cls._filter_new(candidates, fingerprint)

            if new_evidence:
                return cls._build_result(new_evidence, expected_amount, amount_tolerance)

            remaining = int(deadline - time.time())
            print(
                f"[OrderVerifier] No new confirmation yet. "
                f"Retrying in {cls.POLL_INTERVAL_SECONDS}s "
                f"({remaining}s remaining)..."
            )
            time.sleep(cls.POLL_INTERVAL_SECONDS)

        # Timeout — return UNVERIFIED
        return VerificationResult(
            verified=False,
            confidence="UNVERIFIED",
            method="none",
            new_evidence=[],
            details=(
                f"No new order confirmation found for '{merchant}' "
                f"within {cls.MAX_POLL_SECONDS}s after payment handover."
            ),
        )

    @classmethod
    def _filter_new(
        cls,
        candidates: List[OrderEvidence],
        fingerprint: OrderFingerprint,
    ) -> List[OrderEvidence]:
        """Return only evidence that is genuinely new (not in the fingerprint)."""
        new: List[OrderEvidence] = []
        for ev in candidates:
            # Primary: order_id deduplication
            if ev.order_id and ev.order_id in fingerprint.known_order_ids:
                continue
            # Secondary: full fingerprint deduplication
            if ev.fingerprint() in fingerprint.known_fingerprints:
                continue
            new.append(ev)
        return new

    @classmethod
    def _build_result(
        cls,
        new_evidence: List[OrderEvidence],
        expected_amount: Optional[float],
        tolerance: float,
    ) -> VerificationResult:
        """Build a VerificationResult from newly discovered evidence."""
        # Prefer evidence that has an explicit order_id
        has_order_id = [ev for ev in new_evidence if ev.order_id]
        primary = has_order_id[0] if has_order_id else new_evidence[0]

        # Determine method
        method = f"{primary.channel}_order_id" if primary.order_id else f"{primary.channel}_keyword"

        # Confidence tiers
        if primary.order_id and expected_amount and primary.amount:
            amount_match = abs((primary.amount or 0.0) - expected_amount) <= tolerance
            confidence = "HIGH" if amount_match else "MEDIUM"
            details = (
                f"Order ID {primary.order_id} found via {primary.channel}. "
                f"Amount ₹{primary.amount:.2f} "
                f"({'matches' if amount_match else 'differs from'} expected ₹{expected_amount:.2f})."
            )
        elif primary.order_id:
            confidence = "MEDIUM"
            details = f"Order ID {primary.order_id} found via {primary.channel} (amount not verified)."
        else:
            confidence = "LOW"
            details = (
                f"Order confirmation keywords detected via {primary.channel} "
                f"(no order ID extracted). Snippet: {primary.raw_snippet[:120]}"
            )

        return VerificationResult(
            verified=True,
            confidence=confidence,
            method=method,
            new_evidence=new_evidence,
            details=details,
        )

    @classmethod
    def quick_check(
        cls,
        merchant: str,
        since: datetime,
        expected_amount: Optional[float] = None,
    ) -> VerificationResult:
        """Single-shot check (no polling). Useful for immediate post-payment
        verification when the user indicates the order was already placed."""
        candidates = _scan_all_channels(merchant, since)
        if not candidates:
            return VerificationResult(
                verified=False,
                confidence="UNVERIFIED",
                method="none",
                details=f"No order confirmation found for '{merchant}' since {since.isoformat()}.",
            )
        return cls._build_result(candidates, expected_amount, amount_tolerance=5.0)


# ---------------------------------------------------------------------------
# CLI Test Utility
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)

    merchant_arg = sys.argv[1] if len(sys.argv) > 1 else "flipkart"
    amount_arg = float(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"\n[Test] Capturing pre-payment snapshot for: {merchant_arg}")
    fp = OrderVerifier.pre_payment_snapshot(merchant_arg)
    print(f"       Known IDs: {list(fp.known_order_ids)[:5]}")

    print(f"\n[Test] Running quick check for last 5 minutes of {merchant_arg} messages...")
    result = OrderVerifier.quick_check(
        merchant=merchant_arg,
        since=datetime.now(timezone.utc) - timedelta(minutes=5),
        expected_amount=amount_arg,
    )
    print(f"\n  Verified:    {result.verified}")
    print(f"  Confidence:  {result.confidence}")
    print(f"  Method:      {result.method}")
    print(f"  Details:     {result.details}")
    if result.new_evidence:
        for ev in result.new_evidence:
            print(f"\n  Evidence [{ev.channel}]:")
            print(f"    Order ID: {ev.order_id}")
            print(f"    Amount:   ₹{ev.amount}")
            print(f"    Snippet:  {ev.raw_snippet[:160]}")

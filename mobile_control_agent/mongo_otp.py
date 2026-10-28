import os
import re
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient

from otp_text import extract_otp_from_text

# Phone and PC clocks can drift, and the OTP SMS can land a few seconds before
# the agent's run is considered "started" — so look slightly further back.
CLOCK_SKEW_ALLOWANCE = timedelta(seconds=60)

_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=10000)
        _collection = client["mobileuse"]["rawevents"]
    return _collection


def extract_otp(doc: dict) -> str | None:
    payload = doc.get("payload") or {}
    if payload.get("otp"):
        return str(payload["otp"])
    return extract_otp_from_text(payload.get("body") or "")


def find_sms_otp(org: str | None, since: datetime) -> str | None:
    """Newest OTP-bearing SMS received after `since`, optionally narrowed to
    one org (matched against the DLT sender header or the message body)."""
    # deviceTimestamp is stored as naive UTC
    since_utc = since.astimezone(timezone.utc).replace(tzinfo=None)
    query = {"source": "sms", "deviceTimestamp": {"$gt": since_utc - CLOCK_SKEW_ALLOWANCE}}
    if org:
        pattern = re.escape(org)
        query["$or"] = [
            {"payload.sender": {"$regex": pattern, "$options": "i"}},
            {"payload.body": {"$regex": pattern, "$options": "i"}},
        ]
    cursor = _get_collection().find(query).sort([("deviceTimestamp", -1), ("_id", -1)]).limit(10)
    for doc in cursor:
        otp = extract_otp(doc)
        if otp:
            return otp
    return None

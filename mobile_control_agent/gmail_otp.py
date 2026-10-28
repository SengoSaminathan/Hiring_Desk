import base64
import html
import pickle
import re
from datetime import datetime, timedelta

from googleapiclient.discovery import build

from otp_text import extract_otp_from_text


def _message_text(payload: dict) -> str:
    """Flatten an email's text/plain and text/html parts into plain text.
    The OTP usually isn't in Gmail's ~200-char snippet, so the body is needed."""
    texts = []
    data = (payload.get("body") or {}).get("data")
    if data:
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        if payload.get("mimeType") == "text/html":
            decoded = html.unescape(re.sub(r"<[^>]+>", " ", decoded))
        texts.append(decoded)
    for part in payload.get("parts") or []:
        texts.append(_message_text(part))
    return " ".join(texts)


def fetch_gmail_otp(org: str | None = None, since: datetime | None = None):
    """Fetch the latest OTP/verification code from Gmail.

    When `org` is given (e.g. "amazon", "flipkart"), only emails mentioning
    that org are searched. When `since` is given, only emails received after
    it are considered, so a stale code from an earlier login is never reused.
    Checks the few most recent matches, since Gmail's search ranks by
    relevance and a promo email can outrank the actual OTP email.
    """
    with open("token.pickle", "rb") as token:
        creds = pickle.load(token)

    if creds and creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)

    terms = [org] if org else []
    if since:
        terms.append(f"after:{int((since - timedelta(seconds=60)).timestamp())}")
    query = " ".join(terms)
    results = service.users().messages().list(userId="me", q=query, maxResults=5).execute()

    for ref in results.get("messages", []):
        message = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        otp = extract_otp_from_text(_message_text(message["payload"]))
        if otp:
            return otp
    return None

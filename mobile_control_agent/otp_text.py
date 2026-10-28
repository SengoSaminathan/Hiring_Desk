import re

# Prefer a number that sits next to an OTP-ish keyword, so dates, times,
# account numbers, or "password is 349041" in the same message aren't picked up.
OTP_AFTER_KEYWORD = re.compile(
    r"(?:otp|one[\s-]?time[\s-]?password|verification code|security code|code)\D{0,30}?(\d{4,8})\b",
    re.IGNORECASE,
)
OTP_BEFORE_KEYWORD = re.compile(r"\b(\d{4,8})\b\D{0,20}?(?:is|as)\s+(?:your\s+)?(?:otp|code)", re.IGNORECASE)


def extract_otp_from_text(text: str) -> str | None:
    match = OTP_BEFORE_KEYWORD.search(text) or OTP_AFTER_KEYWORD.search(text)
    return match.group(1) if match else None

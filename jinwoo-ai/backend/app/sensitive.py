"""Conservative checks for values that must not enter long-term memory."""

from __future__ import annotations

import re

# These patterns deliberately require a value-like shape, so a harmless note
# such as "document the password policy" remains possible while actual secrets
# and one-time codes are rejected before they reach SQLite.
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"\b(?:password|passcode|pin)\s*(?:is|:|=)\s*\S{3,}", re.IGNORECASE),
    re.compile(r"\b(?:api[ _-]?key|secret|access[ _-]?token|auth[ _-]?token)\s*(?:is|:|=)\s*\S{6,}", re.IGNORECASE),
    re.compile(r"\bbearer\s+[A-Za-z0-9._~+/=-]{12,}\b", re.IGNORECASE),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\b(?:otp|one[ -]?time(?:[ -]?password)?|verification code)\s*(?:is|:|=)\s*\d{4,8}\b", re.IGNORECASE),
)


def contains_sensitive_value(content: str) -> bool:
    """Return whether content appears to contain a secret or one-time code."""

    return any(pattern.search(content) is not None for pattern in _SENSITIVE_VALUE_PATTERNS)

"""Safe URL representations for logs and diagnostics."""

import re
from urllib.parse import urlsplit, urlunsplit


URL_IN_TEXT_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def redact_url_for_log(url: object) -> str:
    """Remove query, fragment, credentials, and control characters from a URL."""
    text = str(url or "").replace("\r", "").replace("\n", "").replace("\t", "")
    try:
        parsed = urlsplit(text)
        if parsed.scheme and parsed.hostname:
            hostname = parsed.hostname
            if ":" in hostname and not hostname.startswith("["):
                hostname = f"[{hostname}]"
            try:
                port = parsed.port
            except ValueError:
                port = None
            netloc = f"{hostname}:{port}" if port is not None else hostname
            return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
    except (AttributeError, TypeError, ValueError):
        return text.split("?", 1)[0].split("#", 1)[0]

    return text.split("?", 1)[0].split("#", 1)[0]


def redact_urls_in_text(message: object) -> str:
    """Remove query strings from every HTTP(S) URL embedded in log text."""
    text = str(message or "")
    return URL_IN_TEXT_PATTERN.sub(
        lambda match: redact_url_for_log(match.group(0)),
        text,
    )

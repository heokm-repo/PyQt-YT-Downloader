"""Cryptographic integrity checks for downloaded release artifacts."""

from __future__ import annotations

import hashlib
import hmac
import re

from utils.logger import log


SHA256_DIGEST_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def normalize_sha256_digest(expected_digest: str | None) -> str | None:
    """Normalize GitHub's ``sha256:<hex>`` digest representation."""
    value = str(expected_digest or "").strip()
    if value.lower().startswith("sha256:"):
        value = value.split(":", 1)[1]
    if not SHA256_DIGEST_PATTERN.fullmatch(value):
        return None
    return value.lower()


def calculate_sha256(file_path: str) -> str:
    """Calculate a file's SHA-256 digest without loading it all into memory."""
    digest = hashlib.sha256()
    with open(file_path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(file_path: str, expected_digest: str | None) -> bool:
    """Verify a file against a trusted SHA-256 digest, failing closed if absent."""
    expected = normalize_sha256_digest(expected_digest)
    if not expected:
        log.error("Missing or invalid trusted SHA-256 digest; refusing downloaded file")
        return False

    try:
        actual = calculate_sha256(file_path)
    except OSError as exc:
        log.error(f"Failed to calculate downloaded file digest: {exc}")
        return False

    if not hmac.compare_digest(actual, expected):
        log.error(
            "Downloaded file SHA-256 mismatch "
            f"(expected={expected}, actual={actual})"
        )
        return False
    return True

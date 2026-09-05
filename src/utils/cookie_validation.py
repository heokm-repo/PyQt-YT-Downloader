"""Validate exported cookies without logging their contents or changing the file."""

import os
import re

from utils.logger import log


def _validate_cookie_file(path: str) -> bool:
    """Accept readable UTF-8 Netscape files containing at least one cookie."""
    try:
        with open(path, encoding="utf-8") as stream:
            if not re.match(r"#( Netscape)? HTTP Cookie File", stream.readline()):
                return False
            count = 0
            for line in stream:
                if line.startswith("#HttpOnly_"):
                    line = line[len("#HttpOnly_"):]
                elif line.startswith("#") or not line.strip():
                    continue
                fields = line.rstrip("\r\n").split("\t")
                if len(fields) != 7:
                    return False
                domain, include_subdomains, _, secure, expires, _, _ = fields
                if not domain or include_subdomains not in ("TRUE", "FALSE"):
                    return False
                if domain.startswith(".") != (include_subdomains == "TRUE"):
                    return False
                if secure not in ("TRUE", "FALSE"):
                    return False
                if expires:
                    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", expires):
                        return False
                count += 1
            return count > 0
    except (UnicodeError, ValueError):
        return False


def is_usable_cookie_file(path: str, *, delete_invalid: bool = False) -> bool:
    """Optionally remove a confirmed invalid file, preserving unreadable files."""
    try:
        before = os.stat(path)
        if _validate_cookie_file(path):
            return True
        if delete_invalid and os.path.isfile(path):
            after = os.stat(path)
            signature = lambda st: (st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
            if signature(before) == signature(after):
                os.remove(path)
                log.warning("Removed empty or malformed saved cookie file")
    except OSError:
        # Missing, locked, or unreadable files must not prevent downloads.
        log.debug("Cookie file could not be read or removed")
    return False

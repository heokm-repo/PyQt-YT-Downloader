"""Build network requests for task thumbnails."""

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest


THUMBNAIL_USER_AGENT = (
    b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)


def build_thumbnail_request(thumbnail_url: str) -> QNetworkRequest:
    """Return a request with the headers expected by thumbnail hosts."""
    request = QNetworkRequest(QUrl(thumbnail_url))
    request.setRawHeader(b"User-Agent", THUMBNAIL_USER_AGENT)
    return request
"""Build network requests for task thumbnails."""

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest

from constants import HTTP_USER_AGENT_HEADER, THUMBNAIL_USER_AGENT


def build_thumbnail_request(thumbnail_url: str) -> QNetworkRequest:
    """Return a request with the headers expected by thumbnail hosts."""
    request = QNetworkRequest(QUrl(thumbnail_url))
    request.setRawHeader(HTTP_USER_AGENT_HEADER, THUMBNAIL_USER_AGENT)
    return request
"""GUI-thread thumbnail requests shared by the cards of one window."""
from dataclasses import dataclass, field
from itertools import count
import weakref

from PyQt5 import sip
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply

from gui.tasks.task_thumbnail_request import build_thumbnail_request
from resources.styles import THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT
from utils.logger import log


@dataclass
class _Request:
    url: str
    reply: object
    tokens: set = field(default_factory=set)


class ThumbnailLoader(QObject):
    """Share in-flight work only; receivers implement on_thumbnail_loaded(token, pixmap).

    All methods run on the GUI thread. Weak receivers and removable destroyed
    connections keep neither removed cards nor completed subscriptions alive.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self._finished)
        self._requests = {}
        self._replies = {}
        self._subscriptions = {}
        self._owners = weakref.WeakKeyDictionary()
        self._tokens = count(1)
        self.closed = False
        if parent is not None:
            parent.destroyed.connect(self.close)

    def subscribe(self, url, receiver):
        if self.closed:
            return None
        self.cancel_owner(receiver)
        request = self._requests.get(url)
        if request is None:
            reply = self.manager.get(build_thumbnail_request(url))
            request = _Request(url, reply)
            self._requests[url] = request
            self._replies[reply] = request
        token = next(self._tokens)
        loader_ref = weakref.ref(self)

        def destroyed(*_):
            loader = loader_ref()
            if loader is not None and not sip.isdeleted(loader):
                loader.cancel(token)

        self._subscriptions[token] = (request, weakref.ref(receiver, destroyed), destroyed)
        self._owners[receiver] = token
        request.tokens.add(token)
        receiver.destroyed.connect(destroyed)
        return token

    def _detach(self, token):
        subscription = self._subscriptions.pop(token, None)
        if subscription is None:
            return None
        request, receiver_ref, destroyed = subscription
        request.tokens.discard(token)
        receiver = receiver_ref()
        if receiver is not None:
            if self._owners.get(receiver) == token:
                del self._owners[receiver]
            if not sip.isdeleted(receiver):
                receiver.destroyed.disconnect(destroyed)
                return receiver
        return None

    def cancel_owner(self, receiver):
        token = self._owners.get(receiver)
        if token is not None:
            self.cancel(token)

    def cancel(self, token):
        subscription = self._subscriptions.get(token)
        if subscription is None:
            return
        request = subscription[0]
        self._detach(token)
        if not request.tokens and self._replies.pop(request.reply, None) is not None:
            self._requests.pop(request.url, None)
            # Remove ownership before abort: Qt may emit finished synchronously.
            try:
                request.reply.abort()
            finally:
                request.reply.deleteLater()

    @staticmethod
    def _decode(data):
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return None
        return pixmap.scaled(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
                             Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    def _finished(self, reply):
        request = self._replies.pop(reply, None)
        if request is None:
            return  # Cancellation already scheduled disposal.
        self._requests.pop(request.url, None)
        try:
            pixmap = None
            if reply.error() == QNetworkReply.NoError:
                try:
                    pixmap = self._decode(reply.readAll())
                except Exception:
                    log.warning('Thumbnail decode failed', exc_info=True)
            for token in tuple(request.tokens):
                receiver = self._detach(token)
                if receiver is not None and not self.closed:
                    try:
                        receiver.on_thumbnail_loaded(token, pixmap)
                    except Exception:
                        log.warning('Thumbnail receiver failed', exc_info=True)
        finally:
            reply.deleteLater()

    def close(self, *_):
        self.closed = True
        for token in tuple(self._subscriptions):
            self.cancel(token)

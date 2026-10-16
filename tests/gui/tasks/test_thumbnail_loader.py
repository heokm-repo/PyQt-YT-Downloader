"""Request races and QObject lifetime contracts, without external network access."""
from unittest.mock import Mock, patch
import weakref

import pytest
from PyQt5 import sip
from PyQt5.QtCore import QByteArray, QBuffer, QCoreApplication, QEvent, QIODevice, QObject, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QColor, QPixmap
from PyQt5.QtNetwork import QNetworkReply
from PyQt5.QtWidgets import QApplication

from gui.tasks import thumbnail_loader as module
from gui.widgets.task_item import TaskWidget
from gui.tasks.task_widget_restore import create_restored_task_widget
from gui.tasks.task_registration import register_download_task
from data.task_collection import TaskCollection
from data.models import DownloadTask
from locales.strings import STR


def image_data(color='red', width=320, height=180):
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(QColor(color))
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG')
    return data


class Reply(QObject):
    def __init__(self, manager):
        super().__init__(manager)
        self.manager = manager
        self.aborts = self.deletions = 0
        self.data = image_data()
        self.error_code = QNetworkReply.NoError

    def abort(self):
        self.aborts += 1
        self.error_code = QNetworkReply.OperationCanceledError
        self.manager.finished.emit(self)  # Deliberately synchronous/reentrant.

    def deleteLater(self):
        self.deletions += 1
        super().deleteLater()

    def error(self):
        return self.error_code

    def readAll(self):
        return self.data


class Manager(QObject):
    finished = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self.requests = []

    def get(self, request):
        reply = Reply(self)
        self.requests.append((request, reply))
        return reply


class Receiver(QObject):
    def __init__(self):
        super().__init__()
        self.results = []

    def on_thumbnail_loaded(self, token, pixmap):
        self.results.append((token, pixmap))


@pytest.fixture
def loader(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(module, 'QNetworkAccessManager', Manager)
    service = module.ThumbnailLoader()
    yield service
    service.close()
    service.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


def test_shared_url_decodes_once_and_disconnects_completed_receivers(loader, monkeypatch):
    receivers = [Receiver() for _ in range(100)]
    connections_before = [r.receivers(r.destroyed) for r in receivers]
    decode = Mock(wraps=loader._decode)
    monkeypatch.setattr(loader, '_decode', decode)
    tokens = [loader.subscribe('https://example.invalid/a', r) for r in receivers]
    assert len(loader.manager.requests) == 1
    request, reply = loader.manager.requests[0]
    assert request.rawHeader(b'User-Agent')
    loader.manager.finished.emit(reply)
    assert decode.call_count == 1
    assert [r.results[0][0] for r in receivers] == tokens
    assert all(r.results[0][1].size().width() == 160 for r in receivers)
    assert not loader._requests and not loader._subscriptions and not loader._owners
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert [r.receivers(r.destroyed) for r in receivers] == connections_before
    assert reply.deletions == 1


def test_cancel_one_subscriber_preserves_other_and_last_cancel_aborts_once(loader):
    first, second = Receiver(), Receiver()
    a, b = loader.subscribe('a', first), loader.subscribe('a', second)
    reply = loader.manager.requests[0][1]
    loader.cancel(a)
    assert reply.aborts == 0
    loader.cancel(b)
    loader.cancel(b)
    assert reply.aborts == reply.deletions == 1
    assert not first.results and not second.results
    assert not loader._subscriptions and not loader._requests and not loader._replies


def test_cancelled_url_can_be_requested_again_and_late_completion_is_ignored(loader):
    receiver = Receiver()
    loader.cancel(loader.subscribe('a', receiver))
    old = loader.manager.requests[0][1]
    current = loader.subscribe('a', receiver)
    loader.manager.finished.emit(old)
    loader.manager.finished.emit(loader.manager.requests[1][1])
    assert [token for token, _ in receiver.results] == [current]
    assert old.deletions == 1


@pytest.mark.parametrize('failure', ['network', 'invalid', 'decode_exception'])
def test_failure_notifies_all_and_allows_retry(loader, monkeypatch, failure):
    receivers = [Receiver(), Receiver()]
    for receiver in receivers:
        loader.subscribe('bad', receiver)
    reply = loader.manager.requests[0][1]
    if failure == 'network':
        reply.error_code = QNetworkReply.ContentNotFoundError
    elif failure == 'invalid':
        reply.data = QByteArray(b'not an image')
    else:
        monkeypatch.setattr(loader, '_decode', Mock(side_effect=ValueError('decode')))
    loader.manager.finished.emit(reply)
    assert all(r.results[0][1] is None for r in receivers)
    assert reply.deletions == 1 and not loader._subscriptions
    loader.subscribe('bad', receivers[0])
    assert len(loader.manager.requests) == 2


def test_receiver_failure_does_not_prevent_delivery_or_disposal(loader):
    first, second = Receiver(), Receiver()
    first.on_thumbnail_loaded = Mock(side_effect=RuntimeError('receiver'))
    loader.subscribe('a', first)
    loader.subscribe('a', second)
    reply = loader.manager.requests[0][1]
    loader.manager.finished.emit(reply)
    assert len(second.results) == 1 and reply.deletions == 1
    assert not loader._subscriptions


def test_destroyed_card_unsubscribes_without_affecting_live_card(loader):
    first, second = Receiver(), Receiver()
    loader.subscribe('a', first)
    loader.subscribe('a', second)
    first.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert sip.isdeleted(first)
    reply = loader.manager.requests[0][1]
    assert reply.aborts == 0 and len(loader._subscriptions) == 1
    loader.manager.finished.emit(reply)
    assert not first.results and len(second.results) == 1


def test_python_receiver_collection_cancels_without_retention(loader):
    receiver = Receiver()
    ref = weakref.ref(receiver)
    loader.subscribe('a', receiver)
    del receiver
    assert ref() is None
    assert not loader._subscriptions
    assert loader.manager.requests[0][1].aborts == 1


def test_close_cancels_all_urls_and_rejects_new_work(loader):
    receivers = [Receiver() for _ in range(4)]
    for index, receiver in enumerate(receivers):
        loader.subscribe(str(index % 2), receiver)
    loader.close()
    loader.close()
    assert all(reply.aborts == reply.deletions == 1 for _, reply in loader.manager.requests)
    assert not loader._subscriptions and not loader._owners and not loader._requests
    assert loader.subscribe('new', receivers[0]) is None
    assert all(not r.results for r in receivers)


def test_parent_destruction_cleans_live_requests(loader):
    parent = QObject()
    service = module.ThumbnailLoader(parent)
    receiver = Receiver()
    service.subscribe('a', receiver)
    reply = service.manager.requests[0][1]
    parent.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert service.closed and sip.isdeleted(service)
    assert reply.aborts == 1 and not receiver.results


def test_completion_callback_can_cancel_another_subscriber(loader):
    first, second = Receiver(), Receiver()
    loader.subscribe('a', first)
    loader.subscribe('a', second)
    first.on_thumbnail_loaded = lambda *_: loader.close()
    loader.manager.finished.emit(loader.manager.requests[0][1])
    assert not second.results and not loader._subscriptions


def test_widget_reversed_responses_repeated_metadata_and_missing_url(loader):
    widget = TaskWidget(1, 'video', {}, thumbnail_loader=loader)
    keeper = Receiver()
    try:
        widget.update_metadata({'thumbnail': 'old'})
        old_token = widget._thumbnail_token
        loader.subscribe('old', keeper)
        old_reply = loader.manager.requests[0][1]
        widget.update_metadata({'thumbnail': 'new'})
        widget.update_metadata({'thumbnail': 'new', 'title': 'latest title'})
        assert len(loader.manager.requests) == 2 and old_reply.aborts == 0
        new_reply = loader.manager.requests[1][1]
        new_reply.data = image_data('blue')
        loader.manager.finished.emit(new_reply)
        with patch.object(loader, 'subscribe', wraps=loader.subscribe) as subscribe:
            widget.update_metadata({'thumbnail': 'new', 'title': 'completed item'})
            subscribe.assert_not_called()
        loader.manager.finished.emit(old_reply)
        widget.on_thumbnail_loaded(old_token, QPixmap())
        assert widget.thumb_label.pixmap().toImage().pixelColor(0, 0) == QColor('blue')
        widget.update_metadata({})
        assert widget.thumb_label.text() == STR.STATUS_NO_IMAGE
        assert not widget.thumb_label.pixmap() or widget.thumb_label.pixmap().isNull()
    finally:
        widget.deleteLater()


@pytest.mark.parametrize('width,height', [(400, 100), (100, 400), (100, 100)])
def test_existing_display_scaling_is_preserved(loader, width, height):
    widget = TaskWidget(1, '', {}, thumbnail_loader=loader)
    try:
        widget.update_metadata({'thumbnail': 'wide'})
        reply = loader.manager.requests[0][1]
        reply.data = image_data(width=width, height=height)
        expected = QPixmap()
        assert expected.loadFromData(reply.data)
        expected = expected.scaled(160, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        loader.manager.finished.emit(reply)
        assert widget.thumb_label.pixmap().toImage() == expected.toImage()
        assert widget.thumb_label.size().width() == 160
        assert widget.thumb_label.size().height() == 90
    finally:
        widget.deleteLater()


def test_registration_and_restore_inject_same_loader_before_metadata(loader):
    tasks, widgets = TaskCollection(), {}
    layout, scheduler = Mock(), Mock()
    task = register_download_task(1, '', {}, None, layout, widgets, lambda _: None,
                                  tasks, scheduler, thumbnail_loader=loader)
    restored = DownloadTask(2, '', meta={'thumbnail': 'saved'})
    widget = create_restored_task_widget(restored, None, layout, widgets, lambda _: None,
                                        thumbnail_loader=loader)
    try:
        assert widgets[1].thumbnail_loader is widget.thumbnail_loader is loader
        assert task is tasks.get(1)
        assert widget._thumbnail_token in loader._subscriptions
        scheduler.add_task.assert_called_once()
    finally:
        for card in widgets.values():
            card.deleteLater()


def test_repeated_completion_releases_subscriptions_without_completed_cache(loader):
    receiver = Receiver()
    connections_before = receiver.receivers(receiver.destroyed)
    for _ in range(30):
        loader.subscribe('same', receiver)
        loader.manager.finished.emit(loader.manager.requests[-1][1])
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        assert not loader._requests and not loader._owners and not loader._subscriptions
        assert receiver.receivers(receiver.destroyed) == connections_before
    assert len(loader.manager.requests) == len(receiver.results) == 30

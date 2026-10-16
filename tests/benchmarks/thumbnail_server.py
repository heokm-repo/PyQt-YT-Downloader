"""Loopback-only HTTP fixture with responses explicitly released by the benchmark."""
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QColor, QImage
from PyQt5.QtNetwork import QHostAddress, QTcpServer


def thumbnail_png():
    image = QImage(1280, 720, QImage.Format_RGB32)
    image.fill(QColor('#7040a0'))
    for x in range(1280):
        for y in range(0, 720, 40):
            image.setPixelColor(x, y, QColor('#f0c030'))
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    assert image.save(buffer, 'PNG')
    return bytes(data)


class ThumbnailServer(QTcpServer):
    def __init__(self):
        super().__init__()
        self.body = thumbnail_png()
        self.requests = []
        self.sockets = []
        self.buffers = {}
        self.released = False
        self.payload_bytes = 0
        self.newConnection.connect(self._accept)
        if not self.listen(QHostAddress.LocalHost, 0):
            raise RuntimeError(self.errorString())

    def _accept(self):
        while self.hasPendingConnections():
            socket = self.nextPendingConnection()
            self.sockets.append(socket)
            self.buffers[socket] = b''
            socket.readyRead.connect(lambda socket=socket: self._read(socket))

    def _read(self, socket):
        self.buffers[socket] += bytes(socket.readAll())
        if b'\r\n\r\n' in self.buffers[socket]:
            header = self.buffers.pop(socket)
            self.requests.append(header.split(b'\r\n', 1)[0].decode('ascii'))
            if self.released:
                self._respond(socket)

    def _respond(self, socket):
        if socket.state() != socket.ConnectedState:
            return
        header = ('HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n'
                  f'Content-Length: {len(self.body)}\r\nConnection: close\r\n\r\n').encode('ascii')
        if socket.write(header + self.body) >= 0:
            self.payload_bytes += len(self.body)
        socket.disconnectFromHost()

    def release(self):
        self.released = True
        for socket in self.sockets:
            if socket not in self.buffers:
                self._respond(socket)

    def dispose(self):
        self.close()
        for socket in self.sockets:
            socket.abort()
        self.deleteLater()

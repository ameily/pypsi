
from PySide import QtGui, QtCore
from pypsi.remote.session import RemotePypsiSession, ConnectionClosed
from pypsi.remote import protocol as proto
from pypsi.gui.widgets import TerminalWidget, NewSessionWidget
import socket


class ClientWidget(QtGui.QWidget):
    titleChanged = QtCore.Signal((QtGui.QWidget, str))
    connected = QtCore.Signal(QtGui.QWidget)
    disconnected = QtCore.Signal(QtGui.QWidget)

    def __init__(self, theme, *args, **kwargs):
        super(ClientWidget, self).__init__(*args, **kwargs)
        self.theme = theme
        self.layout = QtGui.QVBoxLayout(self)
        self.session = NewSessionWidget(self)
        self.layout.addWidget(self.session)
        self.session.triggered.connect(self.on_session_triggered)
        self.session.ui.server.setFocus()
        self.client = None

    def init_session(self):
        print("init_session()")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            self.socket.connect((self.session.server, self.session.port))
        except:
            import traceback
            print(traceback.format_exc())
            return False
        else:
            self.client = RemotePypsiSession(self.socket)
            return True

    @QtCore.Slot()
    def on_session_triggered(self):
        if self.init_session():
            self.layout.removeWidget(self.session)
            self.session.deleteLater()
            self.terminal = TerminalWidget(self.theme, self)
            self.layout.addWidget(self.terminal)
            self.setWindowTitle("Terminal")
            self.terminal.post.connect(self.on_terminal_post)
            self.connected.emit(self)
            self.terminal.ui.stdin.setFocus()

    @QtCore.Slot()
    def poll(self):
        if self.client:
            try:
                msg = self.client.recvmsg(block=False)
            except ConnectionClosed:
                self.disconnected.emit(self)
                self.terminal.setEnabled(False)
            else:
                if msg:
                    self.handle(msg)

    @QtCore.Slot(str, str)
    def on_terminal_post(self, input, sig):
        if self.client:
            msg = proto.InputResponse(input, sig)
            try:
                self.client.sendmsg(msg)
            except:
                self.disconnected.emit(self)
                self.terminal.setEnabled(False)

    def handle(self, msg):
        if isinstance(msg, proto.InputRequest):
            self.terminal.set_prompt(msg.prompt)
        elif isinstance(msg, proto.ShellOutputResponse):
            self.terminal.append(msg.output)

    def setWindowTitle(self, s):
        super(ClientWidget, self).setWindowTitle(s)
        self.titleChanged.emit(self, s)

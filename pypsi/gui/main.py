
from pypsi.gui.ui import Ui_ClientMainWindow
from pypsi.gui.widgets import ClientWidget
from PySide import QtGui, QtCore
from pypsi.gui.theme import GuiTheme


class ClientMainWindow(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(ClientMainWindow, self).__init__(*args, **kwargs)
        self.ui = Ui_ClientMainWindow()
        self.ui.setupUi(self)

        self.ui.actionNewTab.setIcon(QtGui.QIcon.fromTheme("tab-new"))
        self.ui.actionExit.setIcon(QtGui.QIcon.fromTheme("application-exit"))
        self.connections = []
        self.timer = None
        self.theme = GuiTheme.from_builtin("Nightman")
        QtGui.QApplication.instance().setStyleSheet(self.theme.widgets)
        self.on_actionNewTab_triggered()

    @QtCore.Slot()
    def on_actionNewTab_triggered(self):
        w = ClientWidget(self.theme, self)
        w.titleChanged.connect(self.on_tab_titleChanged)
        w.connected.connect(self.on_client_connected)
        w.disconnected.connect(self.on_client_disconnected)
        index = self.ui.tabWidget.addTab(w, "New Session")
        self.ui.tabWidget.setCurrentIndex(index)
        w.session.ui.server.setFocus()

    @QtCore.Slot()
    def on_actionExit_triggered(self):
        self.close()

    @QtCore.Slot(int)
    def on_tabWidget_tabCloseRequested(self, index):
        self.ui.tabWidget.removeTab(index)

    @QtCore.Slot(QtGui.QWidget, str)
    def on_tab_titleChanged(self, w, t):
        index = self.ui.tabWidget.indexOf(w)
        if index >= 0:
            self.ui.tabWidget.setTabText(index, t)

    @QtCore.Slot()
    def on_client_connected(self, widget):
        self.connections.append(widget)
        if not self.timer:
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.on_poll_timeout)
            self.timer.start(10)

    @QtCore.Slot()
    def on_poll_timeout(self):
        for c in self.connections:
            c.poll()

    @QtCore.Slot()
    def on_client_disconnected(self, widget):
        self.connections.remove(widget)
        widget.setEnabled(False)
        if not self.connections:
            self.timer.stop()
            del self.timer
            self.timer = None

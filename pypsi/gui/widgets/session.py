
from pypsi.gui.ui.session import Ui_NewSessionWidget
from PySide import QtGui, QtCore


class NewSessionWidget(QtGui.QWidget):
    triggered = QtCore.Signal()
    server_re = QtCore.QRegExp(r'(?:^\d+\.\d+\.\d+\.\d+)|(?:[a-zA-Z][a-zA-Z0-9._\-]*)$')

    def __init__(self, *args, **kwargs):
        super(NewSessionWidget, self).__init__(*args, **kwargs)
        self.ui = Ui_NewSessionWidget()
        self.ui.setupUi(self)
        self.ui.server.setValidator(QtGui.QRegExpValidator(self.server_re))
        self.ui.server.returnPressed.connect(self.on_connectButton_clicked)
        self.ui.port.installEventFilter(self)

        self.ui.connectButton.setIcon(QtGui.QIcon.fromTheme("dialog-ok-apply"))
        self.ui.resetButton.setIcon(QtGui.QIcon.fromTheme("document-revert"))
        self.ui.connectButton.setEnabled(False)

    @QtCore.Slot(str)
    def on_server_textChanged(self, text):
        self.ui.connectButton.setEnabled(True if text.strip() else False)

    @QtCore.Slot()
    def on_resetButton_clicked(self):
        self.ui.server.clear()
        self.ui.port.setValue(9001)
        self.ui.server.setFocus()

    @QtCore.Slot()
    def on_connectButton_clicked(self):
        self.server = self.ui.server.text()
        self.port = self.ui.port.value()
        self.triggered.emit()

    def eventFilter(self, obj, event):
        if obj == self.ui.port:
            if event.type() == QtCore.QEvent.KeyPress \
                    and event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter) \
                    and self.ui.connectButton.isEnabled():
                self.on_connectButton_clicked()
                return True
        return super(NewSessionWidget, self).eventFilter(obj, event)

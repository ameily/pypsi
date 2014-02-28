
from PySide import QtGui, QtCore

class StdinWidget(QtGui.QLineEdit):
    sigint = QtCore.Signal()
    sigeof = QtCore.Signal()
    scrollLine = QtCore.Signal(int)
    scrollPage = QtCore.Signal(int)

    def __init__(self, *args , **kwargs):
        super(StdinWidget, self).__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        parent = True
        ctrl = event.modifiers() & QtCore.Qt.ControlModifier
        shift = event.modifiers() & QtCore.Qt.ShiftModifier
        if ctrl:
            rem = event.modifiers() ^ ctrl
            if event.key() == QtCore.Qt.Key_C:
                if not self.hasSelectedText() or rem == QtCore.Qt.ShiftModifier:
                    self.sigint.emit()
                    parent = False
            elif event.key() == QtCore.Qt.Key_D and not rem:
                self.sigeof.emit()
                parent = False
        elif shift:
            rem = event.modifiers() ^ shift
            if not rem:
                if event.key() == QtCore.Qt.Key_Up:
                    self.scrollLine.emit(1)
                    parent = False
                elif event.key() == QtCore.Qt.Key_Down:
                    self.scrollLine.emit(-1)
                    parent = False
                elif event.key() == QtCore.Qt.Key_PageUp:
                    self.scrollPage.emit(1)
                    parent = False
                elif event.key() == QtCore.Qt.Key_PageDown:
                    self.scrollPage.emit(-1)
                    parent = False

        if parent:
            super(StdinWidget, self).keyPressEvent(event)

    # tab = complete
    # up = history
    # shift+up = move up one line
    # shit+page_up = move up a page

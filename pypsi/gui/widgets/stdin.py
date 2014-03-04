
from PySide import QtGui, QtCore

class StdinWidget(QtGui.QLineEdit):
    sigint = QtCore.Signal()
    sigeof = QtCore.Signal()
    scrollLine = QtCore.Signal(int)
    scrollPage = QtCore.Signal(int)

    def __init__(self, *args , **kwargs):
        super(StdinWidget, self).__init__(*args, **kwargs)
        self.history = []
        self.hist_pos = -1
        self.tmp_hist = ''

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
        elif not event.modifiers():
            if event.key() == QtCore.Qt.Key_Up:
                self.move_history(-1)
            elif event.key() == QtCore.Qt.Key_Down:
                self.move_history(1)

        if parent:
            super(StdinWidget, self).keyPressEvent(event)

    def submit(self, sig):
        if not sig:
            item = self.text()
            if not self.history or item != self.history[-1]:
                self.history.append(item)
        self.clear()
        self.hist_pos = None

    def move_history(self, direction):
        print("move_history(", direction, ") ==", self.hist_pos)
        if not self.history:
            print(">> hist is null")
            return

        if self.hist_pos is None:
            if direction > 0:
                #self.hist_pos = 0
                self.setText(self.tmp_hist)
                return
            else:
                self.hist_pos = len(self.history) - 1
        else:
            self.hist_pos += direction

        if self.hist_pos < 0:
            #print("hist_pos == -1")
            #self.clear()
            self.hist_pos = 0
            #return

        if self.hist_pos >= len(self.history):
            print("hist_pos >= len()")
            #self.hist_pos = len(self.history) - 1
            self.hist_pos = None
            self.setText(self.tmp_hist)
            self.clear()
            return

        print("hist_pos ==", self.hist_pos)
        #TODO tmp_hist
        self.setText(self.history[self.hist_pos])
        self.setCursorPosition(len(self.text()))

    # tab = complete
    # up = history
    # shift+up = move up one line
    # shit+page_up = move up a page

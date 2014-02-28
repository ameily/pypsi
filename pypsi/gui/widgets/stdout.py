

from PySide import QtGui, QtCore
from pypsi.gui.ansi import AnsiDecoder, TextStyle


class StdoutWidget(QtGui.QTextEdit):
    forwardKey = QtCore.Signal(QtGui.QKeyEvent)

    def __init__(self, *args, **kwargs):
        super(StdoutWidget, self).__init__(*args, **kwargs)
        self.setReadOnly(True)
        metrics = QtGui.QFontMetrics(self.currentFont())
        self.setTabStopWidth(4 * metrics.width(' '))
        self.decoder = AnsiDecoder()
        #self.document().setDefaultStyleSheet(DefaultStyle)
        self.current_style = TextStyle()

    @QtCore.Slot()
    def appendAnsi(self, txt):
        #self.insertPlainText(txt)
        self.moveCursor(QtGui.QTextCursor.End)
        for (html, style) in self.decoder.html(txt, self.current_style, 'stdout-text'):
            self.insertHtml(html)
            self.current_style = style
            #self.current_style = p.style
        self.ensureCursorVisible()

    @QtCore.Slot()
    def appendHtml(self, html):
        self.moveCursor(QtGui.QTextCursor.End)
        self.insertHtml(html)
        self.ensureCursorVisible()

    #TODO keypress -> set focus on stdin
    def keyPressEvent(self, event):
        print("stdout::keyPressEvent()")
        shift = QtCore.Qt.ShiftModifier
        if event.text() and event.modifiers() in (0, shift):
            self.forwardKey.emit(event)
        else:
            super(StdoutWidget, self).keyPressEvent(event)

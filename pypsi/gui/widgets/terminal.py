
from pypsi.gui.ui.terminal import Ui_TerminalWidget
from PySide import QtGui, QtCore
from pypsi.remote import protocol as proto
from pypsi.gui.ansi import AnsiDecoder, TextStyle


class TerminalWidget(QtGui.QWidget):
    post = QtCore.Signal((str, str))
    complete = QtCore.Signal(str)

    def __init__(self, theme, *args, **kwargs):
        super(TerminalWidget, self).__init__(*args, **kwargs)
        self.ui = Ui_TerminalWidget()
        self.ui.setupUi(self)
        self.decoder = AnsiDecoder()
        self.theme = theme
        self.ui.stdout.document().setDefaultStyleSheet(self.theme.term)
        self.ui.prompt.setText("<html></html>")
        self.ui.prompt.findChild(QtGui.QTextDocument).setDefaultStyleSheet(self.theme.term)

    @QtCore.Slot()
    def on_stdin_returnPressed(self):
        self.fire_post()

    @QtCore.Slot()
    def on_stdin_sigint(self):
        self.fire_post('int')

    @QtCore.Slot()
    def on_stdin_sigeof(self):
        self.fire_post('eof')

    @QtCore.Slot()
    def on_stdin_complete(self):
        txt = self.stdin.text()
        index = self.stdin.cursorPosition()
        self.complete.emit(txt[:index])

    @QtCore.Slot()
    def set_completions(self, completions):
        pass

    @QtCore.Slot()
    def append(self, txt):
        self.ui.stdout.appendAnsi(txt)

    @QtCore.Slot()
    def set_prompt(self, prompt):
        html = "<span class='prompt'>"
        for (e, style) in self.decoder.html(prompt, TextStyle(), ""):
            html += e
        html += "</span>"
        self.ui.prompt.setText(html)
        #self.ui.prompt.setStyleSheet(".fg-intense-32 { color: rgb(0,255,0); }")
        #self.ui.prompt.setText(self.decoder.html(prompt, TextStyle(), "prompt"))
        #self.ui.prompt.setText()

    @QtCore.Slot(QtGui.QKeyEvent)
    def on_stdout_forwardKey(self, event):
        self.ui.stdin.setFocus()
        self.ui.stdin.keyPressEvent(event)

    @QtCore.Slot(int)
    def on_stdin_scrollLine(self, direction):
        vbar = self.ui.stdout.verticalScrollBar()
        if vbar:
            vbar.triggerAction(
                QtGui.QAbstractSlider.SliderSingleStepAdd if direction < 0 else
                QtGui.QAbstractSlider.SliderSingleStepSub
            )

    @QtCore.Slot(int)
    def on_stdin_scrollPage(self, direction):
        vbar = self.ui.stdout.verticalScrollBar()
        if vbar:
            vbar.triggerAction(
                QtGui.QAbstractSlider.SliderPageStepAdd if direction < 0 else
                QtGui.QAbstractSlider.SliderPageStepSub
            )

    def fire_post(self, sig=None):
        txt = self.ui.stdin.text()
        #self.append(self.ui.prompt.text() + " " + txt + "\n")
        self.ui.stdout.appendHtml(self.ui.prompt.text())
        #self.ui.stdout.appendText(txt)
        self.ui.stdout.appendAnsi(txt+"\n")
        self.ui.stdin.clear()
        self.post.emit(txt, sig)

    #TODO keypress -> set focus on stdin

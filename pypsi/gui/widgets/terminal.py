#
# Copyright (c) 2014, Adam Meily
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

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
        if sig == 'int':
            txt += '^C'
        elif sig == 'eof':
            txt += '^D'
        self.ui.stdin.submit(sig)
        self.ui.stdout.appendHtml(self.ui.prompt.text())
        self.ui.stdout.appendAnsi(txt+"\n")
        self.post.emit(txt, sig)

    #TODO keypress -> set focus on stdin

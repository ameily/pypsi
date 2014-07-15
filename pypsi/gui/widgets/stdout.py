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

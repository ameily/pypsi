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

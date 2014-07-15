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

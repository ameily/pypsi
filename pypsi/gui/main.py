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

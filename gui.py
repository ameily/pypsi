
if __name__ == '__main__':
    from PySide import QtGui
    from pypsi.gui.main import ClientMainWindow
    import sys

    app = QtGui.QApplication(sys.argv)

    #fp = open("pypsi/gui/themes/nightman.css", 'r')
    #app.setStyleSheet(fp.read())
    #print(app.styleSheet())
    #fp.close()

    window = ClientMainWindow()
    window.show()
    #window.run()
    sys.exit(app.exec_())


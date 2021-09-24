import requests, json,sys
import yt_down_dialog

from PyQt5.QtWidgets import  QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    Interface = yt_down_dialog.YtDownloaderGUI()
    Interface.show()
    sys.exit(app.exec_())


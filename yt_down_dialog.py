from PyQt5.uic import loadUi
import requests, os
# Third part imports
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import \
    QDialog, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QMovie
import time
import threading
from pytube import YouTube
import json
from configparser import ConfigParser




class Download(QThread):

    finished = pyqtSignal()

    def __init__(self,parent=None):
        super(Download, self).__init__(parent)
        self.download_path = None
        self.yt_video = None
        self.video = None
        self.thumb_url = None
        self.title = None
        self.stream = None
        self.res = []
        self.abr = []
        self.itags = []
        self.download_folder = None
        self.download_tag = None
        self.dict_streams = []
        self.file_size = None
        self.file_name = None

    def run(self):
        self.stream.download(self.download_path)
        self.finished.emit()
  

    def stop(self):
        self._isRunning = False


class YtDownloaderGUI(QDialog):

    global X

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("yt-downloader-gui.ui", self)

        self.config = ConfigParser()
        self.config.read('config.INI')

        self.download_core = Download()
        self.download_core.download_path = self.config['DEFAULT']['download_path']

        #create downloadpath on first run
        try:
            os.mkdir(self.download_core.download_path)
        except:
            pass

        self.plainTextEdit_2.setPlainText(self.download_core.download_path)
        
        self.loadingMovie = QMovie("loading.gif")
        self.loaded_image = QImage("ok.png")

        self.downthread = QThread()
        # self.downthread.started.connect(self.download)
        self.downthread.finished.connect(self.SuccessMessage)

        # self.setAttribute(Qt.WA_DeleteOnClose)
        self.label_progess.hide()
        self.progressBar.hide()
        self.pushButton_3.hide()
        self.label_thumb.setScaledContents(True)
        self.label_loading.setScaledContents(True)
        self.comboBox.setCurrentIndex(-1)
        self.comboBox.setEnabled(False)
        self.comboBox_1.setEnabled(False)
        self.pushButton.setEnabled(False)
        
        self.plainTextEdit.textChanged.connect(self.find_yt_video)
        self.comboBox.currentTextChanged.connect(self.get_resolution_thread)
        self.comboBox_1.currentIndexChanged.connect(self.release_download_button)
        self.pushButton.clicked.connect(self.download_file)
        self.pushButton_2.clicked.connect(self.get_new_folder)
        self.pushButton_3.clicked.connect(self.stop_button)

        self.groupBox_2.hide()
        self.groupBox.hide()

    def get_new_folder(self):
        """Sets the new download path and automatically saves on ini file"""
        try:
            #get Folder
            folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
            self.plainTextEdit_2.setPlainText(folder)

            #update ini file
            self.config['DEFAULT']['download_path'] = folder
            with open('config.INI', 'w') as configfile:    # save
                self.config.write(configfile)
        except:
            pass



    def release_buttons_after_download(self):
        self.progressBar.setValue(0)
        self.comboBox.setCurrentIndex(-1)
        self.comboBox.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.label_progess.hide()
        self.progressBar.hide()
        self.pushButton_3.hide()

    def block_buttons_on_download(self):
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.comboBox.setEnabled(False)
        self.comboBox_1.setEnabled(False)
        self.label_progess.show()
        self.progressBar.show()
        self.pushButton_3.show()


    def SuccessMessage(self):
        mbox = QMessageBox()
        mbox.about(QMainWindow(), "Success", "Download Complete", QMessageBox.Ok)
        

    def download_file(self):

        self.download_core.download_folder = self.config['DEFAULT']['download_path']
        self.download_core.stream = self.download_core.video.streams.get_by_itag(self.download_core.download_tag)
        self.download_core.file_size = self.download_core.stream.filesize
        self.download_core.file_name = self.download_core.stream.default_filename

        try:
            os.remove(os.path.join(self.download_core.download_folder, self.download_core.file_name))
        except:
            pass

        self.download_core.start()
        down_progress_thread = threading.Thread(target=self.downloading_thread)
        down_progress_thread.start()
    
    def stop_button(self):
        #stop thread
        self.download_core.stop()
        #remove file
        try:
            os.remove(os.path.join(self.download_core.download_folder, self.download_core.file_name))
        except:
            pass
        #release buttons
        self.release_buttons_after_download()



    def downloading_thread(self):
        # global X
        self.block_buttons_on_download()
        # X = True
        while True:
            try:
                time.sleep(.01)
                currentsize = os.path.getsize(os.path.join(self.download_core.download_folder, self.download_core.file_name))
                download_percentage = currentsize/self.download_core.file_size * 100
                self.progressBar.setValue(download_percentage)
                
                if download_percentage >= 100:
                    self.release_buttons_after_download()
                    # X = False
                    break
            except:
                pass


    def release_download_button(self, val):
        if not val == -1:
            self.download_core.download_tag = self.download_core.itags[val]
            self.pushButton.setEnabled(True)
        else:
            self.pushButton.setEnabled(False)

    def convert_stream_to_dict(self, tag):

            tag = tag.replace("<Stream: ", "{\"")
            tag = tag.replace("\">", "\"}") 
            tag = tag.replace("=", "\":")
            tag = tag.replace("'", "\"")
            tag = tag.replace("\" ", "\",\"")
            d = json.loads(tag)
            return d

    def thread_audio_resolution(self):
        Streams = self.download_core.video.streams.filter(only_audio=True)
        self.download_core.dict_streams = []
        self.download_core.abr = []
        self.download_core.itags = []
        for i,s in enumerate(Streams):
            self.download_core.dict_streams.append(self.convert_stream_to_dict(str(s)))
            try:             
                self.download_core.abr.append(str(self.download_core.dict_streams[i]['abr']) + " " + str(self.download_core.dict_streams[i]['mime_type']) + " vcodec=" + str(self.download_core.dict_streams[i]['acodec']))
                self.download_core.itags.append(self.download_core.dict_streams[i]['itag'])
            except:
                pass
        
        self.comboBox_1.clear()
        self.comboBox_1.addItems(self.download_core.abr)
        self.comboBox_1.setEnabled(True)
        self.comboBox_1.setCurrentIndex(-1)
        self.label_loading.setPixmap(QPixmap(self.loaded_image))
        

    def thread_video_resolution(self):
        Streams = self.download_core.video.streams.filter(file_extension='mp4')
        self.download_core.dict_streams = []
        self.download_core.res = []
        self.download_core.itags = []
        for i,s in enumerate(Streams):
            self.download_core.dict_streams.append(self.convert_stream_to_dict(str(s)))
            try:
                self.download_core.res.append(str(self.download_core.dict_streams[i]['res']) + " " + str(self.download_core.dict_streams[i]['fps']) + " vcodec=" + str(self.download_core.dict_streams[i]['vcodec']))
                self.download_core.itags.append(self.download_core.dict_streams[i]['itag'])
            except:
                pass

        self.comboBox_1.clear()        
        self.comboBox_1.addItems(self.download_core.res)
        self.comboBox_1.setEnabled(True)
        self.comboBox_1.setCurrentIndex(-1)
        self.label_loading.setPixmap(QPixmap(self.loaded_image))
        


    def get_resolution(self, text):
        
        self.comboBox_1.setEnabled(False)

        self.label_loading.setMovie(self.loadingMovie)
        self.loadingMovie.start()

        if text == "Video":
            t = threading.Thread(target=self.thread_video_resolution)
            t.start()
        elif text == "Audio":
            t = threading.Thread(target=self.thread_audio_resolution)
            t.start()
        elif self.comboBox.currentIndex() == -1: 
            self.label_loading.setText(" ")

    def get_resolution_thread(self,text):
        t = threading.Thread(target=self.get_resolution(text))
        t.start()


    def find_yt_video(self):
        self.comboBox.setEnabled(False)
        self.comboBox_1.setEnabled(False)
        self.comboBox.setCurrentIndex(-1)
        self.download_core.yt_video = self.plainTextEdit.toPlainText()
        self.t1 = threading.Thread(target=self.get_yt_data)
        self.t1.start()
        
        

    def get_yt_data(self):
        try:
            
            self.download_core.video = YouTube(self.download_core.yt_video)
            self.download_core.thumb_url = self.download_core.video.thumbnail_url
            # print(self.thumb_url)
            self.download_core.title = self.download_core.video.title
            self.label_foundOrNot.setText("Video Found!")
            self.groupBox_2.show()
            self.groupBox.show()
            self.comboBox.setCurrentIndex(-1)
            self.comboBox.setEnabled(True)
            
            self.t2 = threading.Thread(target=self.update_video_label)
            self.t2.start()
        except:
            self.label_foundOrNot.setText("Video Not Found!")
            self.groupBox_2.hide()
            self.groupBox.hide()

    def update_video_label(self):
        #update thumb image
        image = QImage()
        image.loadFromData(requests.get(self.download_core.thumb_url).content)
        self.label_thumb.setPixmap(QPixmap(image))
        
        #update video text
        self.label_title.setText(self.download_core.title)


    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F11:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()



if __name__ == "main":
    pass
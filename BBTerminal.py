import requests
from PyQt5.QtWidgets import QMainWindow, QLabel, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase, QIcon
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QWidget, QLineEdit, QTextEdit, QPushButton
from configparser import ConfigParser
import os
import resource
import string
import random
from pygame import mixer

config_file = '''
[api]
API_BASE_URL=https://prescript.2dt0.de
UPDATE_API_BASE_URL=https://prescript.2dt0.de
'''

class PetConfig:
    def __init__(self,config_file_name = "config.ini"):
        self.config = ConfigParser()
        if os.path.exists(config_file_name):
            self.config.read(config_file_name)
            self.api_base_url = self.config.get("api","API_BASE_URL")
            self.update_api_base_url = self.config.get("api","UPDATE_API_BASE_URL")
        else:
            raise FileNotFoundError("配置文件不存在")
    def dump(self):
        self.config.set("api","API_BASE_URL",self.api_base_url)
        self.config.set("api","UPDATE_API_BASE_URL",self.update_api_base_url)

def getPrescript(config : PetConfig):
    resp = requests.get(f"{config.api_base_url}/prescript")
    if not resp.ok:
        return ""
    data = resp.json()
    return data["data"]

class BBTerminal(QMainWindow):
    def __init__(self, parent = ..., flags = ...):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.pet_width = 501
        self.pet_height = 250
        self.screen_geometry = QApplication.desktop().availableGeometry()
        self.screen_width = self.screen_geometry.width()
        self.screen_height = self.screen_geometry.height()
        self.start_x = self.screen_width - 30 - self.pet_width
        self.start_y = self.screen_height - self.pet_height - 20
        self.setGeometry(self.start_x, self.start_y, self.pet_width, self.pet_height)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.pet_width, self.pet_height)
        self.setCentralWidget(self.label)
        try:
            self.config = PetConfig()
        except FileNotFoundError:
            resl = QMessageBox.critical(self,"错误","配置文件缺失，是否修补？",QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.Yes)
            if resl == QMessageBox.StandardButton.Yes:
                with open("config.ini","w",encoding="utf-8") as f:
                    f.write(config_file)
                QMessageBox.information(self,"完成","修补完成，即将退出",QMessageBox.StandardButton.Yes)
                exit(0)
            else:
                exit(1)
        self.refreshbutton = QPushButton(None,self)
        self.refreshbutton.setGeometry(398,115,32,32)
        self.refreshbutton.clicked.connect(self.refreshPrescript)
        self.loadImage()
        self.letters = string.ascii_letters + "!?<>@#$%^&*()"
        self.prescript = getPrescript(self.config)
        self.current_index = 0
        self.random_count = 0
        self.nowletter = []
        lenp = len(self.prescript)
        if lenp == 0:
            self.prescript = "致：好好休息。"
        else:
            self.prescript = "致：" + self.prescript
        mixer.init()
        if not os.path.exists("./audio/bb.wav"):
            QMessageBox.critical(None,"错误","音频文件缺失！")
        mixer.music.load("./audio/bb.wav")
        mixer.music.set_volume(1.5)
        self.timer = QTimer()
        self.timer.timeout.connect(self.initPrescript)
        self.timer.start(50)  # 每50ms触发一次
        mixer.music.play()
        self.prescriptlabel = QLabel(self)
        self.prescriptlabel.setGeometry(77,33,275,200)
        self.prescriptlabel.setText("致：好好休息。")
        self.prescriptlabel.setWordWrap(True)
        self.prescriptlabel.setFixedWidth(275)
        self.prescriptlabel.raise_()
        self.prescriptlabel.setStyleSheet("color: rgb(42, 158, 222)")
        fontDb = QFontDatabase()
        fontDb.addApplicationFont(":fonts/hypixel")
        self.setFont(QFont("HYPixel 11px U"))
        self.prescriptlabel.setFont(QFont("HYPixel 11px U", 13))
        self.setWindowIcon(QIcon(":images/icon"))

    def loadImage(self):
        self.bbimg = QPixmap(":images/terminal")
        self.refreshimg = QIcon(":images/refresh")
        self.settingimg = QPixmap(":images/setting")
        self.label.setPixmap(self.bbimg)
        self.refreshbutton.setIcon(self.refreshimg)
    
    def mousePressEvent(self, event):
        """鼠标按下时记录拖动起点"""
        if event.button() == Qt.LeftButton:  # 左键按下
            self.dragPos = event.globalPos()  # 记录全局坐标
            self.is_dragging = False  # 初始标记为未拖动（避免误判为点击）
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动时拖动窗口"""
        if event.buttons() == Qt.LeftButton:  # 左键按住并移动
            self.is_dragging = True  # 标记为拖动状态
            # 计算新位置：当前位置 + 鼠标移动距离
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()  # 更新拖动起点
            event.accept()
    
    def initPrescript(self):
        if self.current_index >= len(self.prescript):
            self.timer.stop()
            return
        
        if self.random_count < 2:  # 显示随机字母
            random_char = random.choice(self.letters)
            display_text = f"{''.join(self.nowletter)}{random_char}"
            self.random_count += 1
        else:  # 显示正确字符
            target_char = self.prescript[self.current_index]
            display_text = f"{''.join(self.nowletter)}{target_char}"
            self.nowletter.append(target_char)
            self.current_index += 1
            self.random_count = 0
        
        self.prescriptlabel.setText(display_text)

    def refreshPrescript(self):
        self.prescript = getPrescript(self.config)
        self.current_index = 0
        self.random_count = 0
        self.nowletter = []
        lenp = len(self.prescript)
        if lenp == 0:
            self.prescript = "致：好好休息。"
        else:
            self.prescript = "致：" + self.prescript
        mixer.music.play()
        self.timer.start(50)
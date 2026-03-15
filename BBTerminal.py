import requests
from PyQt5.QtWidgets import QMainWindow, QLabel, QApplication, QMessageBox, QLineEdit, QDoubleSpinBox, QPushButton
from PyQt5.QtCore import Qt, QTimer, QFile, QIODevice, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import QMenu, QAction, QDialog
from configparser import ConfigParser
import os
import resource
import string
import random
from pygame import mixer
import re

config_file = '''
[api]
API_BASE_URL=https://prescript.2dt0.de
[refresh]
REFRESH_TIME = 60
'''

class PetConfig:
    def __init__(self,config_file_name = "config.ini"):
        self.config = ConfigParser()
        self.config.read(config_file_name)
        self.api_base_url = self.config.get("api","API_BASE_URL")
        self.refresh_seconds = float(self.config.get("refresh","REFRESH_TIME"))
    def dump(self):
        self.config.set("api","API_BASE_URL",self.api_base_url)
        self.config.set("refresh","REFRESH_TIME",str(self.refresh_seconds))
        with open("config.ini","w") as f:
            self.config.write(f) 

def getPrescript(config : PetConfig):
    try:
        resp = requests.get(f"{config.api_base_url}/prescript")
    except Exception:
        return ""
    if not resp.ok:
        return ""
    data = resp.json()
    return data["data"]

class SettingMenu(QDialog):
    on_setting_save = pyqtSignal(PetConfig)
    def __init__(self, parent, flags = Qt.WindowType.Dialog):
        super().__init__(parent, flags)
        self.config = PetConfig()
        self.urlre = re.compile(r'^(https?://)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*/?$')
        self.setGeometry(500,500,300,200)
        self.setWindowTitle('指令 【设置】')
        self.apilabel = QLabel('API设置（只填域名）',self)
        self.apilabel.setGeometry(18,20,500,15)
        self.apiedit = QLineEdit(self)
        self.apiedit.editingFinished.connect(self.onAPIEdited)
        self.apiedit.setGeometry(18,45,250,25)
        self.apiedit.setPlaceholderText(self.config.api_base_url)
        self.refreshtimelabel = QLabel('刷新时间（秒）',self)
        self.refreshtimelabel.setGeometry(18,90,500,15)
        self.refreshtimeedit = QDoubleSpinBox(self)
        self.refreshtimeedit.setMinimum(5)
        self.refreshtimeedit.setMaximum(86400)
        self.refreshtimeedit.setDecimals(1)
        self.refreshtimeedit.setSingleStep(0.1)
        self.refreshtimeedit.setGeometry(18,115,150,25)
        self.refreshtimeedit.valueChanged.connect(self.onRefreshTimeEdited)
        self.refreshtimeedit.setValue(float(self.config.refresh_seconds))
        self.savebutton = QPushButton('保存',self)
        self.savebutton.setGeometry(215,150,65,35)
        self.savebutton.clicked.connect(self.onSaved)
    def onAPIEdited(self):
        text = self.apiedit.text()
        if not self.urlre.match(text):
            QMessageBox.warning(self,"错误","API地址不合法",QMessageBox.StandardButton.Yes)
            return
        self.config.api_base_url = text
    
    def onRefreshTimeEdited(self):
        time = float(self.refreshtimeedit.text())
        self.config.refresh_seconds = time
    
    def onSaved(self, event):
        self.on_setting_save.emit(self.config)

class BBTerminal(QMainWindow):
    def __init__(self, parent = ..., flags = ...):
        super().__init__()
        self.settingDialog = SettingMenu(self)
        self.setWindowTitle('指令【终端】')
        self.settingDialog.on_setting_save.connect(self.onSettingSaved)
        # 从资源文件中解压音频文件
        if not os.path.exists(f"{os.environ.get('TEMP')}\\bb.wav"):
            bbwav = QFile(":audios/bb")
            bbwav.open(QIODevice.OpenModeFlag.ReadOnly)
            tempwav = QFile(f"{os.environ.get('TEMP')}\\bb.wav")
            tempwav.open(QIODevice.OpenModeFlag.WriteOnly)
            tempwav.write(bbwav.readAll())
            bbwav.close()
            tempwav.close()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.X11BypassWindowManagerHint
            | Qt.WindowType.Tool
        )
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
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
        if not os.path.exists("config.ini"):
            resl = QMessageBox.critical(self,"错误","配置文件缺失，是否修补？",QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.Yes)
            if resl == QMessageBox.StandardButton.Yes:
                with open("config.ini","w",encoding="utf-8") as f:
                    f.write(config_file)
            else:
                QApplication.exit()
        self.config = PetConfig()
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
        mixer.music.load(f"{os.environ.get('TEMP')}\\bb.wav")
        mixer.music.set_volume(1.5)
        self.timer = QTimer()
        self.timer.timeout.connect(self.initPrescript)
        self.timer.start(50)  # 每50ms触发一次
        mixer.music.play()
        self.prescriptlabel = QLabel(self)
        self.prescriptlabel.setGeometry(80,43,275,200)
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
        self.refreshtimer = QTimer()
        self.refreshtimer.timeout.connect(self.refreshPrescript)
        if self.config.refresh_seconds != 0:
            self.refreshtimer.start(self.config.refresh_seconds * 1000)
        

    def showContextMenu(self, event : QPoint):
        contextMenu = QMenu(self)
        refreshAct = QAction('刷新',self)
        settingAct = QAction('设置',self)
        quitAct = QAction('退出',self)
        contextMenu.addActions([refreshAct,settingAct,quitAct])
        refreshAct.triggered.connect(self.refreshPrescript)
        settingAct.triggered.connect(self.showSettingWidget)
        quitAct.triggered.connect(QApplication.quit)
        contextMenu.exec_(self.mapToGlobal(event.__pos__()))
        
    def loadImage(self):
        self.bbimg = QPixmap(":images/terminal")
        self.label.setPixmap(self.bbimg)
    
#    """  def mousePressEvent(self, event):
#         """鼠标按下时记录拖动起点"""
#         if event.button() == Qt.LeftButton:  # 左键按下
#             self.dragPos = event.globalPos()  # 记录全局坐标
#             self.is_dragging = False  # 初始标记为未拖动（避免误判为点击）
#             event.accept()

#     def mouseMoveEvent(self, event):
#         """鼠标移动时拖动窗口"""
#         if event.buttons() == Qt.LeftButton:  # 左键按住并移动
#             self.is_dragging = True  # 标记为拖动状态
#             # 计算新位置：当前位置 + 鼠标移动距离
#             self.move(self.pos() + event.globalPos() - self.dragPos)
#             self.dragPos = event.globalPos()  # 更新拖动起点
#             event.accept() """
    
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
    
    def showSettingWidget(self, event):
        self.settingDialog.show()
    
    def onSettingSaved(self, config : PetConfig):
        self.config = config
        self.config.dump()
        if self.config.refresh_seconds != 0:
            self.refreshtimer.start(self.config.refresh_seconds * 1000)

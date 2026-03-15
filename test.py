from PyQt5.QtGui import QFontDatabase, QFont
import resource  # 此处直接导入qrc转换后的py文件
from PyQt5 import QtWidgets
from PyQt5.QtCore import QResource,QFile,QIODevice,QTextStream
import sys
import os

print(os.environ.get("TEMP"))
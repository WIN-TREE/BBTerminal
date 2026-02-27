from PyQt5.QtGui import QFontDatabase, QFont
import resource  # 此处直接导入qrc转换后的py文件
from PyQt5 import QtWidgets
import sys

# 初始化 GUI 应用
app = QtWidgets.QApplication(sys.argv)

fontDb = QFontDatabase()
fontID = fontDb.addApplicationFont(":/fonts/hypixel")  # 此处的路径为qrc文件中的字体路径
fontFamilies = fontDb.applicationFontFamilies(fontID)
print(fontFamilies)  # ['LXGW WenKai']
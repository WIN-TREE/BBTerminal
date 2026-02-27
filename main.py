from PyQt5.QtWidgets import QApplication, QMessageBox
from BBTerminal import BBTerminal
import sys

def __main__():
    app = QApplication(sys.argv)
    try:
        pet = BBTerminal()
        pet.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None,"错误",f"未知错误\n{str(e)}")
        print(str(e))

if __name__ == "__main__":
    __main__()
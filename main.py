import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.app_config import AppConfig

if __name__ == "__main__":
    colorimeter = AppConfig.get_colorimeter()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
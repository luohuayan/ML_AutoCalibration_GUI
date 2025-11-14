from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QSizePolicy,
    QMessageBox,
    QDialog,
)
from PyQt5.QtGui import QFont
from core.app_config import AppConfig
from PyQt5.QtCore import pyqtSignal, Qt

class VersionWindow(QDialog):
    def __init__(self, parent=None, dialog_title="选择文件夹", default_path=""):
        super().__init__(parent)
        self.setWindowTitle("About AutoCalibration GUI")
        self.setGeometry(300, 300, 500, 200)
        self.version="0.1.1.1"
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.title_label=QLabel("Auto_Calibration GUI")
        self.version_label=QLabel("Version: "+self.version)

        self.ok_button=QPushButton("OK")
        self.ok_button.clicked.connect(self.accept) # 点击按钮关闭对话框

        # 设置字体大小
        title_font = QFont("Arial", 16, QFont.Bold)  # 设置标题字体
        version_font = QFont("Arial", 12)  # 设置版本字体

        self.title_label.setFont(title_font)
        self.version_label.setFont(version_font)

        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)

        button_layout=QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

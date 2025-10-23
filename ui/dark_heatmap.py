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
    QGroupBox,
    QGridLayout,
    QSpacerItem,
    QDialog
)
from core.app_config import AppConfig
from PyQt5.QtCore import pyqtSignal, Qt
import mlcolorimeter as mlcm
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image
from scripts.capture_dark_heatmap import capture_dark_heatmap


class DarkHeatMapWindow(QDialog):
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("capture dark heatmap")
        self.setGeometry(200, 200, 800, 500)
        self.colorimeter = AppConfig.get_colorimeter()
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.file_name = "dark_heatmap.xlsx"
        self._init_ui()

    def _init_ui(self):
        grid_layout = QGridLayout()

        self.label_times = QLabel()
        self.label_times.setText("多帧平均次数: ")
        grid_layout.addWidget(self.label_times, 0, 0)

        self.line_edit_times = QLineEdit()
        self.line_edit_times.setText("1")
        self.line_edit_times.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_times, 1, 0)

        self.label_etlist = QLabel()
        self.label_etlist.setText("曝光时间列表(ms), 例如: 1 10 20, 以空格隔开")
        grid_layout.addWidget(self.label_etlist, 2, 0)

        self.line_edit_etlist = QLineEdit()
        self.line_edit_etlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_etlist, 3, 0)

        self.label_binnlist = QLabel()
        self.label_binnlist.setText(
            "binning列表, (0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16), 以空格隔开"
        )
        grid_layout.addWidget(self.label_binnlist, 4, 0)

        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_binnlist, 5, 0)

        self.label_ndlist = QLabel()
        self.label_ndlist.setText("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 6, 0)

        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 7, 0)

        self.label_xyzlist = QLabel()
        self.label_xyzlist.setText("xyz列表, (1: X, 2: Y, 3: Z, 10: Clear), 以空格隔开")
        grid_layout.addWidget(self.label_xyzlist, 8, 0)

        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 9, 0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径:")
        grid_layout.addWidget(self.label_path, 10, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 11, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 11, 1)

        self.label_filename = QLabel()
        self.label_filename.setText("文件名:")
        grid_layout.addWidget(self.label_filename, 12, 0)

        self.line_edit_filename = QLineEdit()
        self.line_edit_filename.setReadOnly(True)  # 设置为只读
        self.line_edit_filename.setPlaceholderText("dark_heatmap")
        self.line_edit_filename.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_filename, 13, 0)

        self.btn_capture = QPushButton("开始拍图")
        self.btn_capture.clicked.connect(self.start_capture)
        grid_layout.addWidget(self.btn_capture, 14, 0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)
    
    def _open_folder_dialog(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.save_path = folder_path
            self.line_edit_path.setText(folder_path)
        else:
            QMessageBox.critical(self,"MLColorimeter","选择路径错误",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def start_capture(self):
        try:
            self.capture_times = int(self.line_edit_times.text())
            self.etlist = self.line_edit_etlist.text().split()
            self.binnlist = self.line_edit_binnlist.text().split()
            self.ndlist = self.line_edit_ndlist.text().split()
            self.xyzlist = self.line_edit_xyzlist.text().split()
            self.file_name = self.line_edit_filename.text() + ".xlsx"

            capture_dark_heatmap(self.colorimeter, self.ndlist, self.xyzlist, self.binnlist, self.etlist, self.save_path, self.file_name, self.capture_times)

            QMessageBox.information(self,"MLColorimeter","finish", QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QSizePolicy,
    QMessageBox,
    QCheckBox,
    QGroupBox,
    QGridLayout,
    QSpacerItem,
    QDialog,
    QComboBox,
    QFormLayout,
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon
from core.app_config import AppConfig
from PyQt5.QtCore import pyqtSignal, Qt, QThread
import mlcolorimeter as mlcm
from scripts.config_detection import config_detection
import os
import configparser
import json


class ConfigDetectionThread(QThread):
    finished = pyqtSignal()  # 线程完成信号
    error = pyqtSignal(str)  # 错误信号
    status_update = pyqtSignal(str)  # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters = parameters

    def run(self):
        try:
            config_detection(
                status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit()  # 发送完成信号
        except Exception as e:
            self.error.emit(str(e))  # 发送错误信号


class ConfigDetectionWindow(QDialog):
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("generate colorshift")
        self.setGeometry(200, 200, 800, 500)
        self.colorimeter = AppConfig.get_colorimeter()
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint |
                            Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowIcon(QIcon(
            "F:/ML_AutoCalibration_GUI/ML_AutoCalibration_GUI/dist/FingerPrintScanMTF.ico"))
        self.intValidator = QIntValidator()
        self.doubleValidator = QDoubleValidator()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.save_path = ""
        self._init_ui()
        self.is_running = False
        self.temp = False

    def _init_ui(self):
        grid_layout = QGridLayout()
        self.label_path = QLabel()
        self.label_path.setText("EYE1路径:")
        grid_layout.addWidget(self.label_path, 0, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("例如：F:/config/EYE1")
        self.line_edit_path.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 0, 1)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 0, 2)

        self.output_path = QLabel()
        self.output_path.setText("输出路径:")
        grid_layout.addWidget(self.output_path, 1, 0)

        self.line_output_path = QLineEdit()
        self.line_output_path.setReadOnly(True)  # 设置为只读
        self.line_output_path.setPlaceholderText("选择文件夹")
        self.line_output_path.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_output_path, 1, 1)

        self.btn_output = QPushButton("浏览...")
        self.btn_output.clicked.connect(self._open_folder_dialog1)
        grid_layout.addWidget(self.btn_output, 1, 2)

        self.label_file_name = QLabel()
        self.label_file_name.setText("保存文件名:")
        grid_layout.addWidget(self.label_file_name, 2, 0)

        self.line_edit_file_name = QLineEdit()
        self.line_edit_file_name.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_file_name.setText("moduleName")
        grid_layout.addWidget(self.line_edit_file_name, 2, 1)

        self.label_detect_folder = QLabel("选择检测项: ")
        grid_layout.addWidget(self.label_detect_folder, 3, 0)

        checkbox_layout = QHBoxLayout()

        self.checkbox_dark = QCheckBox("Dark")
        self.checkbox_dark.setChecked(True)
        self.checkbox_dark.setEnabled(False)
        self.checkbox_colorshift = QCheckBox("ColorShift")
        self.checkbox_colorshift.setChecked(True)

        self.checkbox_luminance = QCheckBox("Luminance")
        self.checkbox_luminance.setChecked(True)
        self.checkbox_radiance = QCheckBox("Radiance")
        self.checkbox_radiance.setChecked(True)
        self.checkbox_offset = QCheckBox("Offset")
        self.checkbox_offset.setChecked(True)
        self.checkbox_darklist = QCheckBox("DarkList")
        self.checkbox_darklist.setChecked(True)
        self.checkbox_ffc = QCheckBox("FFC")
        self.checkbox_ffc.setChecked(True)
        self.checkbox_distortion = QCheckBox("Distortion")
        self.checkbox_distortion.setChecked(True)
        checkbox_layout.addWidget(self.checkbox_dark)
        checkbox_layout.addWidget(self.checkbox_distortion)
        checkbox_layout.addWidget(self.checkbox_colorshift)
        checkbox_layout.addWidget(self.checkbox_luminance)
        checkbox_layout.addWidget(self.checkbox_radiance)
        checkbox_layout.addWidget(self.checkbox_offset)
        checkbox_layout.addWidget(self.checkbox_darklist)
        checkbox_layout.addWidget(self.checkbox_ffc)
        grid_layout.addLayout(checkbox_layout, 3, 1, 1, 8)

        self.btn_write = QPushButton("开始检测")
        self.btn_write.clicked.connect(self.start_detect)
        grid_layout.addWidget(self.btn_write, 4, 0)

        self.status_label = QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label, 4, 1)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum,
                             QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

    def start_detect(self):
        try:
            self.eye1_path = self.line_edit_path.text()
            self.output_path = self.line_output_path.text()
            self.file_name = self.line_edit_file_name.text()
            if not self.eye1_path or not self.output_path or not self.file_name:
                QMessageBox.critical(self, "MLColorimeter", "请确保所有路径和文件名都已填写",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return

            self.select_folders = ['Dark']
            if self.checkbox_colorshift.isChecked():
                self.select_folders.append("ColorShift")
            if self.checkbox_luminance.isChecked():
                self.select_folders.append("Luminance")
            if self.checkbox_radiance.isChecked():
                self.select_folders.append("Radiance")
            if self.checkbox_offset.isChecked():
                self.select_folders.append("Offset")
            if self.checkbox_distortion.isChecked():
                self.select_folders.append("Distortion")
            if self.checkbox_darklist.isChecked():
                self.select_folders.append("DarkList")
            if self.checkbox_ffc.isChecked():
                self.select_folders.append("FFC")

            config_detection(
                eye1_path=self.eye1_path,
                out_path=self.output_path,
                file_name=self.file_name,
                folder_name=self.select_folders)
            self.status_label.setText(
                "<span style='color: green;'>状态: 正在进行检测...</span>")  # 更新状态
            self.btn_write.setEnabled(False)
            self.is_running = True
            parameters = {
                'eye1_path': self.eye1_path,
                'out_path': self.output_path,
                'file_name': self.file_name,
                'folder_name': self.select_folders
            }
            self.config_detection_thread = ConfigDetectionThread(parameters)
            self.config_detection_thread.finished.connect(
                self.on_thread_finished)
            self.config_detection_thread.error.connect(self.on_thread_error)
            self.config_detection_thread.status_update.connect(
                self.update_status)
            self.config_detection_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "MLColorimeter", "exception" +
                                 str(e), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            self.btn_write.setEnabled(True)
            self.is_running = False

    def update_status(self, message):
        self.status_label.setText(
            f"<span style='color: green;'>检测: {message}</span>")

    def on_thread_finished(self):
        QMessageBox.information(self, "MLColorimeter", "检测完成!", QMessageBox.Ok)
        self.status_label.setText(
            "<span style='color: green;'>状态: 检测完成！</span>")  # 更新状态
        self.btn_write.setEnabled(True)
        self.is_running = False

    def on_thread_error(self, error_message):
        QMessageBox.critical(self, "MLColorimeter",
                             "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(
            f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_write.setEnabled(True)
        self.is_running = False

    def closeEvent(self, event):
        if self.is_running:
            event.ignore()
            QMessageBox.warning(self, "警告", "程序运行中，请勿关闭窗口", QMessageBox.Ok)
        else:
            event.accept()

    def _open_folder_dialog(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.line_edit_path.setText(folder_path)
        else:
            QMessageBox.critical(self, "MLColorimeter", "选择路径错误",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

    def _open_folder_dialog1(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.line_output_path.setText(folder_path)
        else:
            QMessageBox.critical(self, "MLColorimeter", "选择路径错误",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

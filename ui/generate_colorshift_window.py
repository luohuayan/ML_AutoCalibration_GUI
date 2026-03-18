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
import os
import configparser
import json


class GenerateColorShift(QDialog):
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
        grid_layout.addWidget(self.line_edit_path, 1, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 1, 1)

        self.checkbox_exist_aperature = QCheckBox("Aperture")
        self.checkbox_exist_aperature.stateChanged.connect(
            self.on_aperature_checkbox_changed)
        grid_layout.addWidget(self.checkbox_exist_aperature, 2, 0)

        self.line_edit_aperature = QLineEdit()
        self.line_edit_aperature.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_aperature.setText("3mm")
        grid_layout.addWidget(self.line_edit_aperature, 3, 0)

        self.checkbox_exist_nd = QCheckBox("NDFilter")
        self.checkbox_exist_nd.stateChanged.connect(
            self.on_nd_checkbox_changed)
        grid_layout.addWidget(self.checkbox_exist_nd, 4, 0)

        self.line_edit_nd = QLineEdit()
        self.line_edit_nd.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_nd.setText("ND0")
        grid_layout.addWidget(self.line_edit_nd, 5, 0)

        self.checkbox_exist_xyz = QCheckBox("ColorFilter")
        self.checkbox_exist_xyz.stateChanged.connect(
            self.on_xyz_checkbox_changed)

        grid_layout.addWidget(self.checkbox_exist_xyz, 7, 0)

        self.line_edit_xyz = QLineEdit()
        self.line_edit_xyz.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_xyz.setText("X")
        grid_layout.addWidget(self.line_edit_xyz, 8, 0)

        self.label_x = QLabel()
        self.label_x.setText(
            "x_offset: ")
        grid_layout.addWidget(self.label_x, 9, 0)
        self.line_edit_x = QLineEdit()
        self.line_edit_x.setText("1")
        self.line_edit_x.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_x, 10, 0)

        self.label_y = QLabel()
        self.label_y.setText(
            "y_offset: ")
        grid_layout.addWidget(self.label_y, 11, 0)
        self.line_edit_y = QLineEdit()
        self.line_edit_y.setText("1")
        self.line_edit_y.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_y, 12, 0)

        self.btn_write = QPushButton("写入")
        self.btn_write.clicked.connect(self.start_write)
        grid_layout.addWidget(self.btn_write, 13, 0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum,
                             QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)
        self.line_edit_aperature.setVisible(False)
        self.line_edit_nd.setVisible(False)
        self.line_edit_xyz.setVisible(False)

    def start_write(self):
        self.file_name = self.output_path = self.json_path = ""
        self.eye1_path = self.line_edit_path.text()
        self.get_colorshift_folder_rule(self.eye1_path)
        if not self.temp:
            return
        self.colorshift_path = self.eye1_path+"/ColorShift"
        os.makedirs(self.colorshift_path, exist_ok=True)
        self.aperture = self.line_edit_aperature.text()
        self.nd = self.line_edit_nd.text()
        self.xyz = self.line_edit_xyz.text()
        self.mapping = {
            "Aperature": self.aperture,
            "NDFilter": self.nd,
            "ColorFilter": self.xyz
        }

        self.x_offset = int(self.line_edit_x.text()
                            ) if self.line_edit_x.text() else 0
        self.y_offset = int(self.line_edit_y.text()
                            ) if self.line_edit_y.text() else 0

        data = {
            "ColorShift": [
                [
                    self.x_offset,
                    self.y_offset
                ]
            ]
        }
        if self.folder_rule == "":
            self.output_path = os.path.join(self.colorshift_path, self.suffix)
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            if self.folder_rule:
                parts = self.folder_rule.split("_")
                file_parts = []
                for part in parts:
                    if part == "Aperture":
                        if self.checkbox_exist_aperature.isChecked():
                            file_parts.append(self.aperture)
                        else:
                            QMessageBox.critical(self, "MLColorimeter", "未勾选Aperture并设置参数",
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                            return
                    elif part == "NDFilter":
                        if self.checkbox_exist_nd.isChecked():
                            file_parts.append(self.nd)
                        else:
                            QMessageBox.critical(self, "MLColorimeter", "未勾选NDFilter并设置参数",
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                            return
                    elif part == "ColorFilter":
                        if self.checkbox_exist_xyz.isChecked():
                            file_parts.append(self.xyz)
                        else:
                            QMessageBox.critical(self, "MLColorimeter", "未勾选ColorFilter并设置参数",
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                            return
                    else:
                        QMessageBox.critical(self, "MLColorimeter", f"Folder_Rule格式不符合规定: {self.folder_rule}",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                self.file_name = "_".join(file_parts)

                self.output_path = os.path.join(
                    self.colorshift_path, self.file_name)
                os.makedirs(self.output_path, exist_ok=True)
                self.json_path = os.path.join(self.output_path, self.suffix)
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        QMessageBox.information(self, "MLColorimeter", f"ColorShift的json文件生成成功，路径: {self.output_path}",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

    def get_colorshift_folder_rule(self, config_path):
        self.ini_path = config_path+"/"+"config.ini"
        if not os.path.exists(self.ini_path):
            QMessageBox.critical(self, "MLColorimeter", "config.ini文件不存在，请检查eye1路径下的文件",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            self.temp = False
            return

        config = configparser.ConfigParser()
        try:
            config.read(self.ini_path, encoding='utf-8')

            if 'ColorShift' in config:
                self.folder_rule = config['ColorShift'].get(
                    'Folder_Rule', '').strip()
                self.suffix = config['ColorShift'].get('Suffix', '').strip()
                self.temp = True
            else:
                QMessageBox.critical(self, "MLColorimeter", "config.ini文件中缺少ColorShift部分，请检查eye1路径下的文件",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                self.temp = False
                return
        except Exception as e:
            QMessageBox.critical(self, "MLColorimeter", f"读取config.ini文件失败: {str(e)}",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            self.temp = False
            return

    def on_aperature_checkbox_changed(self):
        if self.checkbox_exist_aperature.isChecked():
            self.line_edit_aperature.setVisible(True)
        else:
            self.line_edit_aperature.setVisible(False)

    def on_nd_checkbox_changed(self):
        if self.checkbox_exist_nd.isChecked():
            self.line_edit_nd.setVisible(True)
        else:
            self.line_edit_nd.setVisible(False)

    def on_xyz_checkbox_changed(self):
        if self.checkbox_exist_xyz.isChecked():
            self.line_edit_xyz.setVisible(True)
        else:
            self.line_edit_xyz.setVisible(False)

    def _open_folder_dialog(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.eye1_path = folder_path
            self.line_edit_path.setText(folder_path)
        else:
            QMessageBox.critical(self, "MLColorimeter", "选择路径错误",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

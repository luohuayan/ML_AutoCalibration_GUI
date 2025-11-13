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
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFormLayout
)
from core.app_config import AppConfig
from PyQt5.QtCore import pyqtSignal, Qt,QThread
import mlcolorimeter as mlcm
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image
from scripts.capture_colorfilter_center import capture_colorfilter_center
from scripts.capture_RX_center import capture_RX_center
from ui.exposureconfig_window import ExposureConfigWindow

class CaptureRXCenterThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            capture_RX_center(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class CaptureColorfilterCenterThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            capture_colorfilter_center(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class CaptureCenterWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Capture Center")
        self.setGeometry(200, 200, 400, 200)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.file_name = ""
        self.exposure_map_obj = {}
        self._init_ui()
        self.is_running=False

    def _init_ui(self):
        grid_layout = QGridLayout()

        self.label_ndlist = QLabel()
        self.label_ndlist.setText("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 0, 0)
        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 1, 0)

        self.label_xyzlist = QLabel()
        self.label_xyzlist.setText("xyz列表, (1: X, 2: Y, 3: Z, 10: Clear), 以空格隔开")
        grid_layout.addWidget(self.label_xyzlist, 2, 0)
        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 3, 0)
        
        self.btn_load_config = QPushButton("曝光时间配置")
        self.btn_load_config.clicked.connect(self.load_exposure_config)
        grid_layout.addWidget(self.btn_load_config, 3, 1)

        self.cb_useRX = QCheckBox()
        self.cb_useRX.setText("启用RX")
        self.cb_useRX.setChecked(False)
        self.cb_useRX.stateChanged.connect(self._useRX_state_changed)
        grid_layout.addWidget(self.cb_useRX, 4, 0)

        self.label_sphlist = QLabel()
        self.label_sphlist.setText(
            "sph列表, (例如: -6 -5 -4 -3 -2 -1 0 1 2 3 4 5 6), 以空格隔开")
        grid_layout.addWidget(self.label_sphlist, 5, 0)

        self.line_edit_sphlist = QLineEdit()
        self.line_edit_sphlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_sphlist, 6, 0)

        self.label_cyllist = QLabel()
        self.label_cyllist.setText(
            "cyl列表, (例如: -4 -3.5 -3 -2.5 -2 -1.5 -1 -0.5 0), 以空格隔开")
        grid_layout.addWidget(self.label_cyllist, 7, 0)

        self.line_edit_cyllist = QLineEdit()
        self.line_edit_cyllist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_cyllist, 8, 0)

        self.label_axislist = QLabel()
        self.label_axislist.setText(
            "axis列表, (例如: 0 15 30 45 60 75 90 105 120 135 150 165), 以空格隔开")
        grid_layout.addWidget(self.label_axislist, 9, 0)

        self.line_edit_axislist = QLineEdit()
        self.line_edit_axislist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_axislist, 10, 0)

        group_box1=QGroupBox("roi设置(仅启用RX时设置)")
        from_layout1=QFormLayout()

        self.label_x_input=QLabel("x_input: ")
        self.line_edit_x_input = QLineEdit()
        self.line_edit_x_input.setText("0")
        self.line_edit_x_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_y_input=QLabel("y_input: ")
        self.line_edit_y_input = QLineEdit()
        self.line_edit_y_input.setText("0")
        self.line_edit_y_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_width_input=QLabel("width_input: ")
        self.line_edit_width_input = QLineEdit()
        self.line_edit_width_input.setText("300")
        self.line_edit_width_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_height_input=QLabel("height_input: ")
        self.line_edit_height_input = QLineEdit()
        self.line_edit_height_input.setText("300")
        self.line_edit_height_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        horizontal_layout5=QHBoxLayout()
        horizontal_layout5.addWidget(self.label_x_input)
        horizontal_layout5.addWidget(self.line_edit_x_input)
        horizontal_layout5.addWidget(self.label_y_input)
        horizontal_layout5.addWidget(self.line_edit_y_input)
        horizontal_layout5.addWidget(self.label_width_input)
        horizontal_layout5.addWidget(self.line_edit_width_input)
        horizontal_layout5.addWidget(self.label_height_input)
        horizontal_layout5.addWidget(self.line_edit_height_input)
        from_layout1.addRow(horizontal_layout5)

        group_box1.setLayout(from_layout1)
        grid_layout.addWidget(group_box1, 11, 0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径:")
        grid_layout.addWidget(self.label_path, 12, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 13, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 13, 1)

        self.btn_capture = QPushButton("开始拍图")
        self.btn_capture.clicked.connect(self.start_capture)
        grid_layout.addWidget(self.btn_capture, 14, 0)


        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,15,0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

        self.label_sphlist.hide()
        self.line_edit_sphlist.hide()
        self.label_cyllist.hide()
        self.line_edit_cyllist.hide()
        self.label_axislist.hide()
        self.line_edit_axislist.hide()

    def start_capture(self):
        try:
            self.nd_list=self.line_edit_ndlist.text().strip().split()
            self.xyz_list=self.line_edit_xyzlist.text().strip().split()
            self.save_path=self.line_edit_path.text().strip()
            if self.cb_useRX.isChecked():
                self.sph_list=[float(sph) for sph in self.line_edit_sphlist.text().strip().split()]
                self.cyl_list=[float(cyl) for cyl in self.line_edit_cyllist.text().strip().split()]
                self.axis_list=[int(axis) for axis in self.line_edit_axislist.text().strip().split()]
                x=int(self.line_edit_x_input.text())
                y=int(self.line_edit_y_input.text())
                width=int(self.line_edit_width_input.text())
                height=int(self.line_edit_height_input.text())
                self.roi=mlcm.pyCVRect(x,y,width,height)
                self.status_label.setText("<span style='color: green;'>状态: 正在运行...</span>")  # 更新状态
                self.btn_capture.setEnabled(False)
                self.is_running=True
                parameters={
                    'colorimeter':self.colorimeter,
                    'sph_list':self.sph_list,
                    'cyl_list':self.cyl_list,
                    'axis_list':self.axis_list,
                    'save_path':self.save_path,
                    'nd_list':self.nd_list,
                    'xyz_list':self.xyz_list,
                    'roi':self.roi,
                    'exposure_map_obj':self.exposure_map_obj
                }
                self.captureRXcenterThread=CaptureRXCenterThread(parameters)
                self.captureRXcenterThread.finished.connect(self.on_captureCenter_finished)
                self.captureRXcenterThread.error.connect(self.on_captureCenter_error)
                self.captureRXcenterThread.status_update.connect(self.update_status)
                self.captureRXcenterThread.start()
                
            else:
                self.status_label.setText("<span style='color: green;'>状态: 正在运行...</span>")  # 更新状态
                self.btn_capture.setEnabled(False)
                self.is_running=True
                parameters={
                    'colorimeter':self.colorimeter,
                    'save_path':self.save_path,
                    'nd_list':self.nd_list,
                    'xyz_list':self.xyz_list,
                    'exposure_map_obj':self.exposure_map_obj
                }
                self.captureColorfiltercenterThread=CaptureColorfilterCenterThread(parameters)
                self.captureColorfiltercenterThread.finished.connect(self.on_captureCenter_finished)
                self.captureColorfiltercenterThread.error.connect(self.on_captureCenter_error)
                self.captureColorfiltercenterThread.status_update.connect(self.update_status)
                self.captureColorfiltercenterThread.start()
                
            pass
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_captureCenter_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_captureCenter_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def closeEvent(self, event):
        if self.is_running:
            # 如果正在进行定标，拦截关闭事件
            event.ignore()
            QMessageBox.warning(self,"警告","程序运行中，请勿关闭窗口",QMessageBox.Ok)
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
            self.save_path = folder_path
            self.line_edit_path.setText(folder_path)
        else:
            QMessageBox.critical(self,"MLColorimeter","选择路径错误",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def load_exposure_config(self):
        try:
            self.nd_list=self.line_edit_ndlist.text().strip().split()
            self.xyz_list=self.line_edit_xyzlist.text().strip().split()
            self.exposure_config_window = ExposureConfigWindow(self.nd_list,self.xyz_list)
            # 连接信号
            self.exposure_config_window.config_saved.connect(self.update_config)
            self.exposure_config_window.exec_()
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
    
    def update_config(self,exposure_map):
        # print("Received exposure map:", exposure_map)
        self.exposure_map_obj={}
        for nd_str,xyz_dict in exposure_map.items():
            nd_enum=mlcm.str_to_MLFilterEnum(nd_str)
            self.exposure_map_obj[nd_enum]={}
            for xyz_str,setting in xyz_dict.items():
                xyz_enum=mlcm.str_to_MLFilterEnum(xyz_str)
                exposure_mode = mlcm.ExposureMode.Fixed if setting['exposure_mode']=='Fixed' else mlcm.ExposureMode.Auto
                exposure_time=setting['exposure_time']
                self.exposure_map_obj[nd_enum][xyz_enum]=mlcm.pyExposureSetting(
                    exposure_mode=exposure_mode,
                    exposure_time=exposure_time
                )
        
    def _useRX_state_changed(self):
        if self.cb_useRX.isChecked():
            self.label_sphlist.show()
            self.line_edit_sphlist.show()
            self.label_cyllist.show()
            self.line_edit_cyllist.show()
            self.label_axislist.show()
            self.line_edit_axislist.show()
        else:
            self.label_sphlist.hide()
            self.line_edit_sphlist.hide()
            self.label_cyllist.hide()
            self.line_edit_cyllist.hide()
            self.label_axislist.hide()
            self.line_edit_axislist.hide()

        
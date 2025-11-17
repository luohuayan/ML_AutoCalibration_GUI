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
    QDialog,
    QButtonGroup,
    QFormLayout,
    QComboBox,
    QRadioButton,
    QCheckBox,
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
from scripts.capture_image_fixedLUM import capture_image_fixedLUM, capture_image_ficedLUM_afterFFC


class CaptureImageFixedLUMafterFFCThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            capture_image_ficedLUM_afterFFC(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class CaptureImageFixedLUMWindow(QDialog):

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("capture image fixed LUM")
        self.setGeometry(200, 200, 800, 500)
        self.colorimeter = AppConfig.get_colorimeter()
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.file_name = "capture_image_fixedLUM"
        self.exposure_mode=['Auto','Fixed']
        self.binning_selector=['Logic','Sensor']
        self.binning_mode=['AVERAGE','SUM']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self.select_path=path
        self._init_ui()
        self.is_running=False

    def _init_ui(self):
        grid_layout = QGridLayout()

        group_box0=QGroupBox("相机设置")
        from_layout0=QFormLayout()

        self.label_binn_selector = QLabel(" binning_selector：")
        self.line_edit_binn_selector = QComboBox()
        self.line_edit_binn_selector.addItems(self.binning_selector)
        self.line_edit_binn_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_binn_mode = QLabel(" binning_mode：")
        self.line_edit_binn_mode = QComboBox()
        self.line_edit_binn_mode.addItems(self.binning_mode)
        self.line_edit_binn_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_pixel_format = QLabel(" pixel_format：")
        self.line_edit_pixel_format = QComboBox()
        self.line_edit_pixel_format.addItems(self.pixel_format)
        self.line_edit_pixel_format.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_pixel_format.setCurrentText("MLMono12")

        horizontal_layout=QHBoxLayout()
        horizontal_layout.addWidget(self.label_binn_selector)
        horizontal_layout.addWidget(self.line_edit_binn_selector)
        horizontal_layout.addWidget(self.label_binn_mode)
        horizontal_layout.addWidget(self.line_edit_binn_mode)
        horizontal_layout.addWidget(self.label_pixel_format)
        horizontal_layout.addWidget(self.line_edit_pixel_format)
        from_layout0.addRow(horizontal_layout)

        self.label_binnlist = QLabel(" binning：")
        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_binnlist.setPlaceholderText("0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16")
        from_layout0.addRow(self.label_binnlist, self.line_edit_binnlist)

        group_box0.setLayout(from_layout0)
        grid_layout.addWidget(group_box0, 0, 0)


        self.label_ndlist = QLabel()
        self.label_ndlist.setText("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 1, 0)
        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 2, 0)

        self.label_xyzlist = QLabel()
        self.label_xyzlist.setText("xyz列表, (1: X, 2: Y, 3: Z, 10: Clear), 以空格隔开")
        grid_layout.addWidget(self.label_xyzlist, 3, 0)
        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 4, 0)

        self.label_etlist = QLabel()
        self.label_etlist.setText("曝光时间列表(ms), 例如: 1 10 20, 以空格隔开")
        grid_layout.addWidget(self.label_etlist, 5, 0)
        self.line_edit_etlist = QLineEdit()
        self.line_edit_etlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_etlist, 6, 0)
        
        self.label_path = QLabel()
        self.label_path.setText("保存路径:")
        grid_layout.addWidget(self.label_path, 7, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 8, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 8, 1)

        self.radio_other = QRadioButton()
        self.radio_other.setText("Linearity after FFC")
        self.radio_other.setChecked(True)
        grid_layout.addWidget(self.radio_other, 9, 0)

        self.group_box=QGroupBox("标定参数")
        from_layout=QFormLayout()

        self.cb_useRX = QCheckBox()
        self.cb_useRX.setText("启用RX")
        self.cb_useRX.setChecked(False)
        self.cb_useRX.stateChanged.connect(self._useRX_state_changed)

        self.label_sphlist = QLabel("sph列表, (例如: -6 -5 -4 -3 -2 -1 0 1 2 3 4 5 6), 以空格隔开")
        self.line_edit_sphlist = QLineEdit()
        self.line_edit_sphlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_cyllist = QLabel("cyl列表, (例如: -4 -3.5 -3 -2.5 -2 -1.5 -1 -0.5 0), 以空格隔开")
        self.line_edit_cyllist = QLineEdit()
        self.line_edit_cyllist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.label_axislist = QLabel("axis列表, (例如: 0 15 30 45 60 75 90 105 120 135 150 165), 以空格隔开")
        self.line_edit_axislist = QLineEdit()
        self.line_edit_axislist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        from_layout.addRow(self.cb_useRX)
        from_layout.addRow(self.label_sphlist)
        from_layout.addRow(self.line_edit_sphlist)
        from_layout.addRow(self.label_cyllist)
        from_layout.addRow(self.line_edit_cyllist)
        from_layout.addRow(self.label_axislist)
        from_layout.addRow(self.line_edit_axislist)
        
        self.label_input_path=QLabel("input_path: ")
        self.line_edit_input_path = QLineEdit()
        self.line_edit_input_path.setReadOnly(True)
        self.line_edit_input_path.setText(self.select_path)
        self.line_edit_input_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.label_input_path,self.line_edit_input_path)

        self.label_dark_flag=QLabel("dark_flag：")
        self.checkbox_dark_flag=QCheckBox()
        self.checkbox_dark_flag.setChecked(True)
        self.checkbox_dark_flag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_ffc_flag=QLabel("ffc_flag：")
        self.checkbox_ffc_flag=QCheckBox()
        self.checkbox_ffc_flag.setChecked(True)
        self.checkbox_ffc_flag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_color_shift_flag=QLabel("color_shift_flag：")
        self.checkbox_color_shift_flag=QCheckBox()
        self.checkbox_color_shift_flag.setChecked(True)
        self.checkbox_color_shift_flag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_distortion_flag=QLabel("distortion_flag：")
        self.checkbox_distortion_flag=QCheckBox()
        self.checkbox_distortion_flag.setChecked(True)
        self.checkbox_distortion_flag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_exposure_flag=QLabel("exposure_flag：")
        self.checkbox_exposure_flag=QCheckBox()
        self.checkbox_exposure_flag.setChecked(True)
        self.checkbox_exposure_flag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_four_color_flag=QLabel("four_color_flag：")
        self.checkbox_four_color_flag=QCheckBox()
        self.checkbox_four_color_flag.setChecked(True)
        self.checkbox_four_color_flag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        horizontal_layout2=QHBoxLayout()
        horizontal_layout2.addWidget(self.label_dark_flag)
        horizontal_layout2.addWidget(self.checkbox_dark_flag)
        horizontal_layout2.addWidget(self.label_ffc_flag)
        horizontal_layout2.addWidget(self.checkbox_ffc_flag)
        horizontal_layout2.addWidget(self.label_color_shift_flag)
        horizontal_layout2.addWidget(self.checkbox_color_shift_flag)
        horizontal_layout2.addWidget(self.label_distortion_flag)
        horizontal_layout2.addWidget(self.checkbox_distortion_flag)
        horizontal_layout2.addWidget(self.label_exposure_flag)
        horizontal_layout2.addWidget(self.checkbox_exposure_flag)
        horizontal_layout2.addWidget(self.label_four_color_flag)
        horizontal_layout2.addWidget(self.checkbox_four_color_flag)

        from_layout.addRow(horizontal_layout2)

        self.group_box.setLayout(from_layout)
        grid_layout.addWidget(self.group_box, 10, 0)

        self.btn_start_capture = QPushButton("开始拍图")
        self.btn_start_capture.clicked.connect(self.capture_images)
        grid_layout.addWidget(self.btn_start_capture, 11, 0)

        
        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,12,0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

        self.label_sphlist.hide()
        self.line_edit_sphlist.hide()
        self.label_cyllist.hide()
        self.line_edit_cyllist.hide()
        self.label_axislist.hide()
        self.line_edit_axislist.hide()

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

    def capture_images(self):
        try:
            self.pixel_format=self.get_current_pixel_format()
            self.binn_selector=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.binn=mlcm.Binning(int(self.line_edit_binnlist.text().strip()))
            self.nd_list=[int(nd) for nd in self.line_edit_ndlist.text().strip().split()]
            self.xyz_list=[int(xyz) for xyz in self.line_edit_xyzlist.text().strip().split()]
            self.et_list=[float(et) for et in self.line_edit_etlist.text().strip().split()]
            self.save_path=self.line_edit_path.text().strip()
            if not self.nd_list or not self.xyz_list or not self.et_list or not self.save_path:
                QMessageBox.critical(self,"MLColorimeter","请完整填写所有参数",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
                return
            self.status_label.setText("<span style='color: green;'>状态: 正在运行...</span>")  # 更新状态
            self.btn_start_capture.setEnabled(False)
            self.is_running=True
            if self.cb_useRX.isChecked():
                self.sph_list=[float(sph) for sph in self.line_edit_sphlist.text().strip().split()]
                self.cyl_list=[float(cyl) for cyl in self.line_edit_cyllist.text().strip().split()]
                self.axis_list=[int(axis) for axis in self.line_edit_axislist.text().strip().split()]
            else:
                self.sph_list=self.cyl_list=[0]
                self.axis_list=[0]
            self.input_path=self.select_path
            self.dark_flag=self.checkbox_dark_flag.isChecked()
            self.ffc_flag=self.checkbox_ffc_flag.isChecked()
            self.color_shift_flag=self.checkbox_color_shift_flag.isChecked()
            self.distortion_flag=self.checkbox_distortion_flag.isChecked()
            self.exposure_flag=self.checkbox_exposure_flag.isChecked()
            self.four_color_flag=self.checkbox_four_color_flag.isChecked()
            self.cali_config=mlcm.pyCalibrationConfig(
                input_path=self.input_path,
                dark_flag=self.dark_flag,
                ffc_flag=self.ffc_flag,
                color_shift_flag=self.color_shift_flag,
                distortion_flag=self.distortion_flag,
                exposure_flag=self.exposure_flag,
                four_color_flag=self.four_color_flag
            )
            parameters={
                'colorimeter':self.colorimeter,
                'binn_selector':self.binn_selector,
                'binn_mode':self.binn_mode,
                'binn':self.binn,
                'pixel_format':self.pixel_format,
                'sph_list':self.sph_list,
                'cyl_list':self.cyl_list,
                'axis_list':self.axis_list,
                'save_path':self.save_path,
                'nd_list':self.nd_list,
                'xyz_list':self.xyz_list,
                'ET_list':self.et_list,
                'cali_config':self.cali_config
            }
            self.captureimagefixedLUMafterFFCThread=CaptureImageFixedLUMafterFFCThread(parameters)
            self.captureimagefixedLUMafterFFCThread.finished.connect(self.on_capture_finished)
            self.captureimagefixedLUMafterFFCThread.error.connect(self.on_capture_error)
            self.captureimagefixedLUMafterFFCThread.status_update.connect(self.update_status)
            self.captureimagefixedLUMafterFFCThread.start()
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes) 
            self.btn_start_capture.setEnabled(True)
            self.is_running=False   

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_capture_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 完成！</span>")  # 更新状态
        self.btn_start_capture.setEnabled(True)
        self.is_running=False 

    def on_capture_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_start_capture.setEnabled(True)
        self.is_running=False 

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
        
    def get_current_pixel_format(self):
        # 获取当前选择的项
        selected_format=self.line_edit_pixel_format.currentText()
        # 创建字符串到枚举值的映射
        format_mapping={
            'MLMono8':mlcm.MLPixelFormat.MLMono8,
            'MLMono10':mlcm.MLPixelFormat.MLMono10,
            'MLMono12':mlcm.MLPixelFormat.MLMono12,
            'MLMono16':mlcm.MLPixelFormat.MLMono16,
            'MLRGB24':mlcm.MLPixelFormat.MLRGB24,
            'MLBayer':mlcm.MLPixelFormat.MLBayer,
            'MLBayerGB8':mlcm.MLPixelFormat.MLBayerGB8,
            'MLBayerGB12':mlcm.MLPixelFormat.MLBayerGB12,
        }
        # 获取对应的枚举值
        pixel_format_enum=format_mapping.get(selected_format)
        return pixel_format_enum
    
    def get_current_exposure_mode(self):
        # 获取当前选择的项
        selected_mode=self.line_edit_exposure_mode.currentText()
        if selected_mode=='Auto':
            return mlcm.ExposureMode.Auto
        else:
            return mlcm.ExposureMode.Fixed
    
    def get_current_binning_selector(self):
        # 获取当前选择的项
        selected_selector=self.line_edit_binn_selector.currentText()
        if selected_selector=='Logic':
            return mlcm.BinningSelector.Logic
        else:
            return mlcm.BinningSelector.Sensor
        
    def get_current_binning_mode(self):
        # 获取当前选择的项
        selected_mode=self.line_edit_binn_mode.currentText()
        if selected_mode=='AVERAGE':
            return mlcm.BinningMode.AVERAGE
        else:
            return mlcm.BinningMode.SUM
        

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
    QComboBox,
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
from scripts.monocalibration_colorcamera import mono_calibration
from ui.settings_window import SettingsWindow

class CalibrationColorThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            mono_calibration(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class MonoCalibrationColorCameraWindow(QDialog):
    # path_changed = pyqtSignal(str)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("mono calibration Colorcamera")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.select_path=path
        self.file_name = "mono_calibration.xlsx"
        self.binning_selector=['Logic','Sensor']
        self.binning_mode=['AVERAGE','SUM']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self._init_ui()
        
        # 标识当前是否正在定标
        self.is_calibrating=False

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

        horizontal_layout=QHBoxLayout()
        horizontal_layout.addWidget(self.label_binn_selector)
        horizontal_layout.addWidget(self.line_edit_binn_selector)
        horizontal_layout.addWidget(self.label_binn_mode)
        horizontal_layout.addWidget(self.line_edit_binn_mode)
        from_layout0.addRow(horizontal_layout)

        self.label_binnlist = QLabel(" binning：")
        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_binnlist.setText("0")
        self.line_edit_binnlist.setPlaceholderText("0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16")
        from_layout0.addRow(self.label_binnlist, self.line_edit_binnlist)

        group_box0.setLayout(from_layout0)
        grid_layout.addWidget(group_box0, 0, 0)

        self.label_aperture = QLabel()
        self.label_aperture.setText("光阑(mm): 例如：3mm")
        grid_layout.addWidget(self.label_aperture, 1, 0)
        self.line_edit_aperture = QLineEdit()
        self.line_edit_aperture.setText("3mm")
        self.line_edit_aperture.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_aperture, 2, 0)

        self.label_ndlist = QLabel()
        self.label_ndlist.setText("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 3, 0)
        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 4, 0)

        self.label_luminance_lum=QLabel()
        self.label_luminance_lum.setText("Luminance(请输入三个值，分别表示三个颜色通道X、Y、Z对应的亮度）：")
        grid_layout.addWidget(self.label_luminance_lum, 5, 0)
        self.line_edit_luminance_lum = QLineEdit()
        self.line_edit_luminance_lum.setText("1000 2000 3000")
        self.line_edit_luminance_lum.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        grid_layout.addWidget(self.line_edit_luminance_lum, 6, 0)


        self.label_radiance_lum=QLabel()
        self.label_radiance_lum.setText("Radiance：")
        grid_layout.addWidget(self.label_radiance_lum, 7, 0)
        self.line_edit_radiance_lum = QLineEdit()
        self.line_edit_radiance_lum.setText("1000")
        self.line_edit_radiance_lum.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        grid_layout.addWidget(self.line_edit_radiance_lum, 8, 0)

        
        self.label_exposure_offset=QLabel()
        self.label_exposure_offset.setText("exposure offset：")
        grid_layout.addWidget(self.label_exposure_offset, 9, 0)
        self.line_edit_exposure_offset = QLineEdit()
        self.line_edit_exposure_offset.setText("0")
        self.line_edit_exposure_offset.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        grid_layout.addWidget(self.line_edit_exposure_offset, 10, 0)

        self.label_gray_offset=QLabel()
        self.label_gray_offset.setText("gray offset：")
        grid_layout.addWidget(self.label_gray_offset, 11, 0)
        self.line_edit_gray_offset = QLineEdit()
        self.line_edit_gray_offset.setText("0")
        self.line_edit_gray_offset.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        grid_layout.addWidget(self.line_edit_gray_offset, 12, 0)

        self.label_gray_range=QLabel()
        self.label_gray_range.setText("灰度值(例如: 0.5,0.8)，多个灰度值以空格隔开")
        grid_layout.addWidget(self.label_gray_range, 13, 0)
        self.line_edit_gray_range = QLineEdit()
        self.line_edit_gray_range.setText("0.8")
        self.line_edit_gray_range.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_gray_range, 14, 0)

        self.label_image_size = QLabel()
        self.label_image_size.setText("图像中心点坐标x y（打开相机软件查看）：例如像素为13376 9528，则中心点为6688 4764以空格隔开")
        grid_layout.addWidget(self.label_image_size, 15, 0)
        self.line_edit_image_size = QLineEdit()
        self.line_edit_image_size.setText("6688 4764")
        self.line_edit_image_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_image_size, 16, 0)

        self.label_roi_size = QLabel()
        self.label_roi_size.setText("ROI宽高：例如200 200，以空格隔开")
        grid_layout.addWidget(self.label_roi_size, 17, 0)
        self.line_edit_roi_size = QLineEdit()
        self.line_edit_roi_size.setText("200 200")
        self.line_edit_roi_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_roi_size, 18, 0)

        h_layout = QHBoxLayout()
        self.cb_R = QRadioButton()
        self.cb_R.setText("R")
        self.cb_R.setChecked(False)

        h_layout = QHBoxLayout()
        self.cb_G = QRadioButton()
        self.cb_G.setText("G")
        self.cb_G.setChecked(False)

        h_layout = QHBoxLayout()
        self.cb_B = QRadioButton()
        self.cb_B.setText("B")
        self.cb_B.setChecked(False)

        h_layout = QHBoxLayout()
        self.cb_W = QRadioButton()
        self.cb_W.setText("W")
        self.cb_W.setChecked(True)

        self.rgbw_btngroup = QButtonGroup(self)
        self.rgbw_btngroup.addButton(self.cb_R, 1)
        self.rgbw_btngroup.addButton(self.cb_G, 2)
        self.rgbw_btngroup.addButton(self.cb_B, 3)
        self.rgbw_btngroup.addButton(self.cb_W, 4)

        h_layout.addWidget(self.cb_R)
        h_layout.addWidget(self.cb_G)
        h_layout.addWidget(self.cb_B)
        h_layout.addWidget(self.cb_W)
        grid_layout.addLayout(h_layout, 19, 0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径(excel保存位置):")
        grid_layout.addWidget(self.label_path, 20, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 21, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 21, 1)

        self.label_path=QLabel()
        self.label_path.setText("配置路径（eye1）")
        grid_layout.addWidget(self.label_path, 22, 0)
        self.line_edit_eye1_path=QLineEdit()
        self.line_edit_eye1_path.setReadOnly(True)
        self.line_edit_eye1_path.setText(self.select_path)
        grid_layout.addWidget(self.line_edit_eye1_path,23,0)


        self.btn_capture = QPushButton("单色定标")
        self.btn_capture.clicked.connect(self.start_mono_calibration)
        grid_layout.addWidget(self.btn_capture, 24, 0)
        
        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,25,0)

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

    def start_mono_calibration(self):
        try:
            self.binn_selector=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.binn=mlcm.Binning(int(self.line_edit_binnlist.text().strip()))
            # self.path_changed.connect(self.out_path_changed)
            self.eye1_path=self.line_edit_eye1_path.text()
            self.luminance_list=[float(luminance) for luminance in self.line_edit_luminance_lum.text().strip().split()]
            if len(self.luminance_list) < 3:
                QMessageBox.warning(self,"MLColorimeter","请输入三个亮度值",QMessageBox.Ok)
                return
            self.aperture = self.line_edit_aperture.text()
            self.nd_list=self.line_edit_ndlist.text().split()
            self.light_source=self.rgbw_btngroup.checkedButton().text()
            self.radiance=float(self.line_edit_radiance_lum.text())
            self.gray_list=[float(gray) for gray in self.line_edit_gray_range.text().split()]
            self.image_point=self.line_edit_image_size.text().split()
            self.roi_size=self.line_edit_roi_size.text().split()
            self.out_path=self.line_edit_path.text()
            self.gray_offset=float(self.line_edit_gray_offset.text())
            self.exposure_offset=float(self.line_edit_exposure_offset.text())
            
            self.status_label.setText("<span style='color: green;'>状态: 正在进行单色定标...</span>")  # 更新状态
            self.btn_capture.setEnabled(False)
            self.is_calibrating=True
            # 将参数打包到字典中
            parameters = {
                'colorimeter': self.colorimeter,
                'binn_selector': self.binn_selector,
                'binn_mode': self.binn_mode,
                'binn': self.binn,
                'nd_list': self.nd_list,
                'gray_range': self.gray_list,
                'apturate': self.aperture,
                'light_source': self.light_source,
                'luminance': self.luminance_list,
                'radiance': self.radiance,
                'eye1_path': self.eye1_path,
                'out_path': self.out_path,
                'image_point': self.image_point,
                'roi_size': self.roi_size,
                'gray_offset':self.gray_offset,
                'exposure_offset':self.exposure_offset
            }
            self.calibration_thread=CalibrationColorThread(parameters)
            self.calibration_thread.finished.connect(self.on_calibration_finished)
            self.calibration_thread.error.connect(self.on_calibration_error)
            self.calibration_thread.status_update.connect(self.update_status)
            self.calibration_thread.start() # 启动线程
            
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_calibrating=False # 标识定标完成
    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_calibration_finished(self):
        QMessageBox.information(self,"MLColorimeter","单色定标完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 单色定标完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_calibrating=False # 标识定标完成

    def on_calibration_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_capture.setEnabled(True)
        self.is_calibrating=False # 标识定标完成

    def closeEvent(self, event):
        if self.is_calibrating:
            # 如果正在进行定标，拦截关闭事件
            event.ignore()
            QMessageBox.warning(self,"警告","定标进行中，请勿关闭窗口",QMessageBox.Ok)
        else:
            event.accept()
        
    
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
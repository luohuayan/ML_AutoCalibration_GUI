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
    QComboBox,
    QFormLayout,
)
from core.app_config import AppConfig
from PyQt5.QtCore import pyqtSignal, Qt, QThread
import mlcolorimeter as mlcm
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image
from scripts.capture_dark_heatmap import capture_dark_heatmap

class DarkHeatMapThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self,parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            capture_dark_heatmap(status_callback=self.status_update.emit,**self.parameters)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

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
        self.exposure_mode=['Auto','Fixed']
        self.binning_selector=['Logic','Sensor']
        self.binning_mode=['AVERAGE','SUM']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
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

        horizontal_layout=QHBoxLayout()
        horizontal_layout.addWidget(self.label_binn_selector)
        horizontal_layout.addWidget(self.line_edit_binn_selector)
        horizontal_layout.addWidget(self.label_binn_mode)
        horizontal_layout.addWidget(self.line_edit_binn_mode)
        from_layout0.addRow(horizontal_layout)

        self.label_binn = QLabel(" binning：")
        self.line_edit_binn = QLineEdit()
        self.line_edit_binn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_binn.setPlaceholderText("0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16")
        from_layout0.addRow(self.label_binn, self.line_edit_binn)

        self.label_pixel_format = QLabel(" pixel_format：")
        self.line_edit_pixel_format = QComboBox()
        self.line_edit_pixel_format.addItems(self.pixel_format)
        self.line_edit_pixel_format.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_pixel_format.setCurrentText("MLMono12")


        horizontal_layout1=QHBoxLayout()
        horizontal_layout1.addWidget(self.label_pixel_format)
        horizontal_layout1.addWidget(self.line_edit_pixel_format)
        from_layout0.addRow(horizontal_layout1)

        group_box0.setLayout(from_layout0)
        grid_layout.addWidget(group_box0, 0, 0)

        self.label_times = QLabel()
        self.label_times.setText("多帧平均次数: ")
        grid_layout.addWidget(self.label_times, 1, 0)

        self.line_edit_times = QLineEdit()
        self.line_edit_times.setText("1")
        self.line_edit_times.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_times, 2, 0)

        self.label_etlist = QLabel()
        self.label_etlist.setText("曝光时间列表(ms), 例如: 1 10 20, 以空格隔开")
        grid_layout.addWidget(self.label_etlist, 3, 0)

        self.line_edit_etlist = QLineEdit()
        self.line_edit_etlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_etlist, 4, 0)

        self.label_binnlist = QLabel()
        self.label_binnlist.setText(
            "binning列表, (0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16), 以空格隔开"
        )
        grid_layout.addWidget(self.label_binnlist, 5, 0)

        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_binnlist, 6, 0)

        self.label_ndlist = QLabel()
        self.label_ndlist.setText("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 7, 0)

        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 8, 0)

        self.label_xyzlist = QLabel()
        self.label_xyzlist.setText("xyz列表, (1: X, 2: Y, 3: Z, 10: Clear), 以空格隔开")
        grid_layout.addWidget(self.label_xyzlist, 9, 0)

        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 10, 0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径:")
        grid_layout.addWidget(self.label_path, 11, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 12, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 12, 1)

        self.label_filename = QLabel()
        self.label_filename.setText("文件名:")
        grid_layout.addWidget(self.label_filename, 13, 0)

        self.line_edit_filename = QLineEdit()
        self.line_edit_filename.setReadOnly(True)  # 设置为只读
        self.line_edit_filename.setPlaceholderText("dark_heatmap")
        self.line_edit_filename.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_filename, 14, 0)

        self.btn_capture = QPushButton("开始拍图")
        self.btn_capture.clicked.connect(self.start_capture)
        grid_layout.addWidget(self.btn_capture, 15, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,16,0)

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
            self.status_label.setText("<span style='color: green;'>状态: 正在进行拍图或计算...</span>")  # 更新状态
            self.btn_capture.setEnabled(False)
            self.is_running=True
            self.pixel_format=self.get_current_pixel_format()
            self.binn_selector=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.binn=mlcm.Binning(int(self.line_edit_binn.text().strip()))
            self.capture_times = int(self.line_edit_times.text())
            self.etlist = [float(et) for et in self.line_edit_etlist.text().split()]
            binn_enum=[int(binn) for binn in self.line_edit_binnlist.text().strip().split()]
            self.binnlist = [mlcm.Binning(B) for B in binn_enum]
            self.ndlist = [int(nd) for nd in self.line_edit_ndlist.text().split()]
            self.xyzlist = [int(xyz) for xyz in self.line_edit_xyzlist.text().split()]
            self.file_name = self.line_edit_filename.text() + ".xlsx"
            # capture_dark_heatmap(
            #     colorimeter=self.colorimeter,
            #     binn_selector=self.binn_selector,
            #     binn_mode=self.binn_mode,
            #     binn=self.binn,
            #     pixel_format=self.pixel_format,
            #     nd_list=self.ndlist,
            #     xyz_list=self.xyzlist,
            #     binn_list=self.binnlist,
            #     et_list=self.etlist,
            #     save_path=self.save_path,
            #     file_name=self.file_name,
            #     capture_times=self.capture_times
            # )
            parameters={
                'colorimeter':self.colorimeter,
                'binn_selector':self.binn_selector,
                'binn_mode':self.binn_mode,
                'binn':self.binn,
                'pixel_format':self.pixel_format,
                'nd_list':self.ndlist,
                'xyz_list':self.xyzlist,
                'binn_list':self.binnlist,
                'et_list':self.etlist,
                'save_path':self.save_path,
                'file_name':self.file_name,
                'capture_times':self.capture_times
            }
            self.darkheatmapThread=DarkHeatMapThread(parameters)
            self.darkheatmapThread.finished.connect(self.on_darkheatmap_finished)
            self.darkheatmapThread.error.connect(self.on_darkheatmap_error)
            self.darkheatmapThread.status_update.connect(self.update_status)
            self.darkheatmapThread.start()
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_darkheatmap_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_darkheatmap_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def closeEvent(self, event):
        if self.is_running:
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
            
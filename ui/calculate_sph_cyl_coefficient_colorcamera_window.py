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
from scripts.calculate_sph_cyl_coefficient_colorcamera import calculate_sph_cyl_coefficinet

class CalculateSphCylCoefficientColorCameraThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            calculate_sph_cyl_coefficinet(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号


class CalculateSphCylCoefficientColorCameraWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CalculateSphCylCoefficient_ColorCamera")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.file_name="sph_cyl_coefficient.xlsx"
        self.exposure_map_obj={}
        self.nd_list=['ND0','ND1','ND2','ND3','ND4','ND5']
        self.xyz_list=['X','Y','Z','Clear']
        self.binning_selector=['Logic','Sensor']
        self.binning_mode=['AVERAGE','SUM']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self._init_ui()

        # 标识当前流程是否正在运行
        self.is_running=False

    def _init_ui(self):
        grid_layout = QGridLayout()

        self.label_nd_selector = QLabel("ND:")
        grid_layout.addWidget(self.label_nd_selector,0,0)

        self.line_edit_nd_selector = QComboBox()
        self.line_edit_nd_selector.addItems(self.nd_list)
        self.line_edit_nd_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_nd_selector,1,0)

        self.label_xyz_selector=QLabel("XYZ:")
        grid_layout.addWidget(self.label_xyz_selector,2,0)

        self.line_edit_xyz_selector = QComboBox()
        self.line_edit_xyz_selector.addItems(self.xyz_list)
        self.line_edit_xyz_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyz_selector,3,0)

        self.label_exposure_time=QLabel("曝光时间(ms):")
        grid_layout.addWidget(self.label_exposure_time,4,0)
        self.line_edit_exposure_time=QLineEdit()
        self.line_edit_exposure_time.setText("100")
        self.line_edit_exposure_time.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_exposure_time,5,0)

        self.label_avg_count=QLabel("avg_count:")
        grid_layout.addWidget(self.label_avg_count,6,0)
        self.line_edit_avg_count=QLineEdit()
        self.line_edit_avg_count.setText("10")
        self.line_edit_avg_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_avg_count,7,0)

        self.label_sphlist = QLabel("sph列表, (例如: -6 -5 -4 -3 -2 -1 0 1 2 3 4 5 6), 以空格隔开")
        grid_layout.addWidget(self.label_sphlist,8,0)
        self.line_edit_sphlist = QLineEdit()
        self.line_edit_sphlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_sphlist,9,0)
        

        self.label_cyllist = QLabel("cyl列表, (例如: -4 -3.5 -3 -2.5 -2 -1.5 -1 -0.5 0), 以空格隔开")
        grid_layout.addWidget(self.label_cyllist,10,0)
        self.line_edit_cyllist = QLineEdit()
        self.line_edit_cyllist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_cyllist,11,0)

        group_box1=QGroupBox("roi设置(calculate M matrix)")
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
        grid_layout.addWidget(group_box1, 12, 0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径:")
        grid_layout.addWidget(self.label_path, 13, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 14, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 14, 1)
        

        self.btn_capture = QPushButton("计算系数")
        self.btn_capture.clicked.connect(self.start_calculate)
        grid_layout.addWidget(self.btn_capture, 15, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,16,0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

    def start_calculate(self):
        try:
            self.status_label.setText("<span style='color: green;'>状态: 正在进行系数计算...</span>")  # 更新状态
            self.btn_capture.setEnabled(False)
            self.is_running=True
            self.nd=self.get_current_filter(self.line_edit_nd_selector.currentText())
            self.xyz=self.get_current_filter(self.line_edit_xyz_selector.currentText())
            self.exposure_time=float(self.line_edit_exposure_time.text())
            self.exposure=mlcm.pyExposureSetting(mlcm.ExposureMode.Fixed,self.exposure_time)
            self.avg_count=int(self.line_edit_avg_count.text())
            self.sph_list=[float(sph) for sph in self.line_edit_sphlist.text().strip().split()]
            self.cyl_list=[float(cyl) for cyl in self.line_edit_cyllist.text().strip().split()]
            x=int(self.line_edit_x_input.text())
            y=int(self.line_edit_y_input.text())
            width=int(self.line_edit_width_input.text())
            height=int(self.line_edit_height_input.text())
            self.roi=mlcm.pyCVRect(x,y,width,height)
            self.save_path=self.line_edit_path.text()
            # calculate_sph_cyl_coefficinet(
            #     colorimeter=self.colorimeter,
            #     save_path=self.save_path,
            #     file_name=self.file_name,
            #     nd=self.nd,
            #     xyz=self.xyz,
            #     exposure=self.exposure,
            #     avg_count=self.avg_count,
            #     sph_list=self.sph_list,
            #     cyl_list=self.cyl_list,
            #     roi=self.roi
            # )
            parameters={
                'colorimeter': self.colorimeter,
                'save_path':self.save_path,
                'file_name':self.file_name,
                'nd':self.nd,
                'xyz':self.xyz,
                'exposure':self.exposure,
                'avg_count':self.avg_count,
                'sph_list':self.sph_list,
                'cyl_list':self.cyl_list,
                'roi':self.roi
            }
            self.calculate_thread=CalculateSphCylCoefficientColorCameraThread(parameters)
            self.calculate_thread.finished.connect(self.on_calculate_finished)
            self.calculate_thread.error.connect(self.on_calculate_error)
            self.calculate_thread.status_update.connect(self.update_status)
            self.calculate_thread.start() # 启动线程
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False
            
    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_calculate_finished(self):
        QMessageBox.information(self,"MLColorimeter","计算完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 计算完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_calculate_error(self,error_message):
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
    
    def get_current_filter(self, selected_format):
        format_mapping={
            'ND0':mlcm.MLFilterEnum.ND0,
            'ND1':mlcm.MLFilterEnum.ND1,
            'ND2':mlcm.MLFilterEnum.ND2,
            'ND3':mlcm.MLFilterEnum.ND3,
            'ND4':mlcm.MLFilterEnum.ND4,
            'X':mlcm.MLFilterEnum.X,
            'Y':mlcm.MLFilterEnum.Y,
            'Z':mlcm.MLFilterEnum.Z,
            'Clear':mlcm.MLFilterEnum.Clear,
        }
        filter_enum=format_mapping.get(selected_format)
        return filter_enum
        
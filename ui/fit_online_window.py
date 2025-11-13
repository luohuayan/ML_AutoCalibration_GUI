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
    QFormLayout,
    QListWidget
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
from scripts.circle_fit_online import circle_fit_online
from scripts.polynomial_fit_online import polynomial_fit_online

class FitOnlineThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            circle_fit_online(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class PolynomialFitOnlineThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            polynomial_fit_online(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class FitOnlineWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("fit online")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.roi_list=[]
        self.vrange={}
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self.fit_type=['circle','polynomial']
        self._init_ui()

        # 标识当前流程是否正在进行
        self.is_running=False

    def _init_ui(self):
        grid_layout = QGridLayout()
        group_box0=QGroupBox("相机设置")
        from_layout0=QFormLayout()
        self.label_binnlist = QLabel(" binning：")
        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_binnlist.setPlaceholderText("0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16")
        from_layout0.addRow(self.label_binnlist, self.line_edit_binnlist)

        self.label_pixel_format = QLabel(" pixel_format：")
        self.line_edit_pixel_format = QComboBox()
        self.line_edit_pixel_format.addItems(self.pixel_format)
        self.line_edit_pixel_format.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_pixel_format.setCurrentText("MLMono12")
        from_layout0.addRow(self.label_pixel_format,self.line_edit_pixel_format)

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

        self.label_cyllist = QLabel("cyl列表, (例如: -4 -3.5 -3 -2.5 -2 -1.5 -1 -0.5 0), 以空格隔开")
        grid_layout.addWidget(self.label_cyllist,5,0)
        self.line_edit_cyllist = QLineEdit()
        self.line_edit_cyllist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_cyllist,6,0)
        
        self.label_axislist = QLabel("axis列表, (例如: 0 15 30 45 60 75 90 105 120 135 150 165), 以空格隔开")
        grid_layout.addWidget(self.label_axislist,7,0)
        self.line_edit_axislist = QLineEdit()
        self.line_edit_axislist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_axislist,8,0)

        group_box1=QGroupBox("roi设置")
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
        grid_layout.addWidget(group_box1, 9, 0)

        self.label_fit_type = QLabel("fit_type：")
        grid_layout.addWidget(self.label_fit_type, 10, 0)

        self.cb_fit_type = QComboBox()
        self.cb_fit_type.addItems(self.fit_type)
        self.cb_fit_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.cb_fit_type, 11, 0)


        self.label_fit_path = QLabel()
        self.label_fit_path.setText("fit_file path:")
        grid_layout.addWidget(self.label_fit_path, 12, 0)

        self.line_edit_fit_path = QLineEdit()
        self.line_edit_fit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_fit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_fit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_fit_path, 13, 0)

        self.btn_browse1 = QPushButton("浏览...")
        self.btn_browse1.clicked.connect(self._open_file_dialog)
        grid_layout.addWidget(self.btn_browse1, 13, 1)

        self.label_path = QLabel()
        self.label_path.setText("保存路径:")
        grid_layout.addWidget(self.label_path, 14, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 15, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 15, 1)

        self.btn_capture = QPushButton("开始")
        self.btn_capture.clicked.connect(self.start_fit_online)
        grid_layout.addWidget(self.btn_capture, 16, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,17,0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

    def start_fit_online(self):
        try:
            self.pixel_format=self.get_current_pixel_format()
            self.binn=mlcm.Binning(int(self.line_edit_binnlist.text().strip()))
            self.fit_file_path=self.line_edit_fit_path.text()
            self.out_path=self.line_edit_path.text()
            nd_enum=[int(nd) for nd in self.line_edit_ndlist.text().strip().split()]
            self.nd_list=[mlcm.MLFilterEnum(nd) for nd in nd_enum]
            xyz_enum=[int(xyz) for xyz in self.line_edit_xyzlist.text().strip().split()]
            self.xyz_list=[mlcm.MLFilterEnum(xyz) for xyz in xyz_enum]
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
                'nd_list':self.nd_list,
                'xyz_list':self.xyz_list,
                'binn':self.binn,
                'pixel_format':self.pixel_format,
                'cyl_list':self.cyl_list,
                'axis_list':self.axis_list,
                'roi':self.roi,
                'fit_file_path':self.fit_file_path,
                'out_path':self.out_path
            }
            if self.cb_fit_type.currentText=='circle':
                self.fit_online_thread=FitOnlineThread(parameters)
                self.fit_online_thread.finished.connect(self.on_fitonline_finished)
                self.fit_online_thread.error.connect(self.on_fitoneline_error)
                self.fit_online_thread.status_update.connect(self.update_status)
                self.fit_online_thread.start()
            else:
                self.fit_online_thread=PolynomialFitOnlineThread(parameters)
                self.fit_online_thread.finished.connect(self.on_fitonline_finished)
                self.fit_online_thread.error.connect(self.on_fitoneline_error)
                self.fit_online_thread.status_update.connect(self.update_status)
                self.fit_online_thread.start()

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_fitonline_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_fitoneline_error(self,error_message):
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
    
    def _open_file_dialog(self):
        file_path,_=QFileDialog.getOpenFileName(
            self,
            "选择JSON文件",
            self.default_path if self.default_path else "",
            "JSON Files (*.json);;All Files (*)"  # 文件过滤器，仅显示json文件
        )
        if file_path:
            self.line_edit_fit_path.setText(file_path)
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
    

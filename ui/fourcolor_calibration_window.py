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
    QCheckBox,
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
from scripts.fourcolor_calibration import fourcolor_calibration_capture, fourcolor_calibration_calculate
from ui.exposureconfig_window import ExposureConfigWindow

class FourColorCalabrationWindow(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("fourcolor calibration")
        self.setGeometry(200,200,800,500)
        self.colorimeter=AppConfig.get_colorimeter()
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.exposure_mode=['Auto','Fixed']
        self.binning_selector=['Logic','Sensor']
        self.binning_mode=['AVERAGE','SUM']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self.exposure_map_obj = {}
        self._init_ui()
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

        self.btn_load_config = QPushButton("曝光时间配置")
        self.btn_load_config.clicked.connect(self.load_exposure_config)
        grid_layout.addWidget(self.btn_load_config, 4, 1)

        self.label_avg_count=QLabel("avg_count:(count to calculate average image for one color filter)")
        grid_layout.addWidget(self.label_avg_count,5,0)
        self.line_edit_avg_count=QLineEdit()
        self.line_edit_avg_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_avg_count, 6, 0)

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
        self.line_edit_width_input.setText("100")
        self.line_edit_width_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_height_input=QLabel("height_input: ")
        self.line_edit_height_input = QLineEdit()
        self.line_edit_height_input.setText("100")
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
        grid_layout.addWidget(group_box1, 7, 0)

        self.label_is_do_ffc=QLabel("is_do_ffc:(是否在计算前进行平场矫正)")
        grid_layout.addWidget(self.label_is_do_ffc,8,0)
        self.checkbox_is_do_ffc=QCheckBox()
        self.checkbox_is_do_ffc.setChecked(True)
        self.checkbox_is_do_ffc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.checkbox_is_do_ffc,9,0)


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

        self.label_NMatrix_path = QLabel()
        self.label_NMatrix_path.setText("NMatrix路径:(NMatrix_xyL.json contains the specbos data of your light source)")
        grid_layout.addWidget(self.label_NMatrix_path, 12, 0)

        self.line_edit_NMatrix_path= QLineEdit()
        self.line_edit_NMatrix_path.setReadOnly(True)  # 设置为只读
        self.line_edit_NMatrix_path.setPlaceholderText("未选择文件夹")
        self.line_edit_NMatrix_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_NMatrix_path, 13, 0)

        self.btn_NMatrix_path = QPushButton("浏览...")
        self.btn_NMatrix_path.clicked.connect(self._open_file_dialog)
        grid_layout.addWidget(self.btn_NMatrix_path, 13, 1)

        self.btn_start_calibration=QPushButton("四色标定")
        self.btn_start_calibration.clicked.connect(self._start_calibration)
        grid_layout.addWidget(self.btn_start_calibration,14,0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

    def _start_calibration(self):
        try:
            self.pixel_format=self.get_current_pixel_format()
            self.binn_selector=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.binn=mlcm.Binning(int(self.line_edit_binn.text().strip()))
            nd_enum=[int(nd) for nd in self.line_edit_ndlist.text().strip().split()]
            self.nd_list=[mlcm.MLFilterEnum(nd) for nd in nd_enum]
            xyz_enum=[int(xyz) for xyz in self.line_edit_xyzlist.text().strip().split()]
            self.xyz_list=[mlcm.MLFilterEnum(xyz) for xyz in xyz_enum]
            self.avg_count=int(self.line_edit_avg_count.text().strip())
            x=int(self.line_edit_x_input.text().strip())
            y=int(self.line_edit_y_input.text().strip())
            width=int(self.line_edit_width_input.text().strip())
            height=int(self.line_edit_height_input.text().strip())
            self.roi=mlcm.pyCVRect(x,y,width,height)
            self.save_path=self.line_edit_path.text().strip()
            self.nmatrix_path=self.line_edit_NMatrix_path.text().strip()
            self.is_do_ffc=self.checkbox_is_do_ffc.isChecked()
            self.light_source_list=["R", "G", "B", "W"]
            for nd in self.nd_list:
                for light_source in self.light_source_list:
                    temp = QMessageBox.information(self,"提示",f"请先切换到{light_source}光",QMessageBox.Ok)
                    if temp==QMessageBox.Ok:
                        exposure_map=self.exposure_map_obj[nd]
                        fourcolor_calibration_capture(
                            colorimeter=self.colorimeter,
                            binn_selector=self.binn_selector,
                            binn_mode=self.binn_mode,
                            binn=self.binn,
                            pixel_format=self.pixel_format,
                            save_path=self.save_path,
                            light_source=light_source,
                            nd=nd,
                            avg_count=self.avg_count,
                            exposure_map=exposure_map,
                            roi=self.roi,
                            is_do_ffc=self.is_do_ffc
                        )
                    else:
                        return
                fourcolor_calibration_calculate(
                    colorimeter=self.colorimeter,
                    save_path=self.save_path,
                    nd=nd,
                    NMatrix_path=self.nmatrix_path
                )
            
            QMessageBox.information(self,"提示","流程结束",QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

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

    def _open_file_dialog(self):
        file_path,_=QFileDialog.getOpenFileName(
            self,
            "选择NMatrix JSON文件",
            self.default_path if self.default_path else "",
            "JSON Files (*.json);;All Files (*)"  # 文件过滤器，仅显示json文件
        )
        if file_path:
            self.line_edit_NMatrix_path.setText(file_path)
        else:
            QMessageBox.critical(self,"MLColorimeter","选择路径错误",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
    
    def load_exposure_config(self):
        try:
            nd_list=self.line_edit_ndlist.text().strip().split()
            xyz_list=self.line_edit_xyzlist.text().strip().split()
            self.exposure_config_window = ExposureConfigWindow(nd_list,xyz_list)
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
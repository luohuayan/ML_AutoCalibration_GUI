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
from scripts.mono_calibration import mono_calibration
from ui.settings import SettingsWindow

class MonoCalibrationWindow(QWidget):
    # path_changed = pyqtSignal(str)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("mono calibration")
        self.setGeometry(200, 200, 800, 500)
        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.select_path=path
        self.file_name = "mono_calibration.xlsx"
        self._init_ui()

    def _init_ui(self):
        grid_layout = QGridLayout()

        self.label_aperture = QLabel()
        self.label_aperture.setText("光阑(mm): 例如：3mm")
        grid_layout.addWidget(self.label_aperture, 0, 0)
        self.line_edit_aperture = QLineEdit()
        self.line_edit_aperture.setText("3mm")
        self.line_edit_aperture.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_aperture, 1, 0)

        self.label_ndlist = QLabel()
        self.label_ndlist.setText("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 2, 0)
        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 3, 0)

        self.label_xyzlist = QLabel()
        self.label_xyzlist.setText("xyz列表, (1: X, 2: Y, 3: Z, 10: Clear), 以空格隔开")
        grid_layout.addWidget(self.label_xyzlist, 4, 0)
        self.checkbox_exist_xyz=QCheckBox("无xyz滤光片")
        self.checkbox_exist_xyz.stateChanged.connect(self.on_xyz_checkbox_changed)
        grid_layout.addWidget(self.checkbox_exist_xyz,4,1)


        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 5, 0)

        self.label_xyzlist_lum=QLabel()
        self.label_xyzlist_lum.setText("输入对应xyz列表下的亮度, 以空格隔开(无xyz滤光片时只输入一个亮度值即可)")
        grid_layout.addWidget(self.label_xyzlist_lum, 6, 0)
        self.line_edit_xyzlist_lum = QLineEdit()
        self.line_edit_xyzlist_lum.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        grid_layout.addWidget(self.line_edit_xyzlist_lum, 7, 0)

        self.label_radiance_lum=QLabel()
        self.label_radiance_lum.setText("Radiance：")
        grid_layout.addWidget(self.label_radiance_lum, 8, 0)
        self.line_edit_radiance_lum = QLineEdit()
        self.line_edit_radiance_lum.setText("1000")
        self.line_edit_radiance_lum.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        grid_layout.addWidget(self.line_edit_radiance_lum, 9, 0)

        self.label_gray_range=QLabel()
        self.label_gray_range.setText("灰度值(例如: 0.5,0.8)，多个灰度值以空格隔开")
        grid_layout.addWidget(self.label_gray_range, 10, 0)
        self.line_edit_gray_range = QLineEdit()
        self.line_edit_gray_range.setText("0.8")
        self.line_edit_gray_range.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_gray_range, 11, 0)

        self.label_image_size = QLabel()
        self.label_image_size.setText("图像中心点坐标x y（打开相机软件查看）：例如像素为13376 9528，则中心点为6688 4764以空格隔开")
        grid_layout.addWidget(self.label_image_size, 12, 0)
        self.line_edit_image_size = QLineEdit()
        self.line_edit_image_size.setText("6688 4764")
        self.line_edit_image_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_image_size, 13, 0)

        self.label_roi_size = QLabel()
        self.label_roi_size.setText("ROI宽高：例如200 200，以空格隔开")
        grid_layout.addWidget(self.label_roi_size, 14, 0)
        self.line_edit_roi_size = QLineEdit()
        self.line_edit_roi_size.setText("200 200")
        self.line_edit_roi_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_roi_size, 15, 0)

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
        grid_layout.addLayout(h_layout, 16, 0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径(excel保存位置):")
        grid_layout.addWidget(self.label_path, 17, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 18, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 18, 1)

        self.label_path=QLabel()
        self.label_path.setText("配置路径（eye1）")
        grid_layout.addWidget(self.label_path, 19, 0)
        self.line_edit_eye1_path=QLineEdit()
        self.line_edit_eye1_path.setReadOnly(True)
        self.line_edit_eye1_path.setText(self.select_path)
        grid_layout.addWidget(self.line_edit_eye1_path,20,0)


        self.btn_capture = QPushButton("单色定标")
        self.btn_capture.clicked.connect(self.start_mono_calibration)
        grid_layout.addWidget(self.btn_capture, 21, 0)

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

    def on_xyz_checkbox_changed(self):
        is_checked = self.checkbox_exist_xyz.isChecked()
        self.line_edit_xyzlist.setEnabled(not is_checked)
        self.line_edit_xyzlist.setText("") if is_checked else None


    def start_mono_calibration(self):
        try:
            
            # self.path_changed.connect(self.out_path_changed)
            self.eye1_path=self.line_edit_eye1_path.text()
            self.lum_dict={}
            self.luminance_no_xyz=0.0
            if (self.checkbox_exist_xyz.isChecked()):
                self.xyz_list=[]
                lum_list=self.line_edit_xyzlist_lum.text().split()
                self.luminance_no_xyz=float(lum_list[0]) if len(lum_list)>0 else 0.0
            else:
                self.xyz_list=self.line_edit_xyzlist.text().split()
                self.lum_dict=self.generate_luminance_dict()
            self.aperture = self.line_edit_aperture.text()
            self.nd_list=self.line_edit_ndlist.text().split()
            self.light_source=self.rgbw_btngroup.checkedButton().text()
            self.radiance=float(self.line_edit_radiance_lum.text())
            self.gray_list=self.line_edit_gray_range.text().split()
            self.image_point=self.line_edit_image_size.text().split()
            self.roi_size=self.line_edit_roi_size.text().split()
            self.out_path=self.line_edit_path.text()
            mono_calibration(self.colorimeter,self.nd_list,self.xyz_list,self.gray_list,self.aperture,self.light_source,
                            self.lum_dict,self.luminance_no_xyz,self.radiance,self.eye1_path,self.out_path,self.image_point,self.roi_size)
            
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
        

    def generate_luminance_dict(self):
        lum_dict = {}
        try:
            xyzlist = self.line_edit_xyzlist.text().strip().split()
            xyzlist_lum = self.line_edit_xyzlist_lum.text().strip().split()
            for i,xyz in enumerate(xyzlist):
                if xyz=='1':
                    lum_dict[mlcm.MLFilterEnum.X]=float(xyzlist_lum[i])
                elif xyz=='2':
                    lum_dict[mlcm.MLFilterEnum.Y]=float(xyzlist_lum[i])
                elif xyz=='3':
                    lum_dict[mlcm.MLFilterEnum.Z]=float(xyzlist_lum[i])
                elif xyz=='10':
                    lum_dict[mlcm.MLFilterEnum.Clear]=float(xyzlist_lum[i])
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","生成亮度字典异常" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
        return lum_dict
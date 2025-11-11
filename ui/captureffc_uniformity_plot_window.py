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
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QDialog,
    QComboBox,
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
from scripts.captureffc_calUniformity_plot import (
    cal_synthetic_mean_images, capture_ffc_images, cal_uniformity)

from ui.rx_config_window import RXConfigWindow
from ui.roi_config_window import ROIConfigWindow
from ui.exposureconfig_window import ExposureConfigWindow


class CaptureFFCThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self,parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            capture_ffc_images(status_callback=self.status_update.emit,**self.parameters)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

class CalSyntheticThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self,parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            cal_synthetic_mean_images(status_callback=self.status_update.emit,**self.parameters)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

class CalUniformityThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self,parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            cal_uniformity(status_callback=self.status_update.emit,**self.parameters)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


class CaptureFFC_CalUniformity_Plot_Window(QDialog):
    path_changed = pyqtSignal(str)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "capture ffc images; calculate ffc, fourcolor uniformity; generate plot")
        self.setGeometry(200, 200, 800, 700)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.eye1_path=path
        self.rx_dict={}
        self.roi_dict={}
        self.exposure_map_obj={}
        self.file_name = ""
        self.exposure_mode=['Auto','Fixed']
        self.module_id = 1
        self._init_ui()
        self.is_running=False
        self.threads=[] # 存储活动线程

    def _init_ui(self):
        grid_layout = QGridLayout()

        self.label_times = QLabel()
        self.label_times.setText("多帧平均次数: ")
        grid_layout.addWidget(self.label_times, 0, 0)

        self.line_edit_times = QLineEdit()
        self.line_edit_times.setText("1")
        self.line_edit_times.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_times, 1, 0)

        self.label_binn = QLabel()
        self.label_binn.setText(
            "平场图像采集 binning: (0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16)")
        grid_layout.addWidget(self.label_binn, 2, 0)

        self.line_edit_binn = QLineEdit()
        self.line_edit_binn.setText("0")
        self.line_edit_binn.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_binn, 3, 0)

        self.label_binnlist = QLabel()
        self.label_binnlist.setText(
            "计算FFC,FourColor均匀性 binning列表, (0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16), 以空格隔开"
        )
        grid_layout.addWidget(self.label_binnlist, 4, 0)

        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_binnlist, 5, 0)

        self.label_ndlist = QLabel()
        self.label_ndlist.setText(
            "nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 6, 0)

        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 7, 0)

        self.label_xyzlist = QLabel()
        self.label_xyzlist.setText(
            "xyz列表, (1: X, 2: Y, 3: Z, 10: Clear), 以空格隔开")
        grid_layout.addWidget(self.label_xyzlist, 8, 0)

        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 9, 0)

        self.btn_load_config = QPushButton("曝光时间配置")
        self.btn_load_config.clicked.connect(self.load_exposure_config)
        grid_layout.addWidget(self.btn_load_config, 9, 1)

        self.label_path = QLabel()
        self.label_path.setText("数据输出路径:")
        grid_layout.addWidget(self.label_path, 10, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 11, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 11, 1)

        self.cb_useRX = QCheckBox()
        self.cb_useRX.setText("启用RX")
        self.cb_useRX.setChecked(False)
        self.cb_useRX.stateChanged.connect(self._useRX_state_changed)
        grid_layout.addWidget(self.cb_useRX, 12, 0)

        self.label_sphlist = QLabel()
        self.label_sphlist.setText(
            "平场图像采集 sph列表, (例如: -6 -5 -4 -3 -2 -1 0 1 2 3 4 5 6), 以空格隔开")
        grid_layout.addWidget(self.label_sphlist, 13, 0)

        self.line_edit_sphlist = QLineEdit()
        self.line_edit_sphlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_sphlist, 14, 0)

        self.label_cyllist = QLabel()
        self.label_cyllist.setText(
            "平场图像采集 cyl列表, (例如: -4 -3.5 -3 -2.5 -2 -1.5 -1 -0.5 0), 以空格隔开")
        grid_layout.addWidget(self.label_cyllist, 15, 0)

        self.line_edit_cyllist = QLineEdit()
        self.line_edit_cyllist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_cyllist, 16, 0)

        self.label_axislist = QLabel()
        self.label_axislist.setText(
            "平场图像采集 axis列表, (例如: 0 15 30 45 60 75 90 105 120 135 150 165), 以空格隔开")
        grid_layout.addWidget(self.label_axislist, 17, 0)

        self.line_edit_axislist = QLineEdit()
        self.line_edit_axislist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_axislist, 18, 0)

        main_layout=QVBoxLayout()

        h_layout = QHBoxLayout()
        self.cb_captureffc = QCheckBox()
        self.cb_captureffc.setText("启用FFC拍图")
        self.cb_captureffc.setChecked(False)
        self.cb_captureffc.stateChanged.connect(self._captureFFC_config)
        h_layout.addWidget(self.cb_captureffc)

        self.cb_calculate_synthetic = QCheckBox()
        self.cb_calculate_synthetic.setText("计算FFC synthetic图像")
        self.cb_calculate_synthetic.setChecked(False)
        h_layout.addWidget(self.cb_calculate_synthetic)

        self.cb_calculate_uniformity = QCheckBox()
        self.cb_calculate_uniformity.setText("计算FFC FourColor均匀性")
        self.cb_calculate_uniformity.setChecked(False)
        self.cb_calculate_uniformity.stateChanged.connect(self._useRX_config)
        h_layout.addWidget(self.cb_calculate_uniformity)

        h_layout0 = QHBoxLayout()
        self.btn_roi_config=QPushButton("ROI列表配置")
        self.btn_roi_config.clicked.connect(self._roi_config)
        h_layout0.addWidget(self.btn_roi_config)

        self.btn_rx_config=QPushButton("RX列表配置")
        self.btn_rx_config.clicked.connect(self._rx_config)
        h_layout0.addWidget(self.btn_rx_config)

        main_layout.addLayout(h_layout)
        main_layout.addLayout(h_layout0)
        grid_layout.addLayout(main_layout, 19, 0)

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
        self.rgbw_btngroup.idClicked.connect(self._rgbw_changed)

        h_layout.addWidget(self.cb_R)
        h_layout.addWidget(self.cb_G)
        h_layout.addWidget(self.cb_B)
        h_layout.addWidget(self.cb_W)
        grid_layout.addLayout(h_layout, 20, 0)

        self.label_pixelcount = QLabel()
        self.label_pixelcount.setText("Plot计算, 水平方向和竖直方向像素个数: ")
        grid_layout.addWidget(self.label_pixelcount, 21, 0)

        self.line_edit_pixelcount = QLineEdit()
        self.line_edit_pixelcount.setText("7200")
        self.line_edit_pixelcount.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_pixelcount, 22, 0)

        self.label_vrange = QLabel()
        self.label_vrange.setText("Plot图坐标轴范围: 例如: 1500 3900")
        grid_layout.addWidget(self.label_vrange, 23, 0)

        self.line_edit_vrange = QLineEdit()
        self.line_edit_vrange.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_vrange, 24, 0)

        self.btn_capture = QPushButton("开始拍图及计算FFC,FourColor均匀性")
        self.btn_capture.clicked.connect(self._start_capture_calculate)
        grid_layout.addWidget(self.btn_capture, 25, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,26,0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum,
                            QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

        self.label_sphlist.hide()
        self.line_edit_sphlist.hide()
        self.label_cyllist.hide()
        self.line_edit_cyllist.hide()
        self.label_axislist.hide()
        self.line_edit_axislist.hide()
        self.cb_calculate_synthetic.hide()
        self.btn_rx_config.hide()
        self.btn_roi_config.hide()

    def _captureFFC_config(self):
        if self.cb_captureffc.isChecked():
            QMessageBox.information(self,"MLColorimeter","请点击曝光时间配置设置不同nd下xyz滤光片的曝光时间",QMessageBox.Ok)
        else:
            return
        
    def _useRX_config(self):
        if self.cb_calculate_uniformity.isChecked():
            self.btn_rx_config.show()
            self.btn_roi_config.show()
            QMessageBox.information(self,"MLColorimeter","请依次点击ROI列表配置按钮和RX列表配置设置ROI和RX",QMessageBox.Ok)
        else:
            self.btn_rx_config.hide()
            self.btn_roi_config.hide()

    def _open_folder_dialog(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.out_path = folder_path
            self.line_edit_path.setText(folder_path)
        else:
            QMessageBox.critical(self, "MLColorimeter", "选择路径错误",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    
    def load_exposure_config(self):
        try:
            nd_list=self.line_edit_ndlist.text().strip().split()
            xyz_list=self.line_edit_xyzlist.text().strip().split()
            if not nd_list or not xyz_list:
                QMessageBox.warning(self,"MLColorimeter","nd列表或xyz列表不能为空",QMessageBox.Ok)
                return
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

    def _rx_config(self):
        try:
            nd_text=self.line_edit_ndlist.text().strip().split()
            if not nd_text:
                QMessageBox.warning(self,"MLColorimeter","ND列表不能为空",QMessageBox.Ok)
                return
            nd_enum=[int(nd) for nd in self.line_edit_ndlist.text().strip().split()]
            nd_list=[mlcm.MLFilterEnum(nd) for nd in nd_enum]
            self.rx_config_window = RXConfigWindow(nd_list)
            # 连接信号
            self.rx_config_window.config_saved.connect(self.update_rx_config)
            self.rx_config_window.exec_()
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def _roi_config(self):
        try:
            binn_text=self.line_edit_binnlist.text().strip().split()
            if not binn_text:
                QMessageBox.warning(self,"MLColorimeter","binning列表不能为空",QMessageBox.Ok)
                return
            binn_enum=[int(binn) for binn in self.line_edit_binnlist.text().strip().split()]
            binn_list=[mlcm.Binning(binn) for binn in binn_enum]
            self.roi_config_window = ROIConfigWindow(binn_list)
            # 连接信号
            self.roi_config_window.roi_config_saved.connect(self.update_roi_config)
            self.roi_config_window.exec_()
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)


    def update_rx_config(self,rx_map):
        self.rx_dict={}
        try:
            for nd_str,rx_list in rx_map.items():
                nd_enum=mlcm.str_to_MLFilterEnum(nd_str)
                self.rx_dict[nd_enum]=rx_list
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
        
    def update_roi_config(self,roi_map):
        self.roi_dict={}
        try:
            for binn,roi_list in roi_map.items():
                self.roi_dict[binn]=roi_list
            pass
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def _useRX_state_changed(self):
        if self.cb_useRX.isChecked():
            self.label_sphlist.show()
            self.line_edit_sphlist.show()
            self.label_cyllist.show()
            self.line_edit_cyllist.show()
            self.label_axislist.show()
            self.line_edit_axislist.show()
            self.cb_calculate_synthetic.show()
        else:
            self.label_sphlist.hide()
            self.line_edit_sphlist.hide()
            self.label_cyllist.hide()
            self.line_edit_cyllist.hide()
            self.label_axislist.hide()
            self.line_edit_axislist.hide()
            self.cb_calculate_synthetic.hide()

    def _rgbw_changed(self, btn_id):
        obj = {1: "R", 2: "G", 3: "B", 4: "W"}
        self.light_source = obj[btn_id]
        self.colorimeter.ml_bino_manage.ml_get_module_by_id(
            self.module_id).ml_set_light_source(self.light_source)

    def _start_capture_calculate(self):
        try:
            self.status_label.setText("<span style='color: green;'>状态: 正在进行拍图或计算...</span>")  # 更新状态
            self.btn_capture.setEnabled(False)
            self.is_running=True
            self.capture_times = int(self.line_edit_times.text())

            self.binn = mlcm.Binning(int(self.line_edit_binn.text()))
            self.binnlist = self.line_edit_binnlist.text().split()
            self.binnlist = [mlcm.Binning(int(binn)) for binn in self.binnlist]

            self.ndlist = self.line_edit_ndlist.text().split()
            self.ndlist = [mlcm.MLFilterEnum(int(nd)) for nd in self.ndlist]

            self.xyzlist = self.line_edit_xyzlist.text().split()
            self.xyzlist = [mlcm.MLFilterEnum(int(xyz)) for xyz in self.xyzlist]

            self.useRX = self.cb_useRX.isChecked()
            self.sphlist = self.line_edit_sphlist.text().split()
            self.cyllist = self.line_edit_cyllist.text().split()
            self.axislist = self.line_edit_axislist.text().split()

            self.capture_ffc = self.cb_captureffc.isChecked()
            self.cal_synthetic = self.cb_calculate_synthetic.isChecked()
            self.cal_uniformity = self.cb_calculate_uniformity.isChecked()

            self.pixelcount = int(self.line_edit_pixelcount.text())
            self.vrange = [int(vrange) for vrange in self.line_edit_vrange.text().split()]

            # exposure map for calculate uniformity
            self.exposure_map = {
                mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100),
                mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100),
                mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100),
                mlcm.MLFilterEnum.Clear: mlcm.pyExposureSetting(
                    exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100)
            }
            self.start_capture_ffc()

        except Exception as e:
            QMessageBox.critical(self, "MLColorimeter", "exception" + e,
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False
            
    
    def start_capture_ffc(self):
        if self.cb_captureffc.isChecked():
            if not self.exposure_map_obj:
                QMessageBox.warning(self,"MLColorimeter","曝光时间未设置",QMessageBox.Ok)
                self.btn_capture.setEnabled(True)
                self.is_running=False
                return
            ffc_parameters={
                    'colorimeter': self.colorimeter,
                    'nd_list': self.ndlist,
                    'xyz_list':self.xyzlist,
                    'binn': self.binn,
                    'exposure_map': self.exposure_map_obj,
                    'capture_times': self.capture_times,
                    'save_path': self.eye1_path,
                    'use_RX': self.useRX,
                    'sph_list': self.sphlist,
                    'cyl_list': self.cyllist,
                    'axis_list': self.axislist
                }
            ffc_thread=CaptureFFCThread(ffc_parameters)
            self.threads.append(ffc_thread)  # 添加到活动线程列表
            ffc_thread.finished.connect(self.start_calculate_synthetic)
            ffc_thread.error.connect(self._on_capture_error)
            ffc_thread.status_update.connect(self.update_status)
            ffc_thread.start()
        else:
            self.start_calculate_synthetic()
    
    def start_calculate_synthetic(self):
        if self.useRX and self.cb_calculate_synthetic.isChecked():
            synthetic_parameters={
                'colorimeter': self.colorimeter,
                'nd_list': self.ndlist,
                'xyz_list': self.xyzlist,
                'save_path': self.out_path
            }
            synthetic_thread=CalSyntheticThread(synthetic_parameters)
            self.threads.append(synthetic_thread)
            synthetic_thread.finished.connect(self.start_calculate_uniformity)
            synthetic_thread.error.connect(self._on_capture_error)
            synthetic_thread.status_update.connect(self.update_status)
            synthetic_thread.start()
        else:
            self.start_calculate_uniformity()

    def start_calculate_uniformity(self):
        if self.cb_calculate_uniformity.isChecked():
            if not self.roi_dict:
                QMessageBox.warning(self,"MLColorimeter","ROI未配置",QMessageBox.Ok)
                self.btn_capture.setEnabled(True)
                self.is_running=False
                return
            if not self.rx_dict:
                QMessageBox.warning(self,"MLColorimeter","RX未配置",QMessageBox.Ok)
                self.btn_capture.setEnabled(True)
                self.is_running=False
                return
            uniformity_parameters={
                'colorimeter': self.colorimeter,
                'half_size': self.pixelcount/2,
                'vrange': self.vrange,
                'nd_list': self.ndlist,
                'xyz_list': self.xyzlist,
                'uniformity_path': self.out_path,
                'binn_list': self.binnlist,
                'exposure_map': self.exposure_map,
                'roi_dict': self.roi_dict,
                'use_RX': self.useRX,
                'rx_dict': self.rx_dict
            }
            uniformity_thread=CalUniformityThread(uniformity_parameters)
            self.threads.append(uniformity_thread)
            uniformity_thread.finished.connect(self.on_all_tasks_finished)
            uniformity_thread.error.connect(self._on_capture_error)
            uniformity_thread.status_update.connect(self.update_status)
            uniformity_thread.start()
        else:
            self.on_all_tasks_finished()
    
    def on_all_tasks_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识完成
        self.status_label.setText("<span style='color: green;'>状态: 所有任务完成！</span>")  # 更新状态
        

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def _on_capture_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def _on_capture_error(self,error_message):
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


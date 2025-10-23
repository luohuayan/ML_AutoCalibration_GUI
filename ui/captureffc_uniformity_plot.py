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
from scripts.captureffc_calUniformity_plot import (
    cal_synthetic_mean_images, capture_ffc_images, cal_uniformity)


class CaptureFFC_CalUniformity_Plot_Window(QDialog):
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "capture ffc images; calculate ffc, fourcolor uniformity; generate plot")
        self.setGeometry(200, 200, 800, 700)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.file_name = ""
        self.module_id = 1
        self._init_ui()

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

        h_layout = QHBoxLayout()
        self.cb_captureffc = QCheckBox()
        self.cb_captureffc.setText("启用FFC拍图")
        self.cb_captureffc.setChecked(False)
        h_layout.addWidget(self.cb_captureffc)

        self.cb_calculate_synthetic = QCheckBox()
        self.cb_calculate_synthetic.setText("计算FFC synthetic图像")
        self.cb_calculate_synthetic.setChecked(False)
        h_layout.addWidget(self.cb_calculate_synthetic)

        self.cb_calculate_uniformity = QCheckBox()
        self.cb_calculate_uniformity.setText("计算FFC FourColor均匀性")
        self.cb_calculate_uniformity.setChecked(False)
        h_layout.addWidget(self.cb_calculate_uniformity)

        grid_layout.addLayout(h_layout, 19, 0)

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

        self.btn_capture = QPushButton("开始拍图及计算FFC,FourColor均匀性")
        self.btn_capture.clicked.connect(self._start_capture_calculate)
        grid_layout.addWidget(self.btn_capture, 23, 0)

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
            if self.cb_captureffc.isChecked():
                QMessageBox.information(self, "MLColorimeter", "<b>请确认已在脚本中修改FFC拍图的曝光时间配置</b>",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

            if self.cb_calculate_uniformity.isChecked():
                QMessageBox.information(self, "MLColorimeter", "<b>请确认已在脚本中修改计算均匀性的曝光时间配置, rx list配置, roi设置</b>",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

            self.capture_times = int(self.line_edit_times.text())

            self.binn = mlcm.Binning(int(self.line_edit_binn.text()))
            self.binnlist = self.line_edit_binnlist.text().split()
            self.binnlist = [mlcm.Binning(int(binn)) for binn in self.binnlist]

            self.ndlist = self.line_edit_ndlist.text().split()
            self.ndlist = [mlcm.MLFilterEnum(int(nd)) for nd in self.ndlist]

            self.xyzlist = self.line_edit_xyzlist.text().split()
            self.xyzlist = [mlcm.MLFilterEnum(
                int(xyz)) for xyz in self.xyzlist]

            self.useRX = self.cb_useRX.isChecked()
            self.sphlist = self.line_edit_sphlist.text().split()
            self.cyllist = self.line_edit_cyllist.text().split()
            self.axislist = self.line_edit_axislist.text().split()

            self.capture_ffc = self.cb_captureffc.isChecked()
            self.cal_synthetic = self.cb_calculate_synthetic.isChecked()
            self.cal_uniformity = self.cb_calculate_uniformity.isChecked()
            self.pixelcount = int(self.line_edit_pixelcount.text())

            # different exposure map of nd while capture ffc images
            exposure_map_obj = {
                mlcm.MLFilterEnum.ND0: {
                    mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=13),
                    mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=11),
                    mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=34),
                    mlcm.MLFilterEnum.Clear: mlcm.pyExposureSetting(
                        exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=34)
                },
                mlcm.MLFilterEnum.ND1: {
                    mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=120),
                    mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=90),
                    mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=280),
                    mlcm.MLFilterEnum.Clear: mlcm.pyExposureSetting(
                        exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=34)
                },
                mlcm.MLFilterEnum.ND2: {
                    mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4556),
                    mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4054),
                    mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4999),
                    mlcm.MLFilterEnum.Clear: mlcm.pyExposureSetting(
                        exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=34)
                },
                mlcm.MLFilterEnum.ND3: {
                    mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4556),
                    mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4054),
                    mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4999),
                    mlcm.MLFilterEnum.Clear: mlcm.pyExposureSetting(
                        exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=34)
                },
                mlcm.MLFilterEnum.ND4: {
                    mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4556),
                    mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4054),
                    mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4999),
                    mlcm.MLFilterEnum.Clear: mlcm.pyExposureSetting(
                        exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=34)
                }
            }

            # exposure map for calculate uniformity
            exposure_map = {
                mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100),
                mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100),
                mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100),
                mlcm.MLFilterEnum.Clear: mlcm.pyExposureSetting(
                    exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100)
            }

            # different rx list of nd while calculate uniformity
            rx_dict = {
                mlcm.MLFilterEnum.ND0: [
                    [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4],
                    [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0],
                    [0, 90]
                ],
                mlcm.MLFilterEnum.ND1: [
                    [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4],
                    [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0],
                    [0, 90]
                ],
                mlcm.MLFilterEnum.ND2: [
                    [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4],
                    [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0],
                    [0, 90]
                ],
                mlcm.MLFilterEnum.ND3: [
                    [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4],
                    [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0],
                    [0, 90]
                ],

            }

            # different roi list of binn while calculate uniformity
            # x(upper left), y(upper left), width, height
            roi_dict = {
                mlcm.Binning.ONE_BY_ONE: [
                    mlcm.pyCVRect(3000, 2632, 400, 400),
                    mlcm.pyCVRect(3000, 4632, 400, 400),
                    mlcm.pyCVRect(3000, 6632, 400, 400),
                    mlcm.pyCVRect(4900, 2632, 400, 400),
                    mlcm.pyCVRect(4900, 4632, 400, 400),
                    mlcm.pyCVRect(4900, 6632, 400, 400),
                    mlcm.pyCVRect(7800, 2632, 400, 400),
                    mlcm.pyCVRect(7800, 4632, 400, 400),
                    mlcm.pyCVRect(7800, 6632, 400, 400),
                ],
                mlcm.Binning.TWO_BY_TWO: [
                    mlcm.pyCVRect(3000, 2632, 200, 200),
                    mlcm.pyCVRect(3000, 4632, 200, 200),
                    mlcm.pyCVRect(3000, 6632, 200, 200),
                    mlcm.pyCVRect(4900, 2632, 200, 200),
                    mlcm.pyCVRect(4900, 4632, 200, 200),
                    mlcm.pyCVRect(4900, 6632, 200, 200),
                    mlcm.pyCVRect(7800, 2632, 200, 200),
                    mlcm.pyCVRect(7800, 4632, 200, 200),
                    mlcm.pyCVRect(7800, 6632, 200, 200),
                ],
                mlcm.Binning.FOUR_BY_FOUR: [
                    mlcm.pyCVRect(800, 658, 100, 100),
                    mlcm.pyCVRect(800, 1158, 100, 100),
                    mlcm.pyCVRect(800, 1658, 100, 100),
                    mlcm.pyCVRect(1350, 658, 100, 100),
                    mlcm.pyCVRect(1350, 1158, 100, 100),
                    mlcm.pyCVRect(1350, 1658, 100, 100),
                    mlcm.pyCVRect(1900, 658, 100, 100),
                    mlcm.pyCVRect(1900, 1158, 100, 100),
                    mlcm.pyCVRect(1900, 1658, 100, 100),
                ]
            }

            self.eye1_path = self.colorimeter.ml_bino_manage.ml_get_module_by_id(
                self.module_id).ml_get_config_path()

            if self.capture_ffc:
                capture_ffc_images(
                    self.colorimeter,
                    self.ndlist,
                    self.xyzlist,
                    self.binn,
                    exposure_map_obj,
                    self.capture_times,
                    self.eye1_path,
                    self.useRX,
                    self.sphlist,
                    self.cyllist,
                    self.axislist
                )

            if self.useRX and self.cal_synthetic:
                cal_synthetic_mean_images(
                    self.colorimeter,
                    self.ndlist,
                    self.xyzlist,
                    self.out_path
                )

            if self.cal_uniformity:
                cal_uniformity(
                    self.colorimeter,
                    self.pixelcount/2,
                    self.ndlist,
                    self.xyzlist,
                    self.out_path,
                    self.binnlist,
                    exposure_map,
                    roi_dict,
                    self.useRX,
                    rx_dict
                )

            QMessageBox.information(
                self, "MLColorimeter", "finish", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        except Exception as e:
            QMessageBox.critical(self, "MLColorimeter", "exception" + e,
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

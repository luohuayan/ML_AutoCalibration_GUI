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
    QListWidget,
    QScrollArea
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
from scripts.serial_daogui_vid_focus_MTF import start_test_daogui,start_capture_image_vid,start_generate_roi_config,start_calibration_vid

class TestDaoGuiThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self):
        super().__init__()
    
    def run(self):
        try:
            start_test_daogui(status_callback=self.status_update.emit)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class CaptureImageVIDThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            start_capture_image_vid(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class DaoGuiVIDWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("daogui VID test")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.roi_list=[]
        self.vrange={}
        self.binning_selector=['Logic','Sensor']
        self.binning_mode=['AVERAGE','SUM']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self._init_ui()

        # 标识当前流程是否正在进行
        self.is_running=False

    def _init_ui(self):
        # 创建一个 QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 使滚动区域大小可变

        # 创建一个 QWidget 来放置所有控件
        scroll_area_content = QWidget()
        grid_layout = QGridLayout(scroll_area_content)

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

        group_box=QGroupBox("参数设置")
        from_layout=QFormLayout()

        self.label_vid_list=QLabel("vid list:(多个输入以空格分隔，示例150 200 300)")
        from_layout.addRow(self.label_vid_list)
        self.line_edit_vid_list = QLineEdit()
        self.line_edit_vid_list.setText("166 200 250 333 400 500 600 700 800 900 1000 1300 1600 2000")
        self.line_edit_vid_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.line_edit_vid_list)

        self.label_inf_pos=QLabel("inf_pos:")
        self.line_edit_inf_pos = QLineEdit()
        self.line_edit_inf_pos.setText("27.06")
        self.line_edit_inf_pos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.label_inf_pos,self.line_edit_inf_pos)

        self.label_pos_offset=QLabel("pos_offset:(公式infinity_position + 1000 / vid * 0.8 中的这个1000，减法请输入负数)")
        from_layout.addRow(self.label_pos_offset)
        self.line_edit_pos_offset = QLineEdit()
        self.line_edit_pos_offset.setText("1000")
        self.line_edit_pos_offset.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.line_edit_pos_offset)

        self.label_coef=QLabel("coef:(公式infinity_position + 1000 / vid * 0.8 中的这个0.8)")
        from_layout.addRow(self.label_coef)
        self.line_edit_coef = QLineEdit()
        self.line_edit_coef.setText("0.8")
        self.line_edit_coef.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.line_edit_coef)

        self.label_focal_length=QLabel("focal_length: ")
        self.line_edit_focal_length = QLineEdit()
        self.line_edit_focal_length.setText("40")
        self.line_edit_focal_length.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.label_focal_length,self.line_edit_focal_length)

        self.label_pixel_size=QLabel("pixel_size: ")
        self.line_edit_pixel_size = QLineEdit()
        self.line_edit_pixel_size.setText("0.00345")
        self.line_edit_pixel_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.label_pixel_size,self.line_edit_pixel_size)

        self.label_use_chess_mode=QLabel("use_chess_mode: ")
        self.line_edit_use_chess_mode = QCheckBox()
        self.line_edit_use_chess_mode.setChecked(True)
        self.line_edit_use_chess_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_use_lpmm_unit=QLabel("use_lpmm_unit: ")
        self.line_edit_use_lpmm_unit = QCheckBox()
        self.line_edit_use_lpmm_unit.setChecked(True)
        self.line_edit_use_lpmm_unit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        horizontal_layout3=QHBoxLayout()
        horizontal_layout3.addWidget(self.label_use_chess_mode)
        horizontal_layout3.addWidget(self.line_edit_use_chess_mode)
        horizontal_layout3.addWidget(self.label_use_lpmm_unit)
        horizontal_layout3.addWidget(self.line_edit_use_lpmm_unit)
        from_layout.addRow(horizontal_layout3)

        self.label_rough_step=QLabel("rough_step: ")
        self.line_edit_rough_step = QLineEdit()
        self.line_edit_rough_step.setText("0.1")
        self.line_edit_rough_step.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.label_rough_step,self.line_edit_rough_step)


        self.label_freq=QLabel("freq: ")
        self.line_edit_freq = QLineEdit()
        self.line_edit_freq.setText("3")
        self.line_edit_freq.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.label_freq,self.line_edit_freq)

        self.label_average_count=QLabel("average_count: ")
        self.line_edit_average_count = QLineEdit()
        self.line_edit_average_count.setText("3")
        self.line_edit_average_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout.addRow(self.label_average_count,self.line_edit_average_count)

        self.label_total_pulse=QLabel("total_pulse:")
        self.line_edit_total_pulse = QLineEdit()
        self.line_edit_total_pulse.setText("2000000")
        self.line_edit_total_pulse.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        from_layout.addRow(self.label_total_pulse,self.line_edit_total_pulse)


        self.label_light_source=QLabel("light_source: ")

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
        from_layout.addRow(self.label_light_source,h_layout)

        group_box.setLayout(from_layout)
        grid_layout.addWidget(group_box,1,0)

        group_box1=QGroupBox("移动导轨确定Total_pulse值，测试时默认VID为2米,若已确定该值，直接输入即可")
        from_layout1=QFormLayout()
        
        self.btn_test = QPushButton("移动测试")
        self.btn_test.clicked.connect(self.start_test_daogui)
        from_layout1.addRow(self.btn_test)

        group_box1.setLayout(from_layout1)
        grid_layout.addWidget(group_box1,2,0)

        group_box2=QGroupBox("移动不同VID位置后存图用于圈定ROI")
        from_layout2=QFormLayout()

        self.label_path = QLabel("图像保存路径:")
        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout2.addRow(self.label_path,self.line_edit_path)
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(lambda: self._open_folder_dialog(self.line_edit_path)) # 添加lambda保证按钮在点击时再调用
        from_layout2.addRow(self.btn_browse)

        self.btn_vid_image = QPushButton("不同VID拍图")
        self.btn_vid_image.clicked.connect(self.start_capture_image)
        from_layout2.addRow(self.btn_vid_image)

        group_box2.setLayout(from_layout2)
        grid_layout.addWidget(group_box2,3,0)

        group_box3=QGroupBox("生成ROI配置")
        from_layout3=QFormLayout()

        self.label_roi_set_path = QLabel("选择不同vid所选的roi设置所在路径:")
        self.line_edit_roi_set_path= QLineEdit()
        self.line_edit_roi_set_path.setReadOnly(True)  # 设置为只读
        self.line_edit_roi_set_path.setPlaceholderText("未选择文件夹")
        self.line_edit_roi_set_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout3.addRow(self.label_roi_set_path,self.line_edit_roi_set_path)
        self.btn_roi_set_browse = QPushButton("浏览...")
        self.btn_roi_set_browse.clicked.connect(lambda: self._open_folder_dialog(self.line_edit_roi_set_path))
        from_layout3.addRow(self.btn_roi_set_browse)

        self.label_roi_path = QLabel("ROI保存路径:")
        self.line_edit_roi_path = QLineEdit()
        self.line_edit_roi_path.setReadOnly(True)  # 设置为只读
        self.line_edit_roi_path.setPlaceholderText("未选择文件夹")
        self.line_edit_roi_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout3.addRow(self.label_roi_path,self.line_edit_roi_path)

        self.btn_roi_browse = QPushButton("浏览...")
        self.btn_roi_browse.clicked.connect(lambda: self._open_folder_dialog(self.line_edit_roi_path))
        from_layout3.addRow(self.btn_roi_browse)

        
        self.btn_roi_config = QPushButton("生成ROI配置")
        self.btn_roi_config.clicked.connect(self.start_roi_config)
        from_layout3.addRow(self.btn_roi_config)

        group_box3.setLayout(from_layout3)
        grid_layout.addWidget(group_box3,4,0)

        group_box4=QGroupBox("VID定标")
        from_layout4=QFormLayout()
        self.label_mtf_path = QLabel("MTF结果保存路径:")
        self.line_edit_mtf_path = QLineEdit()
        self.line_edit_mtf_path.setReadOnly(True)  # 设置为只读
        self.line_edit_mtf_path.setPlaceholderText("未选择文件夹")
        self.line_edit_mtf_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout4.addRow(self.label_mtf_path,self.line_edit_mtf_path)
        self.btn_mtf_browse = QPushButton("浏览...")
        self.btn_mtf_browse.clicked.connect(lambda: self._open_folder_dialog(self.line_edit_mtf_path))
        from_layout4.addRow(self.btn_mtf_browse)

        self.btn_vid_start = QPushButton("开始定标")
        self.btn_vid_start.clicked.connect(self.start_vid_test)
        from_layout4.addRow(self.btn_vid_start)

        group_box4.setLayout(from_layout4)
        grid_layout.addWidget(group_box4,5,0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,6,0)


        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        # 将布局添加到 scroll_area_content 并将其设置为 scroll_area 的子部件
        scroll_area.setWidget(scroll_area_content)

        # 最后设置主窗口的布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def start_test_daogui(self):
        try:
            self.status_label.setText("<span style='color: green;'>状态: 正在运行</span>")  # 更新状态
            self.btn_test.setEnabled(False)
            self.is_running=True
            self.test_thtread=TestDaoGuiThread()

            self.test_thtread.finished.connect(self.on_thread_finish)
            self.test_thtread.error.connect(self.on_thread_error)
            self.test_thtread.status_update.connect(self.update_status)

            self.test_thtread.start()

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter",e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_test.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_thread_finish(self):
        QMessageBox.information(self,"MLColorimeter","移动完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 移动完成！</span>")  # 更新状态
        self.btn_test.setEnabled(True)
        self.is_running=False # 标识完成

    def on_thread_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_test.setEnabled(True)
        self.is_running=False # 标识完成

    def closeEvent(self, event):
        if self.is_running:
            # 如果正在进行定标，拦截关闭事件
            event.ignore()
            QMessageBox.warning(self,"警告","程序运行中，请勿关闭窗口",QMessageBox.Ok)
        else:
            event.accept()
        

    def start_capture_image(self):
        try:
            self.binn_select=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.pixel_format=self.get_current_pixel_format()
            self.binning=mlcm.Binning(int(self.line_edit_binnlist.text()))
            self.vid_list=[int(vid) for vid in self.line_edit_vid_list.text().strip().split()]
            self.inf_pos=float(self.line_edit_inf_pos.text())
            self.pos_offset=float(self.line_edit_pos_offset.text())
            self.coef=float(self.line_edit_coef.text())
            self.total_pulse=int(self.line_edit_total_pulse.text())
            self.image_out_path=self.line_edit_path.text()

            self.status_label.setText("<span style='color: green;'>状态: 正在运行</span>")  # 更新状态
            self.btn_vid_image.setEnabled(False)
            self.is_running=True

            parameters={
                'colorimeter':self.colorimeter,
                'binn_selector':self.binn_select,
                'binn_mode':self.binn_mode,
                'binn':self.binning,
                'pixel_format':self.pixel_format,
                'vid_list':self.vid_list,
                'inf_pos':self.inf_pos,
                'pos_offset':self.pos_offset,
                'coef':self.coef,
                'total_pulse':self.total_pulse,
                'out_path':self.image_out_path,
            }
            self.capture_thread=CaptureImageVIDThread(parameters)
            self.capture_thread.finished.connect(self.on_capture_finished)
            self.capture_thread.error.connect(self.on_capture_error)
            self.capture_thread.status_update.connect(self.update_status)
            self.capture_thread.start()

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter",e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_vid_image.setEnabled(True)
            self.is_running=False # 标识完成

    def on_capture_finished(self):
        QMessageBox.information(self,"MLColorimeter","拍图完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 拍图完成！</span>")  # 更新状态
        self.btn_vid_image.setEnabled(True)
        self.is_running=False # 标识完成

    def on_capture_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_vid_image.setEnabled(True)
        self.is_running=False # 标识完成
        
    def start_roi_config(self):
        try:
            self.btn_roi_config.setEnabled(False)
            self.roi_set_path=self.line_edit_roi_set_path.text()
            self.roi_out_path=self.line_edit_roi_path.text()
            start_generate_roi_config(roi_set_path=self.roi_set_path,roi_out_path=self.roi_out_path)
            QMessageBox.information(self,"MLColorimeter","生成结束!",QMessageBox.Ok)
            self.btn_roi_config.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter",e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_roi_config.setEnabled(True)


    def start_vid_test(self):
        try:
            if self.line_edit_roi_path.text() is None:
                QMessageBox.warning(self,"MLColorimeter","请先选择roi配置保存路径(即roividconfig.json所在路径)",QMessageBox.Ok)
                return
            self.roi_out_path=self.line_edit_roi_path.text()
            
            self.binn_select=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.pixel_format=self.get_current_pixel_format()
            self.binning=mlcm.Binning(int(self.line_edit_binnlist.text()))
            self.vid_list=[int(vid) for vid in self.line_edit_vid_list.text().strip().split()]
            self.inf_pos=float(self.line_edit_inf_pos.text())
            self.pos_offset=float(self.line_edit_pos_offset.text())
            self.coef=float(self.line_edit_coef.text())
            self.total_pulse=int(self.line_edit_total_pulse.text())
            self.focal_length=float(self.line_edit_focal_length.text())
            self.pixel_size=float(self.line_edit_pixel_size.text())
            self.chess_mode=self.line_edit_use_chess_mode.isChecked()
            self.lpmm_unit=self.line_edit_use_lpmm_unit.isChecked()
            self.rough_step=float(self.line_edit_rough_step.text())
            self.freq=float(self.line_edit_freq.text())
            self.avg_count=int(self.line_edit_average_count.text())
            self.light_source=self.rgbw_btngroup.checkedButton().text()
            self.out_path=self.line_edit_mtf_path.text()

            self.throughFocus=mlcm.pyThroughFocusConfig(
                inf_position=self.inf_pos,
                focal_length=self.focal_length,
                pixel_size=self.pixel_size,
                freq=self.freq,
                use_chess_mode=self.chess_mode,
                use_lpmm_unit=self.lpmm_unit,
                rough_step=self.rough_step,
                average_count=self.avg_count
            )

            start_calibration_vid(
                colorimeter=self.colorimeter,
                binn_selector=self.binn_select,
                binn_mode=self.binn_mode,
                binn=self.binning,
                pixel_format=self.pixel_format,
                vid_list=self.vid_list,
                inf_pos=self.inf_pos,
                pos_offset=self.pos_offset,
                coef=self.coef,
                total_pulse=self.total_pulse,
                roi_out_path=self.roi_out_path,
                out_path=self.out_path,
                light_source=self.light_source,
                through_focus=self.throughFocus
            )

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter",e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def _open_folder_dialog(self,lineedit:QLineEdit):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.save_path = folder_path
            lineedit.setText(folder_path)
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
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
from scripts.FFC_one_by_one import FFC_calculate_1,FFC_calculate_2,FFC_calculate_4
from ui.grayrange_dialog import GrayRangeDialog

class FFCCalculateBinningThread_1(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            FFC_calculate_1(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class FFCCalculateBinningThread_2(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            FFC_calculate_2(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class FFCCalculateBinningThread_4(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            FFC_calculate_4(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class FFCCalculateBinningWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ffc calculate binning")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.colorimeter = AppConfig.get_colorimeter()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.roi_list=[]
        self.vrange={}
        self.binning_selector=['Logic','Sensor']
        self.binning=['ONE_BY_ONE','TWO_BY_TWO','FOUR_BY_FOUR']
        self.binning_mode=['AVERAGE','SUM']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self._init_ui()

        # 标识当前流程是否正在进行
        self.is_running=False

    def _init_ui(self):
        grid_layout = QGridLayout()

        self.label_file_path = QLabel("FFC图像保存路径")
        grid_layout.addWidget(self.label_file_path, 0, 0)
        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 1, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 1, 1)

        self.label_xyz_list=QLabel("xyz滤光片，输入如X Y Z Clear，以空格分隔")
        grid_layout.addWidget(self.label_xyz_list, 2, 0)
        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setText("X Y Z")
        self.line_edit_xyzlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 3, 0)

        self.label_binn = QLabel(" binning：")
        grid_layout.addWidget(self.label_binn, 4, 0)
        self.line_edit_binn = QComboBox()
        self.line_edit_binn.addItems(self.binning)
        self.line_edit_binn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_binn, 5, 0)

        self.label_half_size=QLabel("half_size：(根据FOV修改)")
        grid_layout.addWidget(self.label_half_size,6,0)
        self.line_edit_half_size=QLineEdit()
        self.line_edit_half_size.setText("3600")
        self.line_edit_half_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_half_size, 7, 0)

        self.label_min_loop=QLabel("循环最小值：")
        grid_layout.addWidget(self.label_min_loop,8,0)
        self.line_edit_min_loop=QLineEdit()
        self.line_edit_min_loop.setText("5")
        self.line_edit_min_loop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_min_loop, 9, 0)

        self.label_max_loop=QLabel("循环最大值：")
        grid_layout.addWidget(self.label_max_loop,10,0)
        self.line_edit_max_loop=QLineEdit()
        self.line_edit_max_loop.setText("11")
        self.line_edit_max_loop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_max_loop, 11, 0)

        self.label_step_loop=QLabel("步长：")
        grid_layout.addWidget(self.label_step_loop,12,0)
        self.line_edit_step_loop=QLineEdit()
        self.line_edit_step_loop.setText("2")
        self.line_edit_step_loop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_step_loop, 13, 0)

        self.loop_display=QListWidget()
        self.loop_display.setFixedHeight(100)
        self.loop_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.loop_display,14,0)
        self.btn_submit = QPushButton("提交")
        self.btn_submit.clicked.connect(self.submit)
        grid_layout.addWidget(self.btn_submit, 14, 1)

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


        self.add_button = QPushButton("Add ROI")
        self.add_button.clicked.connect(self.add_roi)
        self.delete_button=QPushButton("Delete ROI")
        self.delete_button.clicked.connect(self.delete_roi)
        from_layout1.addRow(self.add_button,self.delete_button)

        self.roi_display=QListWidget()
        self.roi_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout1.addRow(self.roi_display)

        group_box1.setLayout(from_layout1)
        grid_layout.addWidget(group_box1, 15, 0)

        self.btn_capture = QPushButton("开始计算")
        self.btn_capture.clicked.connect(self.start_ffc_calculate)
        grid_layout.addWidget(self.btn_capture, 16, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,17,0)


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
    def add_roi(self):

        try:
            x=int(self.line_edit_x_input.text().strip())
            y=int(self.line_edit_y_input.text().strip())
            width=int(self.line_edit_width_input.text().strip())
            height=int(self.line_edit_height_input.text().strip())

            # 创建roi并添加到列表
            roi=mlcm.pyCVRect(x,y,width,height)
            self.roi_list.append(roi)
            # 显示在控件上
            roi_str=f"{x},{y},{width},{height}"
            self.roi_display.addItem(roi_str)
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def delete_roi(self):
        try:

            current_item=self.roi_display.currentItem()
            if current_item is None:
                QMessageBox.warning(self,"警告","请先选择要删除的ROI",QMessageBox.Ok)
                return
            
            roi_str=current_item.text()
            # 解析ROi
            roi_coords=list(map(int,roi_str.split(',')))
            roi_list=[int(roi) for roi in roi_coords]
            roi_x=roi_list[0]
            roi_y=roi_list[1]
            roi_w=roi_list[2]
            roi_h=roi_list[3]
            roi_remove=mlcm.pyCVRect(roi_x,roi_y,roi_w,roi_h)
            for index,roi in enumerate(self.roi_list):
                if (roi.x == roi_remove.x and roi.y==roi_remove.y and roi.width==roi_remove.width and roi.height==roi_remove.height):
                    # 只删除第一个匹配的roi
                    del self.roi_list[index]
                    break # 找到并删除后退出循环
            
            row=self.roi_display.row(current_item)
            self.roi_display.takeItem(row)
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def start_ffc_calculate(self):
        try:
            self.status_label.setText("<span style='color: green;'>状态: 正在计算...</span>")  # 更新状态
            self.btn_capture.setEnabled(False)
            self.is_running=True
            self.file_path=self.line_edit_path.text()
            self.xyz_list=self.line_edit_xyzlist.text().strip().split()
            self.half_size=int(self.line_edit_half_size.text())
            # FFC_calculate_1(
            #     xyz_list=self.xyz_list,
            #     filepath=self.file_path,
            #     vrange=self.vrange,
            #     half_size=self.half_size,
            #     roi_list=self.roi_list
            # )
            parameters={
                    'xyz_list':self.xyz_list,
                    'filepath':self.file_path,
                    'vrange':self.vrange,
                    'half_size':self.half_size,
                    'roi_list':self.roi_list
                }
            self.selected_binning=self.line_edit_binn.currentText()
            if self.selected_binning=="ONE_BY_ONE":
                self.ffc_calculate_1_thread=FFCCalculateBinningThread_1(parameters)
                self.ffc_calculate_1_thread.finished.connect(self.on_ffccalculate_finish)
                self.ffc_calculate_1_thread.error.connect(self.on_ffccalculate_error)
                self.ffc_calculate_1_thread.status_update.connect(self.update_status)
                self.ffc_calculate_1_thread.start()
            elif self.selected_binning=="TWO_BY_TWO":
                self.ffc_calculate_2_thread=FFCCalculateBinningThread_2(parameters)
                self.ffc_calculate_2_thread.finished.connect(self.on_ffccalculate_finish)
                self.ffc_calculate_2_thread.error.connect(self.on_ffccalculate_error)
                self.ffc_calculate_2_thread.status_update.connect(self.update_status)
                self.ffc_calculate_2_thread.start()
            elif self.selected_binning=="FOUR_BY_FOUR":
                self.ffc_calculate_4_thread=FFCCalculateBinningThread_4(parameters)
                self.ffc_calculate_4_thread.finished.connect(self.on_ffccalculate_finish)
                self.ffc_calculate_4_thread.error.connect(self.on_ffccalculate_error)
                self.ffc_calculate_4_thread.status_update.connect(self.update_status)
                self.ffc_calculate_4_thread.start()
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_ffccalculate_finish(self):
        QMessageBox.information(self,"MLColorimeter","计算完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 计算完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_ffccalculate_error(self,error_message):
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
    
        
    def submit(self):
        try:
            self.loop_display.clear()
            min_loop=int(self.line_edit_min_loop.text())
            max_loop=int(self.line_edit_max_loop.text())
            step=int(self.line_edit_step_loop.text())

            # 清空之前的灰度范围
            self.vrange.clear()

            for loop_i in range(min_loop,max_loop,step):
                dialog=GrayRangeDialog(loop_i,self)
                if dialog.exec_() == QDialog.Accepted:
                    min_gray, max_gray = dialog.get_values()
                    self.vrange[loop_i] = (min_gray, max_gray)
                    loop_str=f"{loop_i}-{min_gray}-{max_gray}"
                    self.loop_display.addItem(loop_str)
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
    
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QPushButton,
    QFileDialog,
    QSizePolicy,
    QMessageBox,
    QGroupBox,
    QGridLayout,
    QSpacerItem,
    QDialog,
    QFormLayout,
    QCheckBox,
    QListWidget,
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
from scripts.field_curve import field_curve
import json

class FiledCurveThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            field_curve(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class FiledCurveWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("capture field curve")
        self.setGeometry(200, 200, 800, 500)
        self.colorimeter = AppConfig.get_colorimeter()
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.file_name = "field_curve.xlsx"
        self.roi_list=[]
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

        self.label_binnlist = QLabel(" binning：")
        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_binnlist.setPlaceholderText("0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16")
        from_layout0.addRow(self.label_binnlist, self.line_edit_binnlist)

        self.label_exposure_mode = QLabel(" exposure_mode：")
        self.line_edit_exposure_mode = QComboBox()
        self.line_edit_exposure_mode.addItems(self.exposure_mode)
        self.line_edit_exposure_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_exposure_time = QLabel(" exposure_time(ms)：")
        self.line_edit_exposure_time = QLineEdit()
        self.line_edit_exposure_time.setText("100")
        self.line_edit_exposure_time.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_pixel_format = QLabel(" pixel_format：")
        self.line_edit_pixel_format = QComboBox()
        self.line_edit_pixel_format.addItems(self.pixel_format)
        self.line_edit_pixel_format.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_pixel_format.setCurrentText("MLMono12")


        horizontal_layout1=QHBoxLayout()
        horizontal_layout1.addWidget(self.label_exposure_mode)
        horizontal_layout1.addWidget(self.line_edit_exposure_mode)
        horizontal_layout1.addWidget(self.label_exposure_time)
        horizontal_layout1.addWidget(self.line_edit_exposure_time)
        horizontal_layout1.addWidget(self.label_pixel_format)
        horizontal_layout1.addWidget(self.line_edit_pixel_format)
        from_layout0.addRow(horizontal_layout1)

        group_box0.setLayout(from_layout0)
        grid_layout.addWidget(group_box0, 0, 0)



        group_box=QGroupBox("过焦参数")
        from_layout=QFormLayout()

        self.label_focus_max=QLabel("focus_max: ")
        self.line_edit_focus_max = QLineEdit()
        self.line_edit_focus_max.setText("10")
        self.line_edit_focus_max.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_focus_min=QLabel("focus_min: ")
        self.line_edit_focus_min = QLineEdit()
        self.line_edit_focus_min.setText("-10")
        self.line_edit_focus_min.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_inf_pos=QLabel("inf_pos: ")
        self.line_edit_inf_pos = QLineEdit()
        self.line_edit_inf_pos.setText("0")
        self.line_edit_inf_pos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_focal_length=QLabel("focal_length: ")
        self.line_edit_focal_length = QLineEdit()
        self.line_edit_focal_length.setText("4.25")
        self.line_edit_focal_length.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        horizontal_layout2=QHBoxLayout()
        horizontal_layout2.addWidget(self.label_focus_max)
        horizontal_layout2.addWidget(self.line_edit_focus_max)
        horizontal_layout2.addWidget(self.label_focus_min)
        horizontal_layout2.addWidget(self.line_edit_focus_min)
        horizontal_layout2.addWidget(self.label_inf_pos)
        horizontal_layout2.addWidget(self.line_edit_inf_pos)
        horizontal_layout2.addWidget(self.label_focal_length)
        horizontal_layout2.addWidget(self.line_edit_focal_length)
        from_layout.addRow(horizontal_layout2)

        self.label_pixel_size=QLabel("pixel_size: ")
        self.line_edit_pixel_size = QLineEdit()
        self.line_edit_pixel_size.setText("0.0014")
        self.line_edit_pixel_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_focal_space=QLabel("focal_space: ")
        self.line_edit_focal_space = QLineEdit()
        self.line_edit_focal_space.setText("0.5")
        self.line_edit_focal_space.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_use_chess_mode=QLabel("use_chess_mode: ")
        self.line_edit_use_chess_mode = QCheckBox()
        self.line_edit_use_chess_mode.setChecked(True)
        self.line_edit_use_chess_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_use_lpmm_unit=QLabel("use_lpmm_unit: ")
        self.line_edit_use_lpmm_unit = QCheckBox()
        self.line_edit_use_lpmm_unit.setChecked(True)
        self.line_edit_use_lpmm_unit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        horizontal_layout3=QHBoxLayout()
        horizontal_layout3.addWidget(self.label_pixel_size)
        horizontal_layout3.addWidget(self.line_edit_pixel_size)
        horizontal_layout3.addWidget(self.label_focal_space)
        horizontal_layout3.addWidget(self.line_edit_focal_space)
        horizontal_layout3.addWidget(self.label_use_chess_mode)
        horizontal_layout3.addWidget(self.line_edit_use_chess_mode)
        horizontal_layout3.addWidget(self.label_use_lpmm_unit)
        horizontal_layout3.addWidget(self.line_edit_use_lpmm_unit)
        from_layout.addRow(horizontal_layout3)

        self.label_rough_step=QLabel("rough_step: ")
        self.line_edit_rough_step = QLineEdit()
        self.line_edit_rough_step.setText("0.1")
        self.line_edit_rough_step.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_use_fine_adjust=QLabel("use_fine_adjust: ")
        self.line_edit_use_fine_adjust = QCheckBox()
        self.line_edit_use_fine_adjust.setChecked(False)
        self.line_edit_use_fine_adjust.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.label_average_count=QLabel("average_count: ")
        self.line_edit_average_count = QLineEdit()
        self.line_edit_average_count.setText("3")
        self.line_edit_average_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        horizontal_layout4=QHBoxLayout()
        horizontal_layout4.addWidget(self.label_rough_step)
        horizontal_layout4.addWidget(self.line_edit_rough_step)
        horizontal_layout4.addWidget(self.label_use_fine_adjust)
        horizontal_layout4.addWidget(self.line_edit_use_fine_adjust)
        horizontal_layout4.addWidget(self.label_average_count)
        horizontal_layout4.addWidget(self.line_edit_average_count)
        from_layout.addRow(horizontal_layout4)

        group_box.setLayout(from_layout)
        grid_layout.addWidget(group_box, 1, 0)

        self.label_freq_list = QLabel()
        self.label_freq_list.setText("频率列表, 例如: 6.75 13.5, 以空格隔开")
        grid_layout.addWidget(self.label_freq_list, 2, 0)
        self.line_edit_freq_list = QLineEdit()
        self.line_edit_freq_list.setText("6.75 13.5")
        self.line_edit_freq_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_freq_list, 3, 0)

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

        self.label_roi_count=QLabel("roi_count: ")
        self.line_edit_roi_count = QLineEdit()
        self.line_edit_roi_count.setReadOnly(True)
        self.line_edit_roi_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout1.addRow(self.label_roi_count,self.line_edit_roi_count)


        self.add_button = QPushButton("Add ROI")
        self.add_button.clicked.connect(self.add_roi)
        self.delete_button=QPushButton("Delete ROI")
        self.delete_button.clicked.connect(self.delete_roi)
        from_layout1.addRow(self.add_button,self.delete_button)

        self.load_config_button=QPushButton("Load Config")
        self.load_config_button.clicked.connect(self.load_config)
        self.save_config_button=QPushButton("Save Config")
        self.save_config_button.clicked.connect(self.save_config)
        from_layout1.addRow(self.load_config_button,self.save_config_button)

        self.roi_display=QListWidget()
        self.roi_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        from_layout1.addRow(self.roi_display)

        group_box1.setLayout(from_layout1)
        grid_layout.addWidget(group_box1, 4, 0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径:")
        grid_layout.addWidget(self.label_path, 5, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 6, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 6, 1)

        self.btn_capture = QPushButton("开始拍图")
        self.btn_capture.clicked.connect(self.start_capture)
        grid_layout.addWidget(self.btn_capture, 7, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,8,0)


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
            self.line_edit_roi_count.setText(str(len(self.roi_list)))
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
            self.line_edit_roi_count.setText(str(len(self.roi_list)))
            
            row=self.roi_display.row(current_item)
            self.roi_display.takeItem(row)
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def load_config(self):
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(self, "Load ROI Config", "", "JSON Files (*.json);;All Files (*)", options=options)
            if file_name:
                # 读取json文件
                with open(file_name,'r') as f:
                    serialized_data=json.load(f)
                # 清空现有的roi_list
                self.roi_list.clear()
                self.roi_display.clear()

                # 将每个字典转换为pyCVRect对象并添加到roi_list
                for item in serialized_data:
                    rect=mlcm.pyCVRect(item['x'],item['y'],item['width'],item['height'])
                    self.roi_list.append(rect)
                    roi_str=f"{rect.x},{rect.y},{rect.width},{rect.height}"
                    self.roi_display.addItem(roi_str)
                self.line_edit_roi_count.setText(str(len(self.roi_list)))
                

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def save_config(self):
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save ROI Config", "", "JSON Files (*.json);;All Files (*)", options=options)
            if file_name:
                # 序列化
                serialized_dict=[]
                for value in self.roi_list:
                    serialized_dict.append(self.serialize_pyCVRect(value))
                with open(file_name,'w') as f:
                    json.dump(serialized_dict,f,ensure_ascii=False,indent=4)
                QMessageBox.information(self,"成功","保存成功！",QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
    def serialize_pyCVRect(self,rect:mlcm.pyCVRect):
        return{
            'x':rect.x,
            'y':rect.y,
            'width':rect.width,
            'height':rect.height
        }
    def start_capture(self):
        try:
            self.pixel_format=self.get_current_pixel_format()
            self.binn_selector=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.binn=mlcm.Binning(int(self.line_edit_binnlist.text().strip()))
            self.exposure_mode=self.get_current_exposure_mode()
            self.exposure_time=float(self.line_edit_exposure_time.text().strip())
            self.focus_max=float(self.line_edit_focus_max.text().strip())
            self.focus_min=float(self.line_edit_focus_min.text().strip())
            self.inf_pos=float(self.line_edit_inf_pos.text().strip())
            self.focal_length=float(self.line_edit_focal_length.text().strip())
            self.pixel_size=float(self.line_edit_pixel_size.text().strip())
            self.focal_space=float(self.line_edit_focal_space.text().strip())
            self.use_chess_mode=self.line_edit_use_chess_mode.isChecked()
            self.use_lpmm_unit=self.line_edit_use_lpmm_unit.isChecked()
            self.rough_step=float(self.line_edit_rough_step.text().strip())
            self.use_fine_adjust=self.line_edit_use_fine_adjust.isChecked()
            self.average_count=int(self.line_edit_average_count.text().strip())
            self.freq_list=[float(freq) for freq in self.line_edit_freq_list.text().strip().split()]
            if not self.freq_list:
                QMessageBox.critical(self,"MLColorimeter","请填写频率列表",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
                return
            if not self.roi_list:
                QMessageBox.critical(self,"MLColorimeter","请添加roi",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
                return
            self.out_path=self.line_edit_path.text().strip()
            if not self.out_path:
                QMessageBox.critical(self,"MLColorimeter","请选择保存路径",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
                return
            
            self.focus_config = mlcm.pyThroughFocusConfig(
                focus_max=self.focus_max,
                focus_min=self.focus_min,
                inf_position=self.inf_pos,
                focal_length=self.focal_length,
                pixel_size=self.pixel_size,
                focal_space=self.focal_space,
                rois=self.roi_list,
                use_chess_mode=self.use_chess_mode,
                use_lpmm_unit=self.use_lpmm_unit,
                rough_step=self.rough_step,
                use_fine_adjust=self.use_fine_adjust,
                average_count=self.average_count,
            )
            
            self.status_label.setText("<span style='color: green;'>状态: 正在进行拍图...</span>")  # 更新状态
            self.btn_capture.setEnabled(False)
            self.is_running=True

            parameters={
                'colorimeter': self.colorimeter,
                'exposure_mode':self.exposure_mode,
                'binn_selector': self.binn_selector,
                'binn_mode': self.binn_mode,
                'binn': self.binn,
                'pixel_format': self.pixel_format,
                'exposure_time':self.exposure_time,
                'out_path':self.out_path,
                'focus_config':self.focus_config,
                'freq_list':self.freq_list
            }

            self.filed_curve_thread=FiledCurveThread(parameters)
            self.filed_curve_thread.finished.connect(self.on_filed_curve_finished)
            self.filed_curve_thread.error.connect(self.on_filed_curve_error)
            self.filed_curve_thread.status_update.connect(self.update_status)
            self.filed_curve_thread.start()

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_filed_curve_finished(self):
        QMessageBox.information(self,"MLColorimeter","拍图完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 拍图完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_filed_curve_error(self,error_message):
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
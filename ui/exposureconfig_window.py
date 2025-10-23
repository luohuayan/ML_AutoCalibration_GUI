from PyQt5.QtWidgets import (
    QWidget,
    QScrollArea,
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
    QComboBox,
    QFormLayout,
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
from typing import List
import json

class ExposureConfigWindow(QDialog):
    # 定义信号，传递字典类型的数据
    config_saved = pyqtSignal(dict)
    def __init__(self, nd_list:List[str],xyz_list:List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exposure Configuration")
        self.setGeometry(250, 250, 400, 300)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.colorimeter = AppConfig.get_colorimeter()
        self.nd_list = nd_list
        self.xyz_list = xyz_list
        self.exposure_modes=['Auto','Fixed']
        self.settings={}  # (nd,xyz):(mode_combobox,time_entry)
        self.exposure_map={}
        self._init_ui()

    def _init_ui(self):
        scroll_area=QScrollArea()
        scroll_area.setWidgetResizable(True) # 内容自适应大小

        # 创建一个容器小部件，用于防止所有其它部件
        container_widget=QWidget()
        layout = QVBoxLayout(container_widget)
        for nd in self.nd_list:
            nd_enum = mlcm.MLFilterEnum(int(nd))
            nd_str=mlcm.MLFilterEnum_to_str(nd_enum)
            group_box=QGroupBox(f"{nd_str} 设置")
            from_layout=QFormLayout()
            for xyz in self.xyz_list:
                xyz_enum = mlcm.MLFilterEnum(int(xyz))
                xyz_str=mlcm.MLFilterEnum_to_str(xyz_enum)
                mode_combobox=QComboBox()
                mode_combobox.addItems(self.exposure_modes)
                time_entry=QLineEdit()
                time_entry.setPlaceholderText("曝光时间 (ms)")
                time_entry.setText("100")
                from_layout.addRow(QLabel(f"{xyz_str} 曝光模式:"),mode_combobox)
                from_layout.addRow(QLabel(f"{xyz_str} 曝光时间:"),time_entry)
                self.settings[(nd_str,xyz_str)]=(mode_combobox,time_entry)
            group_box.setLayout(from_layout)
            layout.addWidget(group_box)
        
        load_button = QPushButton("Load Config")
        load_button.clicked.connect(self.load_config)
        layout.addWidget(load_button)

        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        container_widget.setLayout(layout)
        scroll_area.setWidget(container_widget)

        main_layout=QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def load_config(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Exposure Config", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    exposure_map=json.load(f)
                    for nd in self.nd_list:
                        nd_enum = mlcm.MLFilterEnum(int(nd))
                        nd_str=mlcm.MLFilterEnum_to_str(nd_enum)
                        for xyz in self.xyz_list:
                            xyz_enum = mlcm.MLFilterEnum(int(xyz))
                            xyz_str=mlcm.MLFilterEnum_to_str(xyz_enum)
                            if nd_str in exposure_map and xyz_str in exposure_map[nd_str]:
                                setting=exposure_map[nd_str][xyz_str]
                                mode_combobox,time_entry=self.settings[(nd_str,xyz_str)]
                                mode_combobox.setCurrentText(setting['exposure_mode'])
                                time_entry.setText(str(setting['exposure_time']))
                            else:
                                mode_combobox.setCurrentIndex(0)
                                time_entry.setText("100")
            except Exception as e:
                QMessageBox.critical(self,"MLColorimeter","Load config error: " + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def save_config(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Exposure Config", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                for nd in self.nd_list:
                    nd_enum = mlcm.MLFilterEnum(int(nd))
                    nd_str=mlcm.MLFilterEnum_to_str(nd_enum)
                    self.exposure_map[nd_str]={}
                    for xyz in self.xyz_list:
                        xyz_enum = mlcm.MLFilterEnum(int(xyz))
                        xyz_str=mlcm.MLFilterEnum_to_str(xyz_enum)
                        mode_combobox,time_entry=self.settings[(nd_str,xyz_str)]
                        mode=mode_combobox.currentText()
                        time=float(time_entry.text())
                        self.exposure_map[nd_str][xyz_str]={
                            'exposure_mode':mode,
                            'exposure_time':time
                        }
                with open(file_name, 'w') as f:
                    json.dump(self.exposure_map, f, ensure_ascii=False, indent=4)
                
                # 发射信号传递配置
                self.config_saved.emit(self.exposure_map)
                QMessageBox.information(self,"MLColorimeter","Config saved successfully", QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            except Exception as e:
                QMessageBox.critical(self,"MLColorimeter","Save config error: " + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
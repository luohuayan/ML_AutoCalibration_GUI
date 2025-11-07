from PyQt5.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QFormLayout, QLabel, QLineEdit, QPushButton, QGroupBox,QMessageBox,QHBoxLayout,QSizePolicy,QListWidget
from PyQt5.QtCore import pyqtSignal
from typing import List
import mlcolorimeter as mlcm
from PyQt5.QtCore import pyqtSignal, Qt
from functools import partial

class ROIConfigWindow(QDialog):
    roi_config_saved = pyqtSignal(dict)

    def __init__(self, binn_list: List[mlcm.Binning], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exposure Configuration")
        self.setGeometry(250, 250, 400, 300)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.binn_list = binn_list
        self.roi_dict={} # 用于存储每个Binning的ROI列表
        self.binn_input_fields = {}  # 用于存储输入框
        self.roi_displays={} # 用于存储每个Binning对应的QListWidget
        self.roi_counts={} # 用于存储每个Binning对应的ROI数量
        self._init_ui()

    def _init_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        container_widget = QWidget()
        layout = QVBoxLayout(container_widget)

        for binn in self.binn_list:
            binn_str=mlcm.Binning_to_str(binn)
            group_box = QGroupBox(f"{binn_str} 设置")
            form_layout = QFormLayout()

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
            # 保存输入框的引用
            self.binn_input_fields[binn] = (self.line_edit_x_input, self.line_edit_y_input, self.line_edit_width_input,self.line_edit_height_input)

            self.add_button = QPushButton("Add ROI")
            # self.add_button.clicked.connect( lambda b=binn: self.add_roi(b)) # 使用闭包传递binn,不生效
            self.add_button.clicked.connect(partial(self.add_roi,binn)) # 通过partial确保每个按钮点击时都能传递当前的binn值

            self.delete_button=QPushButton("Delete ROI")
            self.delete_button.clicked.connect(partial(self.delete_roi,binn))

            from_layout1.addRow(self.add_button,self.delete_button)
            
            self.label_roi_count=QLabel("roi_count: ")
            self.line_edit_roi_count = QLineEdit()
            self.line_edit_roi_count.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.line_edit_roi_count.setReadOnly(True)
            from_layout1.addRow(self.label_roi_count,self.line_edit_roi_count)

            self.roi_display=QListWidget()
            self.roi_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            from_layout1.addRow(self.roi_display)

            group_box1.setLayout(from_layout1)
            form_layout.addWidget(group_box1)

            group_box.setLayout(form_layout)
            layout.addWidget(group_box)
            self.roi_displays[binn]=self.roi_display
            self.roi_counts[binn]=self.line_edit_roi_count
        
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        container_widget.setLayout(layout)
        scroll_area.setWidget(container_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def add_roi(self,binn):

        try:
            input_x,input_y,input_width,input_height=self.binn_input_fields[binn]
            x=int(input_x.text().strip())
            y=int(input_y.text().strip())
            width=int(input_width.text().strip())
            height=int(input_height.text().strip())
            # 创建roi并添加到列表
            roi=mlcm.pyCVRect(x,y,width,height)
            self.roi_dict.setdefault(binn,[]).append(roi)
            # 显示在控件上
            roi_str=f"{x},{y},{width},{height}"
            self.roi_displays[binn].addItem(roi_str)
            self.roi_counts[binn].setText(str(len(self.roi_dict[binn])))
                
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
    
    def save_config(self):
        # 发出信号携带生成的字典
        self.roi_config_saved.emit(self.roi_dict)
        reply = QMessageBox.information(self,"成功","保存成功！",QMessageBox.Ok)

        if reply==QMessageBox.Ok:
            self.close()

    def delete_roi(self,binn):
        try:
            current_item=self.roi_displays[binn].currentItem()
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
            if binn in self.roi_dict:
                # 找到并删除当前选定的roi
                for index,roi in enumerate(self.roi_dict[binn]):
                    if (roi.x == roi_remove.x and roi.y==roi_remove.y and roi.width==roi_remove.width and roi.height==roi_remove.height):
                        # 只删除第一个匹配的roi
                        del self.roi_dict[binn][index]
                        break # 找到并删除后退出循环
            
            row=self.roi_displays[binn].row(current_item)
            self.roi_displays[binn].takeItem(row)
            self.roi_counts[binn].setText(str(len(self.roi_dict[binn])))
                
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
    


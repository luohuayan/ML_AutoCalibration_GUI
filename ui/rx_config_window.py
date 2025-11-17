from PyQt5.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QFormLayout, QLabel, QLineEdit, QPushButton, QGroupBox,QMessageBox,QFileDialog
from PyQt5.QtCore import pyqtSignal
from typing import List
import mlcolorimeter as mlcm
from PyQt5.QtCore import pyqtSignal, Qt
import json

class RXConfigWindow(QDialog):
    config_saved = pyqtSignal(dict)

    def __init__(self, nd_list: List[mlcm.MLFilterEnum], parent=None):
        super().__init__(parent)
        self.setWindowTitle("RX config")
        self.setGeometry(250, 250, 400, 300)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.nd_list = nd_list
        self.nd_input_fields = {}  # 用于存储输入框
        self.is_config_saved=False
        self._init_ui()

    def _init_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        container_widget = QWidget()
        layout = QVBoxLayout(container_widget)

        for nd in self.nd_list:
            nd_str=mlcm.MLFilterEnum_to_str(nd)

            group_box = QGroupBox(f"{nd_str} 设置")
            form_layout = QFormLayout()

            # 创建输入框以输入三个参数的值
            inputs_1 = QLineEdit()
            inputs_1.setPlaceholderText("(例如: -6 -5 -4 -3 -2 -1 0 1 2 3 4 5 6), 以空格隔开")
            inputs_2 = QLineEdit()
            inputs_2.setPlaceholderText("(例如: -4 -3.5 -3 -2.5 -2 -1.5 -1 -0.5 0), 以空格隔开")
            inputs_3 = QLineEdit()
            inputs_3.setPlaceholderText("(例如: 0 15 30 45 60 75 90 105 120 135 150 165), 以空格隔开")

            form_layout.addRow(QLabel("sph列表:"), inputs_1)
            form_layout.addRow(QLabel("cyl列表:"), inputs_2)
            form_layout.addRow(QLabel("axis列表:"), inputs_3)

            group_box.setLayout(form_layout)
            layout.addWidget(group_box)

            # 保存输入框的引用
            self.nd_input_fields[nd_str] = (inputs_1, inputs_2, inputs_3)

        load_button = QPushButton("Load Config")
        load_button.clicked.connect(self.load_config)
        layout.addWidget(load_button)

        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        container_widget.setLayout(layout)
        scroll_area.setWidget(container_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def load_config(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load roi Config", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name,'r') as f:
                    rx_map=json.load(f)
                
                # 遍历字典并填充输入框
                for nd_str, (input_1, input_2, input_3) in self.nd_input_fields.items():
                    if nd_str in rx_map:
                        list_1,list_2,list_3=rx_map[nd_str]
                        input_1.setText(' '.join(map(str,list_1)))
                        input_2.setText(' '.join(map(str,list_2)))
                        input_3.setText(' '.join(map(str,list_3)))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载配置时出错: {str(e)}", QMessageBox.Ok)

    def save_config(self):
        rx_dict = {}
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save ROI Config", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            for nd_str, (input_1, input_2, input_3) in self.nd_input_fields.items():
                try:
                    # 解析输入的字符串为列表
                    list_1 = [float(x) for x in input_1.text().split()]
                    list_2 = [float(x) for x in input_2.text().split()]
                    list_3 = [int(x) for x in input_3.text().split()]
                    
                    # 将解析后的列表添加到字典中
                    rx_dict[nd_str] = [list_1, list_2, list_3]
                except ValueError:
                    print(f"输入格式错误: {nd_str}")  # 处理输入错误
            with open(file_name,'w') as f:
                json.dump(rx_dict,f,ensure_ascii=False,indent=4)

            # 发出信号携带生成的字典
            self.config_saved.emit(rx_dict)
            self.is_config_saved=True
            reply = QMessageBox.information(self,"成功","保存成功！",QMessageBox.Ok)

            if reply==QMessageBox.Ok:
                self.close()
    
    
    def closeEvent(self, event):
        if not self.is_config_saved:
            # 如果配置未保存，弹出提示并阻止关闭窗口
            reply=QMessageBox.question(self,"MLColorimeter","配置未保存，确定要关闭窗口吗？",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
            if reply==QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QMessageBox,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QDialog,
    QSizePolicy,
    QFileDialog,
    QSpacerItem,
    QLineEdit,
    QLabel,
    QGridLayout,
    QCheckBox
)
from PyQt5.QtCore import pyqtSignal, Qt,QThread
from scripts.image_detection import check_image_corruption
import os
from PIL import Image
import mlcolorimeter as mlcm
from scripts.resize_crop_images import resize_crop_images
import ast

class ResizeFFCImagesThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self,parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            resize_crop_images(status_callback=self.status_update.emit,**self.parameters)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

class ResizeFFCImagesWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("resize FFC images")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self._init_ui()

        self.is_running=False
    
    def _init_ui(self):
        grid_layout = QGridLayout()
        self.label_eye1_path = QLabel("EYE1_path:")
        grid_layout.addWidget(self.label_eye1_path, 0, 0)

        self.line_edit_eye1_path = QLineEdit()
        self.line_edit_eye1_path.setReadOnly(True)  # 设置为只读
        self.line_edit_eye1_path.setPlaceholderText("未选择文件夹")
        self.line_edit_eye1_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_eye1_path, 1, 0)

        self.btn_eye1_browse = QPushButton("浏览...")
        self.btn_eye1_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_eye1_browse, 1, 1)

        self.label_ffc_path = QLabel("FFC路径:")
        grid_layout.addWidget(self.label_ffc_path, 2, 0)

        self.line_edit_ffc_path = QLineEdit()
        self.line_edit_ffc_path.setReadOnly(True)  # 设置为只读
        self.line_edit_ffc_path.setPlaceholderText("未选择文件夹")
        self.line_edit_ffc_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ffc_path, 3, 0)

        self.btn_ffc_browse = QPushButton("浏览...")
        self.btn_ffc_browse.clicked.connect(self._open_ffc_dialog)
        grid_layout.addWidget(self.btn_ffc_browse, 3, 1)

        self.label_aperture_list = QLabel("光阑列表, 输入如(3mm 4mm 5mm), 以空格隔开")
        grid_layout.addWidget(self.label_aperture_list, 4, 0)

        self.line_edit_aperture_list = QLineEdit()
        self.line_edit_aperture_list.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_aperture_list, 5, 0)

        self.label_binnlist = QLabel("binning列表(用于重命名), 输入如(_2binn _4binn), 以空格隔开")
        grid_layout.addWidget(self.label_binnlist, 6, 0)

        self.line_edit_binnlist = QLineEdit()
        self.line_edit_binnlist.setText("_2binn")
        self.line_edit_binnlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_binnlist, 7, 0)

        self.label_target_size_list = QLabel("目标图像像素列表, 输入如((5984,6000) (3000,3000)), 以空格隔开")
        grid_layout.addWidget(self.label_target_size_list, 8, 0)

        self.line_edit_target_size_list = QLineEdit()
        self.line_edit_target_size_list.setText("(5984,6000)")
        self.line_edit_target_size_list.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_target_size_list, 9, 0)

        self.cb_generate_ffc = QCheckBox()
        self.cb_generate_ffc.setText("生成FFC图像")
        self.cb_generate_ffc.setChecked(True)
        grid_layout.addWidget(self.cb_generate_ffc,10,0)

        self.cb_calculate_synthetic = QCheckBox()
        self.cb_calculate_synthetic.setText("生成FFC均图(有RX时勾选)")
        self.cb_calculate_synthetic.setChecked(False)
        grid_layout.addWidget(self.cb_calculate_synthetic,11,0)
        self.cb_calculate_synthetic.stateChanged.connect(self._calculate_synthetic)

        self.label_ndlist = QLabel("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开")
        grid_layout.addWidget(self.label_ndlist, 12, 0)

        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 13, 0)

        self.label_xyzlist = QLabel("xyz列表, (1: X, 2: Y, 3: Z, 10: Clear, 12: YA), 以空格隔开")
        grid_layout.addWidget(self.label_xyzlist, 14, 0)

        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 15, 0)

        self.label_lightsource_list = QLabel("光源列表, 输入如(R G B W), 以空格隔开")
        grid_layout.addWidget(self.label_lightsource_list, 16, 0)

        self.line_edit_lightsourcelist = QLineEdit()
        self.line_edit_lightsourcelist.setText("W")
        self.line_edit_lightsourcelist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_lightsourcelist, 17, 0)

        self.btn_start = QPushButton("开始")
        self.btn_start.clicked.connect(self.start)
        grid_layout.addWidget(self.btn_start, 18, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,19,0)
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)


        self.setLayout(grid_layout)

        self.label_ndlist.hide()
        self.line_edit_ndlist.hide()
        self.label_xyzlist.hide()
        self.line_edit_xyzlist.hide()
        self.label_lightsource_list.hide()
        self.line_edit_lightsourcelist.hide()
    
    def _open_folder_dialog(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.line_edit_eye1_path.setText(folder_path)
        else:
            QMessageBox.critical(self,"MLColorimeter","选择路径错误",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def _open_ffc_dialog(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder_path:
            self.line_edit_ffc_path.setText(folder_path)
        else:
            QMessageBox.critical(self,"MLColorimeter","选择路径错误",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def _calculate_synthetic(self):
        if self.cb_calculate_synthetic.isChecked():
            self.label_ndlist.show()
            self.line_edit_ndlist.show()
            self.label_xyzlist.show()
            self.line_edit_xyzlist.show()
            self.label_lightsource_list.show()
            self.line_edit_lightsourcelist.show()
        else:
            self.label_ndlist.hide()
            self.line_edit_ndlist.hide()
            self.label_xyzlist.hide()
            self.line_edit_xyzlist.hide()
            self.label_lightsource_list.hide()
            self.line_edit_lightsourcelist.hide()

    def start(self):
        try:
            self.eye1_path=self.line_edit_eye1_path.text().strip()
            self.ffc_path=self.line_edit_ffc_path.text().strip()
            self.aperture_list=self.line_edit_aperture_list.text().strip().split()
            self.binning_str_list=self.line_edit_binnlist.text().strip().split()
            target_list=self.line_edit_target_size_list.text().strip().split()
            self.target_size_list=[ast.literal_eval(item) for item in target_list]
            self.is_generate_FFC=self.cb_generate_ffc.isChecked()
            self.is_calculate_synthetic=self.cb_calculate_synthetic.isChecked()
            if self.is_calculate_synthetic:
                nd_num=[int(nd) for nd in self.line_edit_ndlist.text().strip().split()]
                self.nd_list=[mlcm.MLFilterEnum(nd) for nd in nd_num]
                xyz_num=[int(xyz) for xyz in self.line_edit_xyzlist.text().strip().split()]
                self.xyz_list=[mlcm.MLFilterEnum(xyz) for xyz in xyz_num]
                self.lightsource_list=self.line_edit_lightsourcelist.text().strip().split()
            self.status_label.setText("<span style='color: green;'>状态: 正在进行...</span>")  # 更新状态
            self.btn_start.setEnabled(False)
            self.is_running=True
            parameters={
                "aperture_list":self.aperture_list,
                "binning_str_list":self.binning_str_list,
                "light_source_list":self.lightsource_list,
                "target_size_list":self.target_size_list,
                "nd_list":self.nd_list,
                "xyz_list":self.xyz_list,
                "is_generate_FFC":self.is_generate_FFC,
                "is_calculate_synthetic":self.is_calculate_synthetic,
                "eye1_path":self.eye1_path,
                "ffc_path":self.ffc_path
            }
            self.resizeffc_thread=ResizeFFCImagesThread(parameters)
            self.resizeffc_thread.finished.connect(self.on_finished)
            self.resizeffc_thread.error.connect(self.on_error)
            self.resizeffc_thread.status_update.connect(self.update_status)
            self.resizeffc_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "MLColorimeter", "exception" + e,
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            self.btn_start.setEnabled(True)
            self.is_running=False
    
    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 完成！</span>")  # 更新状态
        self.btn_start.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_start.setEnabled(True)
        self.is_running=False # 标识定标完成

    def closeEvent(self, event):
        if self.is_running:
            # 如果正在进行定标，拦截关闭事件
            event.ignore()
            QMessageBox.warning(self,"警告","程序进行中，请勿关闭窗口",QMessageBox.Ok)
        else:
            event.accept()

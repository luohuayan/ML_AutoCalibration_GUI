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
    QFormLayout
)
from PyQt5.QtGui import QIntValidator,QDoubleValidator
from core.app_config import AppConfig
from PyQt5.QtCore import pyqtSignal, Qt,QThread
import mlcolorimeter as mlcm
import cylaxismtf.MTF_cylaxis as mtfca
from scripts.cyl_axis_mtf import mtf_calculate

class RXSelfRotationThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            mtf_calculate(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class RXSelfRotationWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RX selfrotation mtf calculate")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.colorimeter = AppConfig.get_colorimeter()
        self.cylaxis=AppConfig.get_cylaxis()
        self.double_validator=QDoubleValidator()
        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self.file_name = "mono_calibration.xlsx"
        self.binning_selector=['Logic','Sensor']
        self.binning_mode=['AVERAGE','SUM']
        self.mtf_type=['CROSS','SLANT','SPOT']
        self.pixel_format=['MLMono8','MLMono10','MLMono12','MLMono16','MLRGB24','MLBayer','MLBayerGB8','MLBayerGB12']
        self._init_ui()
        self.is_running=False
    
    def _init_ui(self):
        grid_layout=QGridLayout()
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

        self.label_binn = QLabel(" binning：")
        self.line_edit_binn = QLineEdit()
        self.line_edit_binn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        int_validator=QIntValidator(0,4,self)
        self.line_edit_binn.setValidator(int_validator)
        self.line_edit_binn.setText("0")
        self.line_edit_binn.setPlaceholderText("0: 1X1, 1: 2X2, 2: 4X4, 3: 8X8, 4: 16X16")
        self.line_edit_binn.textChanged.connect(self.validate_input)
        
        from_layout0.addRow(self.label_binn, self.line_edit_binn)

        self.label_pixel_format = QLabel(" pixel_format：")
        self.line_edit_pixel_format = QComboBox()
        self.line_edit_pixel_format.addItems(self.pixel_format)
        self.line_edit_pixel_format.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.line_edit_pixel_format.setCurrentText("MLMono12")
        from_layout0.addRow(self.label_pixel_format,self.line_edit_pixel_format)

        group_box0.setLayout(from_layout0)
        grid_layout.addWidget(group_box0, 0, 0)

        self.label_ndlist = QLabel()
        self.label_ndlist.setText("nd列表, (4: ND0, 5: ND1, 6: ND2, 7:ND3, 8:ND4), 以空格隔开,如输入4 5")
        grid_layout.addWidget(self.label_ndlist, 1, 0)

        self.line_edit_ndlist = QLineEdit()
        self.line_edit_ndlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_ndlist, 2, 0)

        self.label_xyzlist = QLabel()
        self.label_xyzlist.setText("xyz列表, (1: X, 2: Y, 3: Z, 10: Clear), 以空格隔开，如输入1 2 3")
        grid_layout.addWidget(self.label_xyzlist, 3, 0)

        self.line_edit_xyzlist = QLineEdit()
        self.line_edit_xyzlist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_xyzlist, 4, 0)

        self.label_mtf_type=QLabel("MTF_type:")
        grid_layout.addWidget(self.label_mtf_type,5,0)
        self.combobox_mtf_type=QComboBox()
        self.combobox_mtf_type.addItems(self.mtf_type)
        self.combobox_mtf_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.combobox_mtf_type,6,0)

        self.label_pixel_size=QLabel("pixel_size:")
        grid_layout.addWidget(self.label_pixel_size,7,0)
        self.line_edit_pixel_size=QLineEdit()
        self.line_edit_pixel_size.setValidator(self.double_validator)
        self.line_edit_pixel_size.setText("0.00345")
        self.line_edit_pixel_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_pixel_size,8,0)

        self.label_focal_length=QLabel("focal_length:")
        grid_layout.addWidget(self.label_focal_length,9,0)
        self.line_edit_focal_length=QLineEdit()
        self.line_edit_focal_length.setValidator(self.double_validator)
        self.line_edit_focal_length.setText("40")
        self.line_edit_focal_length.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_focal_length,10,0)

        self.label_move_pixel=QLabel("move_pixel:(roi中心点离十字线中心的像素距离)")
        grid_layout.addWidget(self.label_move_pixel,11,0)
        self.line_edit_move_pixel=QLineEdit()
        intvalidator=QIntValidator()
        self.line_edit_move_pixel.setValidator(intvalidator)
        self.line_edit_move_pixel.setText("80")
        self.line_edit_move_pixel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_move_pixel,12,0)

        self.label_freq0=QLabel("freq0:")
        grid_layout.addWidget(self.label_freq0,13,0)
        self.line_edit_freq0=QLineEdit()
        doubleValidator=QDoubleValidator()
        self.line_edit_freq0.setValidator(doubleValidator)
        self.line_edit_freq0.setText("10")
        self.line_edit_freq0.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_freq0,14,0)

        self.label_cyllist = QLabel("cyl列表, (例如: -4 -3.5 -3 -2.5 -2 -1.5 -1 -0.5 0), 以空格隔开")
        grid_layout.addWidget(self.label_cyllist,15,0)
        self.line_edit_cyllist = QLineEdit()
        self.line_edit_cyllist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_cyllist,16,0)
        
        self.label_axislist = QLabel("axis列表, (例如: 0 15 30 45 60 75 90 105 120 135 150 165), 以空格隔开")
        grid_layout.addWidget(self.label_axislist,17,0)
        self.line_edit_axislist = QLineEdit()
        self.line_edit_axislist.setText("0 90 180 270")
        self.line_edit_axislist.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_axislist,18,0)

        self.label_path = QLabel()
        self.label_path.setText("保存路径(excel保存位置):")
        grid_layout.addWidget(self.label_path, 19, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 20, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 20, 1)

        self.btn_capture = QPushButton("开始MTF计算")
        self.btn_capture.clicked.connect(self.start_mtf_calculate)
        grid_layout.addWidget(self.btn_capture, 21, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,22,0)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer)

        self.setLayout(grid_layout)

    def validate_input(self):
        text=self.line_edit_binn.text()
        if text:
            value=int(text)
            if value <0 or value > 4:
                self.line_edit_binn.setText("")

    def start_mtf_calculate(self):
        try:
            self.pixel_format=self.get_current_pixel_format()
            self.binn_selector=self.get_current_binning_selector()
            self.binn_mode=self.get_current_binning_mode()
            self.binn=mlcm.Binning(int(self.line_edit_binn.text().strip()))
            self.mtftype=self.get_current_mtftype()
            nd_enum=[int(nd) for nd in self.line_edit_ndlist.text().strip().split()]
            self.nd_list=[mlcm.MLFilterEnum(nd) for nd in nd_enum]
            xyz_enum=[int(xyz) for xyz in self.line_edit_xyzlist.text().strip().split()]
            self.xyz_list=[mlcm.MLFilterEnum(xyz) for xyz in xyz_enum]
            self.pixel_size=float(self.line_edit_pixel_size.text())
            self.focal_length=float(self.line_edit_focal_length.text())
            self.freq0=float(self.line_edit_freq0.text())
            self.move_pixel=int(self.line_edit_move_pixel.text())
            self.save_path=self.line_edit_path.text()
            self.cyl_list=[float(cyl) for cyl in self.line_edit_cyllist.text().strip().split()]
            self.axis_list=[int(axis) for axis in self.line_edit_axislist.text().strip().split()]

            self.status_label.setText("<span style='color: green;'>状态: 正在运行...</span>")  # 更新状态
            self.btn_capture.setEnabled(False)
            self.is_running=True

            parameters={
                'colorimeter':self.colorimeter,
                'mtfca':self.cylaxis,
                'binn_selector':self.binn_selector,
                'binn_mode':self.binn_mode,
                'binn':self.binn,
                'mtf_type':self.mtf_type,
                'pixel_format':self.pixel_format,
                'freq0':self.freq0,
                'move_pixel':self.move_pixel,
                'save_path':self.save_path,
                'nd_list':self.nd_list,
                'xyz_list':self.xyz_list,
                'pixel_size':self.pixel_size,
                'focal_length':self.focal_length,
                'cyl_list':self.cyl_list,
                'axis_list':self.axis_list
            }
            self.rx_selfrotation_thread=RXSelfRotationThread(parameters)
            self.rx_selfrotation_thread.finished.connect(self.on_thread_finished)
            self.rx_selfrotation_thread.error.connect(self.on_thread_error)
            self.rx_selfrotation_thread.status_update.connect(self.update_status)
            self.rx_selfrotation_thread.start()

            # mtf_calculate(
            #     colorimeter=self.colorimeter,
            #     mtfca=self.cylaxis,
            #     binn_selector=self.binn_selector,
            #     binn_mode=self.binn_mode,
            #     binn=self.binn,
            #     mtf_type=self.mtftype,
            #     pixel_format=self.pixel_format,
            #     freq0=self.freq0,
            #     move_pixel=self.move_pixel,
            #     save_path=self.save_path,
            #     nd_list=self.nd_list,
            #     xyz_list=self.xyz_list,
            #     pixel_size=self.pixel_size,
            #     focal_length=self.focal_length,
            #     cyl_list=self.cyl_list,
            #     axis_list=self.axis_list
            # )
            
        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + e, QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_capture.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>状态: {message}</span>")
    
    def on_thread_finished(self):
        QMessageBox.information(self,"MLColorimeter","完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 完成！</span>")  # 更新状态
        self.btn_capture.setEnabled(True)
        self.is_running=False # 标识定标完成

    def on_thread_error(self,error_message):
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
        
    def get_current_mtftype(self):
        selected_type=self.combobox_mtf_type.currentText()
        format_mapping={
            'CROSS':mtfca.MTF_TYPE.CROSS,
            'SLANT':mtfca.MTF_TYPE.SLANT,
            'SPOT':mtfca.MTF_TYPE.SPOT
        }
        mtf_type_enum=format_mapping.get(selected_type)
        return mtf_type_enum
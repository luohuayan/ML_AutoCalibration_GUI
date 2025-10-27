from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QMessageBox,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QMenuBar,
    QMenu,
    QStatusBar,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QRect, QMetaObject
from core.app_config import AppConfig
from ui.settings import SettingsWindow
from ui.dark_heatmap import DarkHeatMapWindow
from ui.captureffc_uniformity_plot import CaptureFFC_CalUniformity_Plot_Window
from ui.mono_calibration import MonoCalibrationWindow
from ui.calculate_sph_cyl_coefficient_window import CalculateSphCylCoefficientWindow
from ui.capture_center_window import CaptureCenterWindow
from ui.capture_image_fixedLUM_window import CaptureImageFixedLUMWindow
from ui.filed_curve_window import FiledCurveWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Colorimeter Controller")
        self.setGeometry(100, 100, 1024, 768)
        self._init_ui()
        self.colorimeter = AppConfig.get_colorimeter()
        self.select_path=""

        # 初始化子窗口调用
        self.settings_window = None
        self.dark_heatmap_window = None
        self.captureffc_caluniformity_window = None
        self.monocalibration_window = None
        self.calculate_sph_cyl_coefficient_window = None
        self.capture_center_window = None
        self.capture_image_fixedLUM_window = None
        self.filed_curve_window = None
        


    def _init_ui(self):
        # 创建菜单栏
        self.create_menus()

        # 创建主界面控件
        self.create_main_widget()

    def create_menus(self):
        menubar = self.menuBar()

        # Settings 菜单
        settings_action = menubar.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)

        # Scripts 菜单
        scripts_menu = menubar.addMenu("&Scripts")

        # 子菜单项
        script1_action = QAction("capture_dark_heatmap", self)
        script1_action.triggered.connect(self.open_dark_heatmap)

        script2_action = QAction("captureffc_uniformity_plot", self)
        script2_action.triggered.connect(self.open_captureffc_caluniformity)

        script3_action = QAction("monocalibration", self)
        script3_action.triggered.connect(self.open_monocalibration)

        script4_action = QAction("calculate_sph_cyl_coef", self)
        script4_action.triggered.connect(self.open_calculate_sph_cyl_coefficient)

        script5_action = QAction("calculate_center", self)
        script5_action.triggered.connect(self.open_capture_center)

        script6_action = QAction("capture_image_fixedLUM", self)
        script6_action.triggered.connect(self.open_capture_image_fixedLUM)

        script7_action = QAction("filed_curve", self)
        script7_action.triggered.connect(self.open_filed_curve)

        scripts_menu.addAction(script1_action)
        scripts_menu.addAction(script2_action)
        scripts_menu.addAction(script3_action)
        scripts_menu.addAction(script4_action)
        scripts_menu.addAction(script5_action)
        scripts_menu.addAction(script6_action)
        scripts_menu.addAction(script7_action)

    def create_main_widget(self):
        # 主控件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 按钮
        self.connect_btn = QPushButton("Connect", self)
        self.disconnect_btn = QPushButton("Disconnect", self)

        # 设置按钮样式
        self.connect_btn.setStyleSheet("QPushButton { padding: 8px 16px; }")
        self.disconnect_btn.setStyleSheet("QPushButton { padding: 8px 16px; }")

        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        btn_layout.addStretch()

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

        main_widget.setLayout(main_layout)

        # 连接按钮信号
        self.connect_btn.clicked.connect(self.connect_colorimeter)
        self.disconnect_btn.clicked.connect(self.disconnect_colorimeter)

    def connect_colorimeter(self):
        ret = self.colorimeter.ml_connect()
        if not ret.success:
            QMessageBox.critical(
                self,
                "MLColorimeter",
                "ml_connect error",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
        QMessageBox.information(
                self,
                "MLColorimeter",
                "连接成功",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

    def disconnect_colorimeter(self):
        ret = self.colorimeter.ml_disconnect()
        if not ret.success:
            QMessageBox.critical(
                self,
                "MLColorimeter",
                "ml_disconnect error",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
        QMessageBox.information(
                self,
                "MLColorimeter",
                "断开连接成功",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

    def open_settings(self):
        self.settings_window = SettingsWindow(self)
        self.settings_window.path_changed.connect(self.handle_path_changed)
        self.settings_window.exec_()
    
    
    def handle_path_changed(self,path):
        self.select_path=path


    def open_dark_heatmap(self):
        self.dark_heatmap_window = DarkHeatMapWindow()
        self.dark_heatmap_window.exec_()

    def open_captureffc_caluniformity(self):
        self.captureffc_caluniformity_window = CaptureFFC_CalUniformity_Plot_Window()
        self.captureffc_caluniformity_window.exec_()

    def open_monocalibration(self):
        self.monocalibration_window = MonoCalibrationWindow(self.select_path)
        self.monocalibration_window.exec_()

    def open_calculate_sph_cyl_coefficient(self):
        self.calculate_sph_cyl_coefficient_window = CalculateSphCylCoefficientWindow()
        self.calculate_sph_cyl_coefficient_window.exec_()

    def open_capture_center(self):
        self.capture_center_window = CaptureCenterWindow()
        self.capture_center_window.exec_()

    def open_capture_image_fixedLUM(self):
        self.capture_image_fixedLUM_window = CaptureImageFixedLUMWindow(self.select_path)
        self.capture_image_fixedLUM_window.exec_()

    def open_filed_curve(self):
        self.filed_curve_window = FiledCurveWindow()
        self.filed_curve_window.exec_()

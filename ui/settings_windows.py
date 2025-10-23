from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QSizePolicy,
    QMessageBox
)
from core.app_config import AppConfig
from PyQt5.QtCore import pyqtSignal, Qt


class SettingsWindow(QWidget):
    path_changed = pyqtSignal(str)

    def __init__(self, parent=None, dialog_title="选择文件夹", default_path=""):
        super().__init__(parent)
        self.setWindowTitle("Setting")
        self.setGeometry(300, 300, 500, 200)
        self.dialog_title = dialog_title
        self.default_path = default_path
        self.colorimeter = AppConfig.get_colorimeter()
        self._init_ui()

    def _init_ui(self):
        # 水平布局：输入框 + 按钮
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 去除边距，方便嵌入其他布局

        self.label = QLabel()
        self.label.setText("配置文件路径:")
        layout.addWidget(self.label)

        # 输入框（显示路径）
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)  # 设置为只读
        self.line_edit.setPlaceholderText("未选择文件夹")
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.line_edit)

        # 按钮（触发选择）
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        layout.addWidget(self.btn_browse)

        self.setLayout(layout)

    def _open_folder_dialog(self):
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.dialog_title,
            self.default_path if self.default_path else "",  # 初始路径
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.set_path(folder_path)
            ret = self.colorimeter.ml_add_module(path_list=[folder_path])
            if not ret.success:
                QMessageBox.critical(self,"MLColorimeter","ml_add_module error",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.close()
        else:
            QMessageBox.critical(self,"MLColorimeter","选择路径错误",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.close()

    def get_path(self):
        """获取当前选择的路径"""
        return self.line_edit.text().strip()

    def set_path(self, path):
        """直接设置路径（不弹出对话框）"""
        if path != self.get_path():
            self.line_edit.setText(path)
            self.line_edit.setToolTip(path)  # 悬浮显示完整路径
            self.path_changed.emit(path)  # 触发信号

    def clear(self):
        """清空路径"""
        self.line_edit.clear()

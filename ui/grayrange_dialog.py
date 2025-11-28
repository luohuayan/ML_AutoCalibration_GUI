
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QMessageBox,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QDialog,
    QMenuBar,
    QMenu,
    QStatusBar,
    QLineEdit,
    QLabel,
    QDialogButtonBox,
)
class GrayRangeDialog(QDialog):
    def __init__(self, loop_i, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"输入灰度 {loop_i}0% 的灰度显示范围")

        self.loop_i = loop_i
        self.min_gray_input = QLineEdit(self)
        self.max_gray_input = QLineEdit(self)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"灰度 {loop_i}0% 对应的灰度显示范围:"))
        
        layout.addWidget(QLabel("最小值:"))
        layout.addWidget(self.min_gray_input)
        
        layout.addWidget(QLabel("最大值:"))
        layout.addWidget(self.max_gray_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_values(self):
        try:
            min_gray = int(self.min_gray_input.text())
            max_gray = int(self.max_gray_input.text())
            return min_gray, max_gray
        except ValueError:
            return None, None
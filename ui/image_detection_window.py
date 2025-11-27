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
)
from PyQt5.QtCore import pyqtSignal, Qt,QThread
from scripts.image_detection import check_image_corruption
import os
from PIL import Image

class ImageDetectionThread(QThread):
    finished=pyqtSignal() # 线程完成信号
    error=pyqtSignal(str) # 错误信号
    status_update=pyqtSignal(str) # 状态更新信号

    def __init__(self, parameters):
        super().__init__()
        self.parameters=parameters
    
    def run(self):
        try:
            check_image_corruption(status_callback=self.status_update.emit, **self.parameters)
            self.finished.emit() # 发送完成信号
        except Exception as e:
            self.error.emit(str(e)) # 发送错误信号

class ImageDetectionWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("capture field curve")
        self.setGeometry(200, 200, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.dialog_title = "选择文件夹"
        self.default_path = ""
        self._init_ui()

        self.is_running=False
    
    def _init_ui(self):
        grid_layout = QGridLayout()
        self.label_path = QLabel()
        self.label_path.setText("检测图像路径:")
        grid_layout.addWidget(self.label_path, 0, 0)

        self.line_edit_path = QLineEdit()
        self.line_edit_path.setReadOnly(True)  # 设置为只读
        self.line_edit_path.setPlaceholderText("未选择文件夹")
        self.line_edit_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_path, 1, 0)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._open_folder_dialog)
        grid_layout.addWidget(self.btn_browse, 1, 1)

        self.label_save_path = QLabel()
        self.label_save_path.setText("保存路径:")
        grid_layout.addWidget(self.label_save_path, 2, 0)

        self.line_edit_save_path = QLineEdit()
        self.line_edit_save_path.setReadOnly(True)  # 设置为只读
        self.line_edit_save_path.setPlaceholderText("未选择文件夹")
        self.line_edit_save_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout.addWidget(self.line_edit_save_path, 3, 0)

        self.btn_save_browse = QPushButton("浏览...")
        self.btn_save_browse.clicked.connect(self._open_save_dialog)
        grid_layout.addWidget(self.btn_save_browse, 3, 1)

        self.btn_check = QPushButton("开始检测")
        self.btn_check.clicked.connect(self.start_check)
        grid_layout.addWidget(self.btn_check, 4, 0)

        self.status_label=QLabel("状态：等待开始")
        self.status_label.setWordWrap(True)  # 设置自动换行
        grid_layout.addWidget(self.status_label,5,0)
        
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

    def _open_save_dialog(self):
        folder_path,_ = QFileDialog.getOpenFileName(
            self,
            "选择保存文件",
            self.default_path if self.default_path else "",  # 初始路径
            "Text Files (*.txt);;All Files (*)",
            options=QFileDialog.DontResolveSymlinks,
        )

        if folder_path:
            self.line_edit_save_path.setText(folder_path)
        else:
            QMessageBox.critical(self,"MLColorimeter","选择路径错误",QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)

    def start_check(self):
        try:
            self.file_path=self.line_edit_path.text()
            self.output_file=self.line_edit_save_path.text()
            if not self.file_path or not self.output_file:
                QMessageBox.warning(self,"MLColorimeter","检测图像路径或保存路径未选择",QMessageBox.Ok)
                return
            for root,dirs,files in os.walk(self.file_path): # type: ignore
                for file in files: # type: ignore
                    # 检查文件扩展名是否为.tif或.tiff
                    if file.lower().endswith(('.tif','.tiff')):
                        file_path=os.path.join(root,file)
                        try:
                            with Image.open(file_path) as img:
                                self.width,self.height=img.size
                                QMessageBox.information(self,"MLColorimeter",f"检测的正常的第一张图像分辨率为：{self.width}x{self.height}像素",QMessageBox.Ok)
                                break
                        except (IOError,SyntaxError) as e: # type: ignore
                            # 如果发生异常，表示图像损坏
                            continue
                else:
                    continue
                break

            
            response = QMessageBox.question(self,"MLColorimeter",f"是否将{self.width}x{self.height}分辨率作为检测标准?",QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
            if response==QMessageBox.Yes:
                self.status_label.setText("<span style='color: green;'>状态: 正在进行检测...</span>")  # 更新状态
                self.btn_check.setEnabled(False)
                self.is_running=True
                parameters={
                    'folder_path':self.file_path,
                    'output_file':self.output_file,
                    'width':self.width,
                    'height':self.height
                }
                self.image_detection_thread=ImageDetectionThread(parameters)
                self.image_detection_thread.finished.connect(self.on_thread_finished)
                self.image_detection_thread.error.connect(self.on_thread_error)
                self.image_detection_thread.status_update.connect(self.update_status)
                self.image_detection_thread.start()

                # check_image_corruption(
                # folder_path=self.file_path,
                # output_file=self.output_file,
                # width=self.width,
                # height=self.height
                # )
            else:
                return

        except Exception as e:
            QMessageBox.critical(self,"MLColorimeter","exception" + str(e), QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
            self.btn_check.setEnabled(True)
            self.is_running=False

    def update_status(self,message):
        self.status_label.setText(f"<span style='color: green;'>检测: {message}</span>")
    
    def on_thread_finished(self):
        QMessageBox.information(self,"MLColorimeter","检测完成!",QMessageBox.Ok)
        self.status_label.setText("<span style='color: green;'>状态: 检测完成！</span>")  # 更新状态
        self.btn_check.setEnabled(True)
        self.is_running=False 

    def on_thread_error(self,error_message):
        QMessageBox.critical(self, "MLColorimeter", "发生错误: " + error_message, QMessageBox.Ok)
        self.status_label.setText(f"<span style='color: red;'>状态: 发生错误: {error_message}</span>")  # 更新状态为红色
        self.btn_check.setEnabled(True)
        self.is_running=False 

    def closeEvent(self, event):
        if self.is_running:
            event.ignore()
            QMessageBox.warning(self,"警告","程序运行中，请勿关闭窗口",QMessageBox.Ok)
        else:
            event.accept()
    # def check_image_corruption(
    #         folder_path:str,
    #         output_file:str
    # ):
    #     # 存储损坏图像的路径
    #     corrupted_images=[] # type: ignore

    #     # 存储分辨率不符合的图像路径
    #     unmatched_images=[]  # type: ignore
    #     # 第一张图像分辨率
    #     first_image_resolution=None # type: ignore

    #     for root,dirs,files in os.walk(folder_path): # type: ignore
    #         for file in files: # type: ignore
    #             # 检查文件扩展名是否为.tif或.tiff
    #             if file.lower().endswith(('.tif','.tiff')):
    #                 file_path=os.path.join(root,file)
    #                 print(file_path)
    #                 try:
    #                     with Image.open(file_path) as img: # type: ignore
    #                         # 检查图像是否为空或损坏
    #                         img.load() # 强制加载图像数据以检查是否有效
    #                         if img.size==(0,0) or img.getbbox() is None:  # 没有有效像素
    #                             corrupted_images.append(file_path)
    #                         else:
    #                             if first_image_resolution is None:
    #                                 first_image_resolution=img.size
    #                                 # 弹窗确认分辨率
    #                                 resolution_message=f"第一张图像分辨率为：{first_image_resolution[0]}x{first_image_resolution[1]}像素\n,是否将此分辨率作为标准进行检测？" # type: ignore
    #                                 roots=tk.Tk()
    #                                 roots.withdraw()
    #                                 confirm=messagebox.askyesno("确认分辨率",resolution_message) # type: ignore

    #                                 if not confirm:
    #                                     print("用户取消了分辨率确认，程序终止。")
    #                                     return
    #                             elif img.size!=first_image_resolution:
    #                                 unmatched_images.append(file_path)
                    
    #                 except (IOError,SyntaxError) as e: # type: ignore
    #                     # 如果发生异常，记录损坏的图像
    #                     corrupted_images.append(file_path)
        
    #     # 将损坏图像的路径写入输出文件
    #     with open(output_file,'w') as f:
    #         f.write("损坏图像路径：\n")
    #         for image_path in corrupted_images:
    #             f.write(image_path+'\n')
            
    #         f.write("\n分辨率不符合的图像路径：\n")
    #         for image_path in unmatched_images:
    #             f.write(image_path+'\n')
        
    #     print(f"检测完成，损坏图像路径或分辨率不符合的图像路径已保存到 {output_file}。")

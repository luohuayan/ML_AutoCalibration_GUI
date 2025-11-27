import os
from PIL import Image
import tkinter as tk
from tkinter import messagebox

def get_image_resolution(file_path):
    with Image.open(file_path) as img:
        return img.size

def check_image_corruption(
        folder_path:str,
        output_file:str,
        width:int,
        height:int,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    # 存储损坏图像的路径
    corrupted_images=[] # type: ignore

    # 存储分辨率不符合的图像路径
    unmatched_images=[]  # type: ignore

    for root,dirs,files in os.walk(folder_path): # type: ignore
        for file in files: # type: ignore
            # 检查文件扩展名是否为.tif或.tiff
            if file.lower().endswith(('.tif','.tiff')):
                file_path=os.path.join(root,file)
                update_status(file_path)
                try:
                    with Image.open(file_path) as img: # type: ignore
                        # 检查图像是否为空或损坏
                        img.load() # 强制加载图像数据以检查是否有效
                        if img.size==(0,0) or img.getbbox() is None:  # 没有有效像素
                            corrupted_images.append(file_path)
                        elif width!=img.width or height!=img.height:
                            unmatched_images.append(file_path)
                except (IOError,SyntaxError) as e: # type: ignore
                    # 如果发生异常，记录损坏的图像
                    corrupted_images.append(file_path)
    
    # 将损坏图像的路径写入输出文件
    with open(output_file,'w') as f:
        f.write("损坏图像路径：\n")
        for image_path in corrupted_images:
            f.write(image_path+'\n')
        
        f.write("\n分辨率不符合的图像路径：\n")
        for image_path in unmatched_images:
            f.write(image_path+'\n')
    
    update_status(f"检测完成，损坏图像路径或分辨率不符合的图像路径已保存到 {output_file}。")

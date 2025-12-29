import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime
from threading import Thread
import time
import matplotlib.pyplot as plt


def resize_crop_images(image, target_size=(5984, 6000)):
    h, w = image.shape[:2]

    # 计算缩放比例，保持长宽比
    scale = max(target_size[0]/w, target_size[1]/h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # 调整大小
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 计算裁剪区域（居中裁剪）
    start_x = (new_w - target_size[0]) // 2
    start_y = (new_h - target_size[1]) // 2

    # 裁剪
    cropped = resized[start_y:start_y+target_size[1],
                    start_x:start_x+target_size[0]]

    return cropped


def cal_synthetic_mean_images(
    module_id: int,
    save_path: str,
    nd: mlcm.MLFilterEnum,
    xyz: mlcm.MLFilterEnum,
    sphere_list: List[float],
    light_source: str,
    aperture: str
):
    # aperture = ml_colorimeter.ml_get_aperture()

    ml_colorimeter.ml_cal_synthetic_mean_images(
        module_id=module_id,
        save_path=save_path,
        aperture=aperture,
        nd=nd,
        xyz=xyz,
        sphere_list=sphere_list,
        light_source=light_source
    )


def find_tif_files(root_dir):
    tif_files = []

    # 遍历目录树
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.tif')):
                # 获取完整文件路径
                full_path = os.path.join(root, file)
                tif_files.append(full_path)

    return tif_files

def resize_crop_images(
        colorimeter:mlcm.ML_Colorimeter,
        eye1_path:str,
        ffc_path:str,
        aperture_list:List[str],
        binning_str_list:List[str],
        target_size_list:List[tuple],
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        light_source_list:List[str],
        is_calculate_synthetic:bool=False,

):
    path_list = [
        eye1_path,
    ]
    # add mono module into ml_colorimeter system, according to path_list create one or more mono module
    ret = colorimeter.ml_add_module(path_list=path_list)
    if not ret.success:
        raise RuntimeError("ml_add_module error")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)

    for aperture in aperture_list:
            for binning_str in binning_str_list:
                for target_size in target_size_list:
                    # find and resize images
                    file_list = find_tif_files(ffc_path)
                    for tif_file in file_list:
                        image = cv2.imread(tif_file, -1)
                        cropped_image = resize_crop_images(image, target_size)
                        cropped_tif_file = tif_file.replace("FFC", "FFC" + binning_str)
                        parent_dir = os.path.dirname(cropped_tif_file)
                        os.makedirs(parent_dir, exist_ok=True)
                        cv2.imwrite(cropped_tif_file, cropped_image)
                        print(cropped_tif_file)
            print("resize all image finish")


if __name__ == '__main__':
    eye1_path = r"D:\MLOptic\MLColorimeter\config\EYE1"
    ffc_path = r"C:\Users\huayan.luo\Desktop\FFC"
    path_list = [
        eye1_path,
    ]
    try:
        # create a ML_Colorimeter system instance
        ml_colorimeter = mlcm.ML_Colorimeter()
        # add mono module into ml_colorimeter system, according to path_list create one or more mono module
        ret = ml_colorimeter.ml_add_module(path_list=path_list)
        if not ret.success:
            raise RuntimeError("ml_add_module error")

        module_id = 1
        ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)

        aperture_list = ["2mm"]

        binning_str_list = ["_2binn"]
        target_size_list = [(5984, 6000)]

        nd_list = [mlcm.MLFilterEnum.ND0, mlcm.MLFilterEnum.ND1]
        xyz_list = [mlcm.MLFilterEnum.X, mlcm.MLFilterEnum.Y,mlcm.MLFilterEnum.Z, mlcm.MLFilterEnum.Clear]
        light_source_list = ["R", "G", "B", "W"]

        is_calculate_synthetic = False

        for aperture in aperture_list:
            for binning_str in binning_str_list:
                for target_size in target_size_list:
                    # find and resize images
                    file_list = find_tif_files(ffc_path)
                    for tif_file in file_list:
                        image = cv2.imread(tif_file, -1)
                        cropped_image = resize_crop_images(image, target_size)
                        cropped_tif_file = tif_file.replace("FFC", "FFC" + binning_str)
                        parent_dir = os.path.dirname(cropped_tif_file)
                        os.makedirs(parent_dir, exist_ok=True)
                        cv2.imwrite(cropped_tif_file, cropped_image)
                        print(cropped_tif_file)
            print("resize all image finish")

        for binning_str in binning_str_list:
            save_path = ffc_path.replace("FFC", "FFC" + binning_str)
            # calculate synthetic images
            if is_calculate_synthetic:
                sphere_list = [0]
                for aperture in aperture_list:
                    for light_source in light_source_list:
                        for nd in nd_list:
                            save_path = eye1_path
                            for xyz in xyz_list:
                                cal_synthetic_mean_images(
                                    module_id=module_id,
                                    save_path=save_path,
                                    nd=nd,
                                    xyz=xyz,
                                    sphere_list=sphere_list,
                                    light_source=light_source,
                                    aperture=aperture
                                )
                                print("calculate mean images for: " +
                                    mlcm.MLFilterEnum_to_str(xyz))
                            print("calculate mean images for: " +
                                mlcm.MLFilterEnum_to_str(nd))
                        print("calculate mean images for: " + light_source)
            print("calculate ffc synthetic mean finish")

    except Exception as e:
        print(e)

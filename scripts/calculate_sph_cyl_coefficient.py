import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def calculate_sph_cyl_coefficinet():
    save_path = r"D:\sph_cyl_coefficient"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    nd = mlcm.MLFilterEnum.ND0
    # xyz filter list to switch during capture
    xyz = mlcm.MLFilterEnum.Y

    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    ret = ml_mono.ml_move_nd_syn(nd)
    if not ret.success:
        raise RuntimeError("ml_move_nd_syn error")

    ret = ml_mono.ml_move_xyz_syn(xyz)
    if not ret.success:
        raise RuntimeError("ml_move_xyz_syn error")

    exposure = mlcm.pyExposureSetting(
        exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=21
    )
    ret = ml_mono.ml_set_exposure(exposure)
    if not ret.success:
        raise RuntimeError("ml_set_exposure error")

    for i in range(10):
        sph_coefficient = []
        cyl_coefficient = []
        last_sph = 0
        last_cyl = 0
        for sph in [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4]:
            rx = mlcm.pyRXCombination(sph=sph, cyl=0, axis=0)
            ret = ml_mono.ml_set_rx_syn(rx)
            if not ret.success:
                raise RuntimeError("ml_set_rx_syn error")

            ret = ml_mono.ml_capture_image_syn()
            if not ret.success:
                raise RuntimeError("ml_capture_image_syn error")

            img = ml_mono.ml_get_image()
            cv2.imwrite(
                save_path + "\\" + mlcm.pyRXCombination_to_str(rx) + ".tif", img
            )
            gray = cv2.mean(img[2502:3502, 3460:4460])[0]
            sph_coefficient.append(gray)

            if sph == 0:
                last_sph = gray
        for i in range(len(sph_coefficient)):
            sph_coefficient[i] = format(sph_coefficient[i] / last_sph, ".3f")

        print("sph coefficient: ")
        print(sph_coefficient)

        for cyl in [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0]:
            rx = mlcm.pyRXCombination(sph=0, cyl=cyl, axis=0)
            ret = ml_mono.ml_set_rx_syn(rx)
            if not ret.success:
                raise RuntimeError("ml_set_rx_syn error")

            ret = ml_mono.ml_capture_image_syn()
            if not ret.success:
                raise RuntimeError("ml_capture_image_syn error")

            img = ml_mono.ml_get_image()
            cv2.imwrite(
                save_path + "\\" + mlcm.pyRXCombination_to_str(rx) + ".tif", img
            )
            gray = cv2.mean(img[2502:3502, 3460:4460])[0]
            cyl_coefficient.append(gray)

            if cyl == 0:
                last_cyl = gray
        for i in range(len(cyl_coefficient)):
            cyl_coefficient[i] = format(cyl_coefficient[i] / last_cyl, ".3f")

        print("cyl coefficient: ")
        print(cyl_coefficient)

    print("calculate sph cyl coefficient finish")


if __name__ == "__main__":
    eye1_path = r"D:\MLColorimeter\config\EYE1"
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
        # connect all module in the ml_colorimeter system
        ret = ml_colorimeter.ml_connect()
        if not ret.success:
            raise RuntimeError("ml_connect error")

        module_id = 1
        ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)

        calculate_sph_cyl_coefficinet()
    except Exception as e:
        print(e)

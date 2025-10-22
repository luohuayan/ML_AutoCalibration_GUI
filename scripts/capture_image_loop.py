import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def capture_images_loop():
    save_path = r"E:\duling_uniformity"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # nd filter to switch during capture
    nd_list = [mlcm.MLFilterEnum.ND0]
    # xyz filter list to switch during capture
    xyz_list = [mlcm.MLFilterEnum.Y]

    # exposure map of color filter during capture
    exposure_map = {
        mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(
            exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100
        ),
        mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(
            exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100
        ),
        mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(
            exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100
        ),
    }

    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    ffc_csv = save_path + r"\capture_images_loop-20240925.csv"
    output_title = [
        "RX",
        "ColorFilter",
        "NDFilter",
        "Light Source",
        "Gray Value",
        "Exposuretime",
    ]
    with open(ffc_csv, "a+", newline="") as f:
        mywriter = csv.writer(f)
        mywriter.writerow(output_title)

    rx = mlcm.pyRXCombination(sph=0, cyl=0, axis=0)
    ret = ml_mono.ml_set_rx_syn(rx)
    if not ret.success:
        raise RuntimeError("ml_set_rx_syn error")

    for nd in nd_list:
        ret = ml_mono.ml_move_nd_syn(nd)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")

        for xyz in xyz_list:
            ret = ml_mono.ml_move_xyz_syn(xyz)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn error")

            ret = ml_mono.ml_set_exposure(exposure_map[xyz])
            if not ret.success:
                raise RuntimeError("ml_set_exposure error")

            get_exposure_time = ml_mono.ml_get_exposure_time()

            ret = ml_colorimeter.ml_capture_image_syn()
            if not ret.success:
                raise RuntimeError("ml_capture_image_syn error")

            get_image = ml_mono.ml_get_image()

            line = []
            line.append(mlcm.pyRXCombination_to_str(rx))
            line.append(mlcm.MLFilterEnum_to_str(xyz))
            line.append(mlcm.MLFilterEnum_to_str(nd))
            line.append("W")
            gray = cv2.mean(get_image)[0]
            line.append(gray)
            line.append(get_exposure_time)
            with open(ffc_csv, "a+", newline="") as f:
                mywriter = csv.writer(f)
                mywriter.writerow(line)
            print("capture image for: " + mlcm.MLFilterEnum_to_str(xyz))
        print("capture image for: " + mlcm.MLFilterEnum_to_str(nd))
    print("capture all images finish")


if __name__ == "__main__":
    eye1_path = r"I:\duling ffc\EYE1"
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

        for i in range(100):
            capture_images_loop()
    except Exception as e:
        print(e)

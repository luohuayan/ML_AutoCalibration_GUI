import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def capture_RX_center():
    save_path = r"D:\aolanduo2_RX_center"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # nd filter to switch during capture
    nd_list = [mlcm.MLFilterEnum.ND0]
    # xyz filter list to switch during capture
    xyz_list = [mlcm.MLFilterEnum.X, mlcm.MLFilterEnum.Y, mlcm.MLFilterEnum.Z]

    exposure_map_obj = {
        mlcm.MLFilterEnum.ND0: {
            mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=20
            ),
            mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=20
            ),
            mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=25
            ),
        },
        mlcm.MLFilterEnum.ND1: {
            mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=180
            ),
            mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=100
            ),
            mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=150
            ),
        },
        mlcm.MLFilterEnum.ND2: {
            mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4556
            ),
            mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4054
            ),
            mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=4999
            ),
        },
    }

    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    for nd in nd_list:
        ret = ml_mono.ml_move_nd_syn(nd)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")

        for xyz in xyz_list:
            ret = ml_mono.ml_move_xyz_syn(xyz)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn error")

            out_path = (
                save_path
                + "\\"
                + mlcm.MLFilterEnum_to_str(nd)
                + "_"
                + mlcm.MLFilterEnum_to_str(xyz)
            )
            if not os.path.exists(out_path):
                os.makedirs(out_path)

            ret = ml_mono.ml_set_exposure(exposure_map_obj[nd][xyz])
            if not ret.success:
                raise RuntimeError("ml_set_exposure error")

            for sph in [0]:
                for cyl in [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0]:
                    for axis in [
                        0,
                        15,
                        30,
                        45,
                        60,
                        75,
                        90,
                        105,
                        120,
                        135,
                        150,
                        165,
                        180,
                        195,
                        210,
                        225,
                        240,
                        255,
                        270,
                        285,
                        300,
                        315,
                        330,
                        345,
                        360,
                    ]:
                        rx = mlcm.pyRXCombination(sph=sph, cyl=cyl, axis=axis)
                        ret = ml_mono.ml_set_rx_syn(rx)
                        if not ret.success:
                            raise RuntimeError("ml_set_rx_syn error")

                        ret = ml_mono.ml_capture_image_syn()
                        if not ret.success:
                            raise RuntimeError("ml_capture_image_syn error")

                        get_image = ml_mono.ml_get_image()
                        img_path = (
                            out_path + "\\" + mlcm.pyRXCombination_to_str(rx) + ".tif"
                        )
                        roi_img = get_image[2680:3280, 3650:4250]
                        cv2.imwrite(img_path, roi_img)
                        print("capture image for: " + mlcm.pyRXCombination_to_str(rx))
            print("capture image for: " + mlcm.MLFilterEnum_to_str(xyz))
        print("capture image for: " + mlcm.MLFilterEnum_to_str(nd))
    print("capture RX center finish")


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

        capture_RX_center()

    except Exception as e:
        print(e)

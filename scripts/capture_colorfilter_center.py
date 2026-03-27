import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime
import time


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def capture_colorfilter_center(
        colorimeter: mlcm.ML_Colorimeter,
        save_path: str,
        nd_list: List[mlcm.MLFilterEnum],
        xyz_list: List[mlcm.MLFilterEnum],
        exposure_map_obj: Dict[mlcm.MLFilterEnum,
                               Dict[mlcm.MLFilterEnum, mlcm.pyExposureSetting]] = {},
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    # test
    # update_status("capture_colorfilter_center start")
    # time.sleep(10)
    # update_status("capture_colorfilter_center finish")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)

    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    rx = mlcm.pyRXCombination(sph=0, cyl=0, axis=0)
    ret = ml_mono.ml_set_rx_syn(rx)
    if not ret.success:
        raise RuntimeError("ml_set_rx_syn")

    for nd in nd_list:
        nd_enum = mlcm.MLFilterEnum(int(nd))
        ret = ml_mono.ml_move_nd_syn(nd_enum)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")

        for xyz in xyz_list:
            xyz_enum = mlcm.MLFilterEnum(int(xyz))
            ret = ml_mono.ml_move_xyz_syn(xyz_enum)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn")

            ret = ml_mono.ml_set_exposure(exposure_map_obj[nd_enum][xyz_enum])
            if not ret.success:
                raise RuntimeError("ml_set_exposure error")

            ret = ml_mono.ml_capture_image_syn()
            if not ret.success:
                raise RuntimeError("ml_capture_image_syn error")

            get_image = ml_mono.ml_get_image()
            img_path = (
                save_path
                + "\\"
                + mlcm.MLFilterEnum_to_str(nd_enum)
                + "_"
                + mlcm.MLFilterEnum_to_str(xyz_enum)
                + ".tif"
            )

            cv2.imwrite(img_path, get_image)
            update_status(
                f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{mlcm.MLFilterEnum_to_str(xyz_enum)} save success")
    update_status("finish")

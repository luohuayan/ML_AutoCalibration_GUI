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


def capture_RX_center(
    colorimeter: mlcm.ML_Colorimeter,
    save_path: str,
    nd_list: List[mlcm.MLFilterEnum],
    xyz_list: List[mlcm.MLFilterEnum],
    cyl_list: List,
    axis_list: List,
    roi: mlcm.pyCVRect,
    exposure_map_obj: Dict[mlcm.MLFilterEnum, Dict[mlcm.MLFilterEnum, mlcm.pyExposureSetting]],
    status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    mono = colorimeter.ml_bino_manage.ml_get_module_by_id(1)
    pixel_format = mlcm.MLPixelFormat.MLBayerRG12
    ret = mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    for nd in nd_list:
        ret = mono.ml_move_nd_syn(nd)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")

        for xyz in xyz_list:
            ret = mono.ml_move_xyz_syn(xyz)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn error")

            out_path = (
                save_path
                + "\\"
                + mlcm.MLFilterEnum_to_str(nd)
                + "_"
                + mlcm.MLFilterEnum_to_str(xyz)
            )
            os.makedirs(out_path, exist_ok=True)

            ret = mono.ml_set_exposure(exposure_map_obj[nd][xyz])
            if not ret.success:
                raise RuntimeError("ml_set_exposure error")

            for cyl in cyl_list:
                for axis in axis_list:
                    rx = mlcm.pyRXCombination(0, cyl, axis)
                    ret = mono.ml_set_rx_syn(rx)
                    if not ret.success:
                        raise RuntimeError("ml_set_rx_syn error")

                    ret = mono.ml_capture_image_syn()
                    if not ret.success:
                        raise RuntimeError("ml_capture_image_syn error")

                    get_image = mono.ml_get_image()
                    X, Y, Z = cv2.split(get_image)  # type: ignore
                    img_path = (
                        out_path + "\\" +
                        mlcm.pyRXCombination_to_str(rx) + ".tif"
                    )
                    roi_img = Y[roi.y:roi.y +
                                roi.height, roi.x:roi.x+roi.width]
                    cv2.imwrite(img_path, roi_img)
                    update_status(
                        f"capture image for: {mlcm.pyRXCombination_to_str(rx)}")
            update_status(
                f"capture image for: {mlcm.MLFilterEnum_to_str(xyz)}")
        update_status(f"capture image for: {mlcm.MLFilterEnum_to_str(nd)}")
    update_status("capture RX center finish")

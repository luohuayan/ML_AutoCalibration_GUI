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
        colorimeter:mlcm.ML_Colorimeter,
        sph_list:List[float],
        cyl_list:List[float],
        axis_list:List[int],
        save_path:str,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        roi:mlcm.pyCVRect,
        exposure_map_obj:Dict[mlcm.MLFilterEnum,Dict[mlcm.MLFilterEnum,mlcm.pyExposureSetting]]={},
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    # #test
    # update_status("capture_RX_center start")
    # time.sleep(10)
    # update_status("capture_RX_center finish")

    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    for nd in nd_list:
        nd_enum = mlcm.MLFilterEnum(int(nd))
        ret = ml_mono.ml_move_nd_syn(nd_enum)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")

        for xyz in xyz_list:
            xyz_enum = mlcm.MLFilterEnum(int(xyz))
            ret = ml_mono.ml_move_xyz_syn(xyz_enum)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn error")

            out_path = (
                save_path
                + "\\"
                + mlcm.MLFilterEnum_to_str(nd_enum)
                + "_"
                + mlcm.MLFilterEnum_to_str(xyz_enum)
            )
            if not os.path.exists(out_path):
                os.makedirs(out_path)

            ret = ml_mono.ml_set_exposure(exposure_map_obj[nd_enum][xyz_enum])
            if not ret.success:
                raise RuntimeError("ml_set_exposure error")

            for sph in sph_list:
                for cyl in cyl_list:
                    for axis in axis_list:
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
                        roi_img = get_image[roi.y:roi.y+roi.height, roi.x:roi.x+roi.width]
                        cv2.imwrite(img_path, roi_img)
                        update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{mlcm.MLFilterEnum_to_str(xyz_enum)}_{mlcm.pyRXCombination_to_str(rx)} save success")
    update_status("finish")


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
        # print(e)
        pass

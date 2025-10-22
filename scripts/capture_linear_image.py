import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def capture_linear_images():
    save_path = r"F:\FFC"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # nd filter to switch during capture
    nd_list = [mlcm.MLFilterEnum.ND0]
    # xyz filter list to switch during capture
    xyz_list = [mlcm.MLFilterEnum.X, mlcm.MLFilterEnum.Y, mlcm.MLFilterEnum.Z]
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

    for sph in [0]:
        for cyl in [0]:
            for axis in [0]:
                rx = mlcm.pyRXCombination(sph=sph, cyl=cyl, axis=axis)
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

                        exposure = mlcm.pyExposureSetting(
                            exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100
                        )
                        ret = ml_mono.ml_set_exposure(exposure)
                        if not ret.success:
                            raise RuntimeError("ml_set_exposure error")

                        get_exposure_time = ml_mono.ml_get_exposure_time()
                        print(get_exposure_time)

                        if get_exposure_time > 5:
                            step = int((get_exposure_time - 5) / 15)
                            # 在5ms与get_exposure_time之间遍历曝光时间，步长为step
                            for et in range(5, int(get_exposure_time), int(step)):
                                # 遍历区间，设置曝光时间
                                exposure = mlcm.pyExposureSetting(
                                    exposure_mode=mlcm.ExposureMode.Fixed,
                                    exposure_time=et,
                                )

                                ret = ml_mono.ml_set_exposure(exposure)
                                if not ret.success:
                                    raise RuntimeError("ml_set_exposure error")

                                ret = ml_colorimeter.ml_capture_image_syn()
                                if not ret.success:
                                    raise RuntimeError("ml_capture_image_syn error")

                                get_image = ml_mono.ml_get_image()
                                img_path = (
                                    save_path
                                    + "\\"
                                    + mlcm.MLFilterEnum_to_str(nd)
                                    + "_"
                                    + mlcm.MLFilterEnum_to_str(xyz)
                                    + "_"
                                    + str(et)
                                    + ".tif"
                                )

                                cv2.imwrite(img_path, get_image)

                        print("capture image for: " + mlcm.MLFilterEnum_to_str(xyz))
                    print("capture image for: " + mlcm.MLFilterEnum_to_str(nd))
                print("capture image for: " + mlcm.pyRXCombination_to_str(rx))


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

        capture_linear_images()
    except Exception as e:
        print(e)

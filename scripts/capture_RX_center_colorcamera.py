import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def capture_RX_center(
    colorimter: mlcm.ML_Colorimeter,
    save_path: str,
    nd_list: List[mlcm.MLFilterEnum],
    xyz_list: List[mlcm.MLFilterEnum],
    cyl_list: List,
    axis_list: List,
    roi: mlcm.pyCVRect,
    exposure_map_obj: Dict[mlcm.MLFilterEnum, Dict[mlcm.MLFilterEnum, mlcm.pyExposureSetting]],
):
    mono = colorimter.ml_bino_manage.ml_get_module_by_id(1)
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
            if not os.path.exists(out_path):
                os.makedirs(out_path)

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
                    X, Y, Z = cv2.split(get_image)
                    img_path = (
                        out_path + "\\" +
                        mlcm.pyRXCombination_to_str(rx) + ".tif"
                    )
                    roi_img = Y[roi.y:roi.y +
                                roi.height, roi.x:roi.x+roi.width]
                    cv2.imwrite(img_path, roi_img)
                    print("capture image for: " +
                          mlcm.pyRXCombination_to_str(rx))
            print("capture image for: " + mlcm.MLFilterEnum_to_str(xyz))
        print("capture image for: " + mlcm.MLFilterEnum_to_str(nd))
    print("capture RX center finish")


if __name__ == "__main__":
    eye1_path = r"I:\duling ffc\EYE1"
    path_list = [
        eye1_path,
    ]
    save_path = r"D:\aolanduo2_RX_center"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
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

        # nd filter to switch during capture
        nd_list = [mlcm.MLFilterEnum.ND0]
        # xyz filter list to switch during capture
        xyz_list = [mlcm.MLFilterEnum.Y]

        cyl_list = [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0]
        axis_list = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165]

        roi = mlcm.pyCVRect(0, 0, 300, 300)

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

        capture_RX_center(
            ml_colorimeter,
            save_path,
            nd_list,
            xyz_list,
            cyl_list,
            axis_list,
            roi,
            exposure_map_obj
        )

    except Exception as e:
        print(e)

import mlcolorimeter as mlcm
import cv2
from typing import List, Dict
import os
import time

"""
    center_fit.py is an example script that shows a simplified way to fit rx cross center with circle.
"""


def polynomial_fit_online(
        colorimeter: mlcm.ML_Colorimeter,
        nd_list: List[mlcm.MLFilterEnum],
        xyz_list: List[mlcm.MLFilterEnum],
        binn: mlcm.Binning,
        pixel_format: mlcm.MLPixelFormat,
        cyl_list: List[float],
        axis_list: List[int],
        fit_file_path: str,
        out_path: str,
        roi: mlcm.pyCVRect,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    # test
    # update_status("polynomial_fit_online start")
    # time.sleep(5)
    # update_status("polynomial_fit_online finish")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    ret = ml_mono.ml_set_binning(binn)
    if not ret.success:
        raise RuntimeError("ml_set_binning error")

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
            for cyl in cyl_list:
                for axis in axis_list:
                    rx = mlcm.pyRXCombination(sph=0, cyl=cyl, axis=axis)
                    ret = ml_mono.ml_set_rx_syn(rx)
                    if not ret.success:
                        raise RuntimeError("ml_set_rx_syn error")

                    ret = ml_mono.ml_capture_image_syn()
                    if not ret.success:
                        raise RuntimeError("ml_capture_image_syn error")
                    get_image = ml_mono.ml_get_image()
                    # create polynomial fit instance
                    ml_center_fit = mlcm.pyMLCenterFit(mlcm.MLCenterFit())

                    # load polynomial fit config
                    ml_center_fit.ml_load_polynomialFit_config(fit_file_path)

                    # excute polynomial fit, after finish, return the fitted image
                    fitted_img = ml_center_fit.ml_polynomial_fit(
                        get_image, rx, xyz, binn
                    )

                    roi_img = fitted_img[roi.y:roi.y +
                                         roi.height, roi.x:roi.x+roi.width]

                    cv2.imwrite(
                        out_path + "\\" +
                        mlcm.pyRXCombination_to_str(rx) + ".tif",
                        roi_img,
                    )
                    update_status(
                        f"polynomial fit for: {mlcm.pyRXCombination_to_str(rx)}")
            update_status(
                f"polynomial fit for: {mlcm.MLFilterEnum_to_str(xyz)}")
        update_status(f"polynomial fit for: {mlcm.MLFilterEnum_to_str(nd)}")
    update_status("polynomial fit finish online")

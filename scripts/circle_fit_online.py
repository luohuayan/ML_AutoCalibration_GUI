import mlcolorimeter as mlcm
import cv2
from typing import List, Dict
import os
import time

"""
    center_fit.py is an example script that shows a simplified way to fit rx cross center with circle.
"""


def circle_fit_online(
        colorimeter:mlcm.ML_Colorimeter,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        cyl_list:List[float],
        axis_list:List[int],
        roi:mlcm.pyCVRect,
        fit_file_path:str,
        out_path:str,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    #test
    # update_status("circle_fit_online start")
    # time.sleep(5)
    # update_status("circle_fit_online finish")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    ret = ml_mono.ml_set_binning(binn)
    if not ret.success:
        raise RuntimeError("ml_set_binning error")

    # pixel_format = mlcm.MLPixelFormat.MLMono12
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

                    ml_mono.ml_capture_image_syn()
                    img = ml_mono.ml_get_image()[module_id]

                    # excute circle fit
                    # create circle fit instance
                    ml_center_fit = mlcm.pyMLCenterFit(mlcm.MLCenterFit())

                    # load circle fit config
                    ml_center_fit.ml_load_circleFit_config(fit_file_path)

                    # excute circle fit, after finish, return the fitted image
                    fitted_img = ml_center_fit.ml_circle_fit(img, rx, xyz, binn)

                    roi_img = fitted_img[roi.y:roi.y+roi.height, roi.x:roi.x+roi.width]

                    cv2.imwrite(
                        out_path + "\\" + mlcm.pyRXCombination_to_str(rx) + ".tif",
                        roi_img,
                    )
                    update_status(f"center fit for: {mlcm.pyRXCombination_to_str(rx)}")
            update_status(f"center fit for: {mlcm.MLFilterEnum_to_str(xyz)}")
        update_status(f"center fit for: {mlcm.MLFilterEnum_to_str(nd)}")
    update_status("circle fit finish online")


# if __name__ == "__main__":
#     # circle fit config
#     circle_fit_file = r"D:\projectFile01\aolanduo\aolanduo3_RX_center\CircleFit.json"
#     # path to save image after center fit
#     out_path = r"D:\projectFile01\aolanduo\aolanduo3_RX_center\ND0_X_fitted"
#     if not os.path.exists(out_path):
#         os.makedirs(out_path)

#     eye1_path = r"I:\duling ffc\EYE1"
#     path_list = [
#         eye1_path,
#     ]
#     try:
#         # create a ML_Colorimeter system instance
#         ml_colorimeter = mlcm.ML_Colorimeter()
#         # add mono module into ml_colorimeter system, according to path_list create one or more mono module
#         ret = ml_colorimeter.ml_add_module(path_list=path_list)
#         if not ret.success:
#             raise RuntimeError("ml_add_module error")
#         # connect all module in the ml_colorimeter system
#         ret = ml_colorimeter.ml_connect()
#         if not ret.success:
#             raise RuntimeError("ml_connect error")

#         module_id = 1
#         ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)

#         circle_fit_online()

#     except Exception as e:
#         print(e)

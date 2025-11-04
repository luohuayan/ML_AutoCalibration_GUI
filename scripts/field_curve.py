import mlcolorimeter as mlcm
import os
from typing import List
import time

"""
    field_curve.py is an example script that shows a simplified way to do vid scan, then get field curve
"""


def field_curve(
        colorimeter:mlcm.ML_Colorimeter,
        exposure_mode:mlcm.ExposureMode,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        exposure_time:float,
        out_path:str,
        focus_config:mlcm.pyThroughFocusConfig=None,
        freq_list:List[float]=[6.75,13.5],
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    # test
    # update_status("field_curve start")
    # time.sleep(5)
    # update_status("field_curve finish")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    # exposure time for fixed exposure, initial time for auto exposure
    exposure = mlcm.pyExposureSetting(exposure_mode, exposure_time)

    ret = ml_mono.ml_set_binning_selector(binn_selector)
    if not ret.success:
        raise RuntimeError("ml_set_binning_selector error")

    ret = ml_mono.ml_set_binning(binn)
    if not ret.success:
        raise RuntimeError("ml_set_binning error")

    # Set binning mode for camera.
    ret = ml_mono.ml_set_binning_mode(binn_mode)
    if not ret.success:
        raise RuntimeError("ml_set_binning_mode error")

    # Format of the pixel to use for acquisition.
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    # Set exposure for camera, contain auto and fixed.
    ret = ml_mono.ml_set_exposure(exposure)
    if not ret.success:
        raise RuntimeError("ml_set_exposure error")

    for freq in freq_list:
        file_path = out_path + "\\through_focus\\coarse_result.csv"
        new_path = out_path + f"\\through_focus\\coarse_result_{str(freq)}.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(new_path):
            os.remove(new_path)
        focus_config.freq = freq
        motion_name = "CameraMotion"

        ret = ml_mono.ml_vid_scan(motion_name=motion_name, focus_config=focus_config)
        if not ret.success:
            raise RuntimeError("ml_vid_scan error")

        ret = ml_mono.ml_save_vid_scan_result(out_path)
        if not ret.success:
            raise RuntimeError("ml_save_vid_scan_result error")
        os.rename(file_path, new_path)
        update_status(f"vid scan finish for freq: {str(freq)} ")


if __name__ == "__main__":
    # set mono module calibration configuration path
    eye1_path = r"D:\ml_software\EYE1"
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

        roi_list = [
            mlcm.pyCVRect(6369, 	4054 , 250, 250),
            mlcm.pyCVRect(6377, 	4407 , 250, 250),
            mlcm.pyCVRect(6174, 	4225 , 250, 250),
            mlcm.pyCVRect(6564, 	4208 , 250, 250),
            mlcm.pyCVRect(12160, 1211, 250, 250),
            mlcm.pyCVRect(11733, 762, 250, 250),
            mlcm.pyCVRect(757, 4042, 250, 250),
            mlcm.pyCVRect(1199, 4446, 250, 250),
            mlcm.pyCVRect(6419, 4068, 250, 250),
            mlcm.pyCVRect(6844, 4548, 250, 250),
            mlcm.pyCVRect(12173, 4057, 250, 250),
            mlcm.pyCVRect(11738, 4568, 250, 250),
            mlcm.pyCVRect(819, 8065, 250, 250),
            mlcm.pyCVRect(1313, 8614, 250, 250),
            mlcm.pyCVRect(6448, 8342, 250, 250),
            mlcm.pyCVRect(5956, 8802, 250, 250),
            mlcm.pyCVRect(12192, 8229, 250, 250),
            mlcm.pyCVRect(11748, 8741, 250, 250),
        ]
        out_path = r"D:\ml_software"
        field_curve()
    except Exception as e:
        # print(e)
        pass

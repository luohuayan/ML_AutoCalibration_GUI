import mlcolorimeter as mlcm
from typing import List, Dict
import time

"""
    fourcolor_calibration.py is an example script that shows a simplified way to do fourcolor calibration.
        The fourcolor calibration process consists of two parts, one is fourcolor calibration capture, 
        and the other part is fourcolor calibration calculate.
"""


# def fourcolor_calibration_capture(
#     module_id: int,
#     save_path: str,
#     light_source: str,
#     nd: mlcm.MLFilterEnum,
#     rx: mlcm.pyRXCombination = mlcm.pyRXCombination(),
#     avg_count: int = 5,
#     exposure_map: Dict[mlcm.MLFilterEnum, mlcm.pyExposureSetting] = {
#         mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(),
#         mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(),
#         mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(),
#     },
#     roi: mlcm.pyCVRect = mlcm.pyCVRect(),
#     is_do_ffc: bool = False,
# ):
#     # capture M images and calculate M matrix
#     ret = ml_colorimeter.ml_capture_and_calMMatrix2(
#         module_id=module_id,
#         save_path=save_path,
#         light_source=light_source,
#         nd=nd,
#         rx=rx,
#         avg_count=avg_count,
#         exposure_map=exposure_map,
#         roi=roi,
#         is_do_ffc=is_do_ffc,
#     )
#     if not ret.success:
#         raise RuntimeError("ml_capture_and_calMMatrix2 error")

def fourcolor_calibration_capture(
        colorimeter:mlcm.ML_Colorimeter,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        save_path: str,
        light_source: str,
        nd: mlcm.MLFilterEnum,
        avg_count: int = 5,
        exposure_map: Dict[mlcm.MLFilterEnum, mlcm.pyExposureSetting] ={},
        roi: mlcm.pyCVRect = mlcm.pyCVRect(),
        is_do_ffc: bool = False,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    update_status("fourcolor_calibration_capture start")
    # time.sleep(10)
    # update_status("fourcolor_calibration_capture finish")

    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    # set pixel format to MLMono12 during capture
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")
    ret = ml_mono.ml_set_binning_selector(binn_selector)
    if not ret.success:
        raise RuntimeError("ml_set_binning_selector error")

    # Set binning mode for camera.
    ret = ml_mono.ml_set_binning_mode(binn_mode)
    if not ret.success:
        raise RuntimeError("ml_set_binning_mode error")
    
    ret = ml_mono.ml_set_binning(binn)
    if not ret.success:
        raise RuntimeError("ml_set_binning error")
    
    rx = mlcm.pyRXCombination(0, 0, 0)
    ret = ml_mono.ml_set_rx_syn(rx=rx)
    if not ret.success:
        raise RuntimeError("ml_set_rx_syn error")
    # capture M images and calculate M matrix
    ret = colorimeter.ml_capture_and_calMMatrix2(
        module_id=module_id,
        save_path=save_path,
        light_source=light_source,
        nd=nd,
        rx=rx,
        avg_count=avg_count,
        exposure_map=exposure_map,
        roi=roi,
        is_do_ffc=is_do_ffc,
    )
    if not ret.success:
        update_status("ml_capture_and_calMMatrix2 error")
        raise RuntimeError("ml_capture_and_calMMatrix2 error")


def fourcolor_calibration_calculate(
    colorimeter:mlcm.ML_Colorimeter,
    save_path: str,
    nd: mlcm.MLFilterEnum,
    NMatrix_path: str,
    status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    update_status("fourcolor_calibration_calculate start")
    # time.sleep(10)
    # update_status("fourcolor_calibration_calculate finish")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    aperture = ml_mono.ml_get_aperture()
    rx = mlcm.pyRXCombination(0, 0, 0)
    ret = ml_mono.ml_set_rx_syn(rx=rx)
    if not ret.success:
        raise RuntimeError("ml_set_rx_syn error")
# save M matrix images and exposure time
    ret = colorimeter.ml_save_MMatrix_and_exposure(
        module_id=module_id, save_path=save_path, aperture=aperture, nd=nd, rx=rx
    )
    if not ret.success:
        raise RuntimeError("ml_save_MMatrix_and_exposure error")

    # get M matrix by module id
    mmatrix = colorimeter.ml_get_MMatrix(module_id) # type: ignore

    # calculate N matrix using the input NMatrix_xyL.json
    ret = colorimeter.ml_cal_NMatrix(NMatrix_path)
    if not ret.success:
        raise RuntimeError("ml_cal_NMatrix error")
    nmatrix = colorimeter.ml_get_NMatrix() # type: ignore

    # calculate R matrix using the M matrix and N matrix, and save R matrix to config
    ret = colorimeter.ml_cal_RMatrix(module_id=module_id, nd=nd)
    if not ret.success:
        raise RuntimeError("ml_cal_RMatrix error")
    rmatrix = colorimeter.ml_get_RMatrix(module_id) # type: ignore

# if __name__ == "__main__":
#     # set mono module calibration configuration path
#     eye1_path = r"D:\config\EYE1"
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

#         # N matrix path, NMatrix_xyL.json contains the specbos data of your light source
#         NMatrix_path = r"D:\config\NMatrix_xyL.json"
#         # path to save M images and exposure time
#         save_path = r"D:\intermediate_data"

#         # nd filter list to switch during capture
#         nd_list = [mlcm.MLFilterEnum.ND0]
#         # exposure map of color filter during capture
#         exposure_map = {
#             mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(
#                 exposure_mode=mlcm.ExposureMode.Auto, exposure_time=1000
#             ),
#             mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(
#                 exposure_mode=mlcm.ExposureMode.Auto, exposure_time=1000
#             ),
#             mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(
#                 exposure_mode=mlcm.ExposureMode.Auto, exposure_time=1000
#             ),
#         }
#         rx = mlcm.pyRXCombination(0, 0, 0)
#         ret = ml_mono.ml_set_rx_syn(rx=rx)
#         if not ret.success:
#             raise RuntimeError("ml_set_rx_syn error")

#         # count to calculate average image for one color filter
#         avg_count = 5
#         # ROI setting to calculate M matrix
#         roi = mlcm.pyCVRect(x=2000, y=2000, width=1000, height=1000)
#         # whether to do flat field correction before calculation
#         is_do_ffc = True
#         # light source list for fourcolor calibration
#         light_source_list = ["R", "G", "B", "W"]

#         # set pixel format to MLMono12 during capture
#         ret = ml_mono.ml_set_pixel_format(pixel_format=mlcm.MLPixelFormat.MLMono12)
#         if not ret.success:
#             raise RuntimeError("ml_set_pixel_format error")

#         # capture M matrix image for nd list
#         for nd in nd_list:
#             # need to manually switch the light source of IS, or add your code to control the IS
#             for light_source in light_source_list:
#                 # execute fourcolor calibration capture
#                 fourcolor_calibration_capture(
#                     module_id=module_id,
#                     save_path=save_path,
#                     light_source=light_source,
#                     nd=nd,
#                     rx=rx,
#                     avg_count=avg_count,
#                     exposure_map=exposure_map,
#                     roi=roi,
#                     is_do_ffc=is_do_ffc,
#                 )
#             print(
#                 "capture fourcolor calibration images for "
#                 + mlcm.MLFilterEnum_to_str(nd)
#             )

#             # calculate M, N, R matrix after capturing M matrix
#             fourcolor_calibration_calculate(
#                 module_id=module_id,
#                 save_path=save_path,
#                 nd=nd,
#                 rx=rx,
#                 NMatrix_path=NMatrix_path,
#             )
#             print("calculate R matrix for " + mlcm.MLFilterEnum_to_str(nd))

#     except Exception as e:
#         print(e)

import mlcolorimeter as mlcm
import os
import shutil
import time
from typing import List

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
        focus_config:mlcm.pyFocusScanConfig_=None,
        freq_list:List[float]=[6.75,13.5],
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    ret=mlcm.pyMLFocusScan.ml_set_monomanage_focus(ml_mono)
    if not ret.success:
        raise RuntimeError("ml_set_monomanage_focus error")
    
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
        file_path = out_path + "\\focus_scan\\coarse_result.csv"
        new_path = out_path + f"\\focus_scan\\coarse_result_{str(freq)}.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(new_path):
            os.remove(new_path)
        image_path = out_path + "\\focus_scan\\coarse_images"
        new_image_path = out_path + f"\\focus_scan\\coarse_images_{str(freq)}"
        if os.path.exists(image_path):
            shutil.rmtree(image_path)
        if not os.path.exists(new_image_path):
            os.makedirs(new_image_path)
        motion_name = "CameraMotion"
        focus_config.freq=freq

        status=mlcm.pyMLFocusScan.ml_start_focusscan()

        if not status:
            raise RuntimeError("ml_start_focusscan error")

        ret = mlcm.pyMLFocusScan.ml_focusscan_async(motion_name=motion_name,config=focus_config)
        if not ret.success:
            raise RuntimeError("ml_focusscan_async error")
        
        ret =mlcm.pyMLFocusScan.ml_wait_focusscan_finish()

        if ret.success:
            res = mlcm.pyMLFocusScan.ml_get_focusscan_result()
            mlcm.pyMLFocusScan.ml_calculate_combin_map("H",{0,1})
            mlcm.pyMLFocusScan.ml_calculate_combin_map("V",{2,3})
            mlcm.pyMLFocusScan.ml_calculate_combin_map("AVG",{0,1,2,3})
            mlcm.pyMLFocusScan.ml_get_combin_result()
            ret = mlcm.pyMLFocusScan.ml_save_focusscan_result(focus_config.image_save_path,"")
            if not ret.success:
                raise RuntimeError("ml_save_focusscan_result error")
            if(focus_config.save_result_img):
                mlcm.pyMLFocusScan.ml_wait_for_tasks_finish()
        else:
            raise RuntimeError("ml_wait_focusscan_finish error")
        
        
        
        # ret = ml_mono.ml_vid_scan(motion_name=motion_name, focus_config=focus_config)
        # if not ret.success:
        #     raise RuntimeError("ml_vid_scan error")

        # ret = ml_mono.ml_save_vid_scan_result(out_path, True, "")
        # if not ret.success:
        #     raise RuntimeError("ml_save_vid_scan_result error")
        os.rename(file_path, new_path)
        update_status(f"vid scan finish for freq {str(freq)}")

        for filename in os.listdir(image_path):
            src_path = os.path.join(image_path, filename)
            
            # 只拷贝文件，不拷贝子文件夹
            if os.path.isfile(src_path):
                dst_path = os.path.join(new_image_path, filename)
                shutil.copy2(src_path, dst_path)
                update_status(f"已拷贝: {filename}")


# if __name__ == "__main__":
#     # set mono module calibration configuration path
#     eye1_path = r"D:\config\weilaixing\EYE1"
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

#         roi_list = [
#             mlcm.pyCVRect(5500, 4800, 600, 600),
#         ]
#         out_path = r"D:\output"
#         field_curve()
#     except Exception as e:
#         print(e)

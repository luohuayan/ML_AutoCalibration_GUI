import mlcolorimeter as mlcm
import os
import shutil

"""
    field_curve.py is an example script that shows a simplified way to do vid scan, then get field curve
"""


def field_curve():
    # exposure mode setting, Auto or Fixed
    exposure_mode = mlcm.ExposureMode.Auto
    # exposure time for fixed exposure, initial time for auto exposure
    exposure_time = 100
    exposure = mlcm.pyExposureSetting(exposure_mode, exposure_time)
    # camera binning selector
    binn_selector = mlcm.BinningSelector.Logic
    # camera binning
    binn = mlcm.Binning.ONE_BY_ONE
    # camera binning mode
    binn_mode = mlcm.BinningMode.AVERAGE
    # camera pixel format
    pixel_format = mlcm.MLPixelFormat.MLMono12

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

    for freq in [6.75, 13.75]:
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

        focus_config = mlcm.pyThroughFocusConfig(
            focus_max=13,
            focus_min=12,
            inf_position=14.48,
            focal_length=50,
            pixel_size=0.00345,
            focal_space=0,
            freq=freq,
            rois=roi_list,
            use_chess_mode=True,
            use_lpmm_unit=False,
            rough_step=0.02,
            use_fine_adjust=False,
            fine_step=0.01,
            average_count=3,
            store_image=True
        )
        motion_name = "CameraMotion"

        ret = ml_mono.ml_vid_scan(motion_name=motion_name, focus_config=focus_config)
        if not ret.success:
            raise RuntimeError("ml_vid_scan error")

        ret = ml_mono.ml_save_vid_scan_result(out_path, True, "")
        if not ret.success:
            raise RuntimeError("ml_save_vid_scan_result error")
        os.rename(file_path, new_path)
        print("vid scan finish for freq " + str(freq))

        for filename in os.listdir(image_path):
            src_path = os.path.join(image_path, filename)
            
            # 只拷贝文件，不拷贝子文件夹
            if os.path.isfile(src_path):
                dst_path = os.path.join(new_image_path, filename)
                shutil.copy2(src_path, dst_path)
                print(f"已拷贝: {filename}")


if __name__ == "__main__":
    # set mono module calibration configuration path
    eye1_path = r"D:\config\weilaixing\EYE1"
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
            mlcm.pyCVRect(5500, 4800, 600, 600),
        ]
        out_path = r"D:\output"
        field_curve()
    except Exception as e:
        print(e)

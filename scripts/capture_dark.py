import mlcolorimeter as mlcm
import os
import cv2


def capture_dark():
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
    get_binn_selector = ml_mono.ml_get_binning_selector()
    print(get_binn_selector)

    ret = ml_mono.ml_set_binning(binn)
    if not ret.success:
        raise RuntimeError("ml_set_binning error")
    get_binn = ml_mono.ml_get_binning()
    print(get_binn)

    # Set binning mode for camera.
    ret = ml_mono.ml_set_binning_mode(binn_mode)
    if not ret.success:
        raise RuntimeError("ml_set_binning_mode error")
    get_binn_mode = ml_mono.ml_get_binning_mode()
    print(get_binn_mode)

    # Format of the pixel to use for acquisition.
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")
    get_pixel_format = ml_mono.ml_get_pixel_format()
    print(get_pixel_format)

    for i in range(1, 51):
        exposure = mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=i*1000)

        # Set exposure for camera, contain auto and fixed.
        ret = ml_mono.ml_set_exposure(exposure)
        if not ret.success:
            raise RuntimeError("ml_set_exposure error")

        # capture a single image
        ret = ml_mono.ml_capture_image_syn()
        if not ret.success:
            raise RuntimeError("ml_capture_image_syn error")
        get_img = ml_mono.ml_get_image()
        cv2.imwrite(save_path+"\\" + str(i) +"s.tif", get_img)


if __name__ == "__main__":
    # set mono module calibration configuration path
    eye1_path = r"D:\MLColorimeter\config\EYE1"
    save_path = r""
    if not os.path.exists(save_path):
        os.makedirs(save_path)

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

        capture_dark()
    except Exception as e:
        print(e)

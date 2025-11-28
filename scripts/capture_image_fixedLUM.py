import mlcolorimeter as mlcm
from typing import List, Dict
import numpy as np
import cv2
import os
import time

def capture_image_fixedLUM(
        colorimeter:mlcm.ML_Colorimeter,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        save_path:str,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        ET_list:List[float],
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    #test
    update_status("capture_image_fixedLUM start")
    time.sleep(10)
    update_status("capture_image_fixedLUM finish")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    for nd in nd_list:
        nd_enum = mlcm.MLFilterEnum(nd)
        ret = ml_mono.ml_move_nd_syn(nd_enum)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")

        for xyz in xyz_list:
            xyz_enum = mlcm.MLFilterEnum(xyz)
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

            for ET in ET_list:
                exposure=mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=ET)
                ret = ml_mono.ml_set_exposure(exposure)
                if not ret.success:
                    raise RuntimeError("ml_set_exposure error")
                # capture single image from camera
                ml_mono.ml_capture_image_syn()
                img = ml_mono.ml_get_image()
                img_name = f"ET_{ET}ms.tiff"
                img_path = os.path.join(out_path, img_name)
                cv2.imwrite(img_path, img)
                update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{mlcm.MLFilterEnum_to_str(xyz_enum)}_{str(ET)} save success")
            
    update_status("finish!")

def capture_image_ficedLUM_afterFFC(
        colorimeter:mlcm.ML_Colorimeter,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        sph_list:List[float],
        cyl_list:List[float],
        axis_list:List[int],
        save_path:str,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        ET_list:List[float],
        use_rx:bool,
        cali_config: mlcm.pyCalibrationConfig=mlcm.pyCalibrationConfig(),
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    #test
    # update_status("capture_image_ficedLUM_afterFFC start")
    # time.sleep(10)
    # update_status("capture_image_ficedLUM_afterFFC finish")
    module_id=1
    ml_mono=colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
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
    
    # set pixel format to MLMono12 for capture
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")
    
    cali_config.light_source_list=[ml_mono.ml_get_light_source()]
    cali_config.aperture=ml_mono.ml_get_aperture()
    cali_config.nd_filter_list=[mlcm.MLFilterEnum(nd) for nd in nd_list]
    cali_config.color_filter_list=[mlcm.MLFilterEnum(xyz) for xyz in xyz_list]
    cali_config.binn=mlcm.Binning.ONE_BY_ONE

    if not use_rx:
        rx=mlcm.pyRXCombination(0,0,0)
        ret=ml_mono.ml_set_rx_syn(rx)
        if not ret.success:
            raise RuntimeError("ml_set_rx_syn error")
        cali_config.rx=rx
        for nd in nd_list:
            nd_enum = mlcm.MLFilterEnum(nd)
            ret = ml_mono.ml_move_nd_syn(nd_enum)
            if not ret.success:
                raise RuntimeError("ml_move_nd_syn error")
            for et in ET_list:
                capture_data_dict=dict()
                for xyz in xyz_list:
                    xyz_enum = mlcm.MLFilterEnum(int(xyz))
                    ret = ml_mono.ml_move_xyz_syn(xyz_enum)
                    if not ret.success:
                        raise RuntimeError("ml_move_xyz_syn error")
                    exposure=mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=et)
                    ret = ml_mono.ml_set_exposure(exposure)
                    if not ret.success:
                        raise RuntimeError("ml_set_exposure error")
                    ret=ml_mono.ml_capture_image_syn()
                    if not ret.success:
                        raise RuntimeError("ml_capture_image_syn error")
                    capture_data=ml_mono.ml_get_CaptureData()
                    capture_data_dict[xyz_enum]=capture_data
                
                ret=colorimeter.ml_set_CaptureData(module_id,data=capture_data_dict)
                if not ret.success:
                    raise RuntimeError("ml_set_CaptureData error")
                
                # load calibration data by calbration config
                ret = colorimeter.ml_load_calibration_data(cali_config=cali_config)
                if not ret.success:
                    raise RuntimeError("ml_load_calibration_data error")
                
                # execute calibration process for capture data by calibration config
                ret = colorimeter.ml_image_process(cali_config)
                if not ret.success:
                    raise RuntimeError("ml_image_process error")
                # get calibration data after calibration process
                processed_data=colorimeter.ml_get_processed_data(module_id)
                for xyz in xyz_list:
                    img_ffc=processed_data[mlcm.CalibrationEnum.FFC][mlcm.MLFilterEnum(int(xyz))].image
                    img_raw=processed_data[mlcm.CalibrationEnum.Raw][mlcm.MLFilterEnum(int(xyz))].image
                    img_name_ffc=f"FFC_{mlcm.MLFilterEnum_to_str(nd_enum)}_{mlcm.MLFilterEnum_to_str(xyz_enum)}_{et}ms.tiff"
                    img_name_raw=f"Raw_{mlcm.MLFilterEnum_to_str(nd_enum)}_{mlcm.MLFilterEnum_to_str(xyz_enum)}_{et}ms.tiff"
                    img_path_raw=os.path.join(save_path,img_name_raw)
                    cv2.imwrite(img_path_raw,img_raw)
                    img_path_ffc=os.path.join(save_path,img_name_ffc)
                    cv2.imwrite(img_path_ffc,img_ffc)
                update_status(f"ET_{str(et)}_{mlcm.pyRXCombination_to_str(rx)} ffc and raw image save success")
            update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)} capture finish")
    else:
        for nd in nd_list:
            nd_enum = mlcm.MLFilterEnum(nd)
            ret = ml_mono.ml_move_nd_syn(nd_enum)
            if not ret.success:
                raise RuntimeError("ml_move_nd_syn error")
            for et in ET_list:
                for sph in sph_list:
                    for cyl in cyl_list:
                        for axis in axis_list:
                            capture_data_dict=dict()
                            rx=mlcm.pyRXCombination(sph,cyl,axis)
                            ret=ml_mono.ml_set_rx_syn(rx)
                            if not ret.success:
                                raise RuntimeError("ml_set_rx_syn error")
                            cali_config.rx=rx
                            for xyz in xyz_list:
                                xyz_enum = mlcm.MLFilterEnum(int(xyz))
                                ret = ml_mono.ml_move_xyz_syn(xyz_enum)
                                if not ret.success:
                                    raise RuntimeError("ml_move_xyz_syn error")
                                exposure=mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=et)
                                ret = ml_mono.ml_set_exposure(exposure)
                                if not ret.success:
                                    raise RuntimeError("ml_set_exposure error")
                                ret=ml_mono.ml_capture_image_syn()
                                if not ret.success:
                                    raise RuntimeError("ml_capture_image_syn error")
                                capture_data=ml_mono.ml_get_CaptureData()
                                capture_data_dict[xyz_enum]=capture_data
                            
                            ret=colorimeter.ml_set_CaptureData(module_id,data=capture_data_dict)
                            if not ret.success:
                                raise RuntimeError("ml_set_CaptureData error")
                            
                            # load calibration data by calbration config
                            ret = colorimeter.ml_load_calibration_data(cali_config=cali_config)
                            if not ret.success:
                                raise RuntimeError("ml_load_calibration_data error")
                            
                            # execute calibration process for capture data by calibration config
                            ret = colorimeter.ml_image_process(cali_config)
                            if not ret.success:
                                raise RuntimeError("ml_image_process error")
                            # get calibration data after calibration process
                            processed_data=colorimeter.ml_get_processed_data(module_id)
                            for xyz in xyz_list:
                                img_ffc=processed_data[mlcm.CalibrationEnum.FFC][mlcm.MLFilterEnum(int(xyz))].image
                                img_raw=processed_data[mlcm.CalibrationEnum.Raw][mlcm.MLFilterEnum(int(xyz))].image
                                img_name_ffc=f"FFC_{str(sph)}d_{str(cyl)}d_{str(axis)}deg_{mlcm.MLFilterEnum_to_str(nd_enum)}_{mlcm.MLFilterEnum_to_str(xyz_enum)}_{et}ms.tiff"
                                img_name_raw=f"Raw_{str(sph)}d_{str(cyl)}d_{str(axis)}deg_{mlcm.MLFilterEnum_to_str(nd_enum)}_{mlcm.MLFilterEnum_to_str(xyz_enum)}_{et}ms.tiff"
                                img_path_raw=os.path.join(save_path,img_name_raw)
                                cv2.imwrite(img_path_raw,img_raw)
                                img_path_ffc=os.path.join(save_path,img_name_ffc)
                                cv2.imwrite(img_path_ffc,img_ffc)
                            update_status(f"ET_{str(et)}_{mlcm.pyRXCombination_to_str(rx)} ffc and raw image save success")
            update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)} capture finish")
    
    update_status("finish!")

if __name__ == "__main__":
    pass

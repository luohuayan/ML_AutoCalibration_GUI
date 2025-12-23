import mlcolorimeter as mlcm
import cv2
import os
import json
import logging
import numpy as np
import tkinter as tk
from tkinter import messagebox
import pandas as pd
from datetime import datetime
from typing import List,Dict
import time


# 创建文件夹
def create_directory(path):
    os.makedirs(path, exist_ok=True)

# 保存json数据到文件
def save_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def process_image(img,img_x=6688,img_y=4764,roi_width=250,roi_height=250):
    roi_center_x= int(roi_width /2 )
    roi_center_y= int(roi_height /2 )
    roi_list = []
    for x, y in [(img_x, img_y)]:
        y1,y2 = int(y -roi_center_y), int(y +roi_center_y)
        x1, x2 = int(x -roi_center_x), int(x + roi_center_x)
        roi = img[y1: y2, x1: x2]
        grays = cv2.mean(roi)[0]
        roi_list.append(grays)
    return np.mean(roi_list)

def save_results_to_excel(results,out_path):
    results_df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_excel_path="monocalibration_results" + "_" + timestamp + ".xlsx"
    os.makedirs(out_path, exist_ok=True)
    result_file = os.path.join(out_path, output_excel_path)
    
    results_df.to_excel(result_file, index=False)
    logging.info(f"Calibration results saved to {result_file}")


def mono_calibration(
        colorimeter:mlcm.ML_Colorimeter,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        gray_range:List[float],
        apturate:str,
        light_source:str,
        luminance_values:Dict[mlcm.MLFilterEnum, float],
        luminance_no_xyz:float,
        radiance:float,
        eye1_path:str,
        out_path:str,
        image_point:List[int],
        roi_size:List[int],
        expusure_offset:float=0,
        gray_offset:float=0,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    
    if len(image_point) >=2:
        image_x=int(image_point[0])
        image_y=int(image_point[1])
    if len(roi_size) >=2:
        roi_width=int(roi_size[0])
        roi_height=int(roi_size[1])
    module_id = 1
    mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    # set light source
    mono.ml_set_light_source(light_source)
    
    ret = mono.ml_set_binning_selector(binn_selector)
    if not ret.success:
        raise RuntimeError("ml_set_binning_selector error")

    # Set binning mode for camera.
    ret = mono.ml_set_binning_mode(binn_mode)
    if not ret.success:
        raise RuntimeError("ml_set_binning_mode error")
    
    ret = mono.ml_set_binning(binn)
    if not ret.success:
        raise RuntimeError("ml_set_binning error")
    
    # Format of the pixel to use for acquisition.
    ret = mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    exposure = mlcm.pyExposureSetting(
            exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100
        )
    results = []
    if nd_list==[]:
        for gray in gray_range:
            aeparams = mlcm.pyAEParams(dynamic_range=gray,target_max=gray + 0.05,target_min=gray - 0.05, max_time=19000, rate=1000000)
            ret = mono.ml_update_AE_params(aeparams)
            if xyz_list == []:
                mono.ml_set_exposure(exposure=exposure)
                mono.ml_capture_image_syn()
                img = mono.ml_get_image()
                average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                average_gray+=gray_offset
                exposure_time = mono.ml_get_exposure_time() + expusure_offset
                update_status(f"{str(gray)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                luminance_k= luminance_no_xyz / gray_ET if gray_ET > 0 else 0
                radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                results.append({
                    "Gray Range": f"{gray * 100}" + "%",
                    "NDFilter": "None",
                    "AVEGray": average_gray,
                    "ExposureTime": exposure_time,
                    "G/ET": gray_ET,
                    "Luminance": luminance_no_xyz,
                    "K(L)":luminance_k,
                    "Radiance": radiance,
                    "K(R)": radiance_k
                })
            else:
                for xyz in xyz_list:
                    Luminance = luminance_values[xyz]
                    # move color filter
                    mono.ml_move_xyz_syn(xyz)
                    # set exposure by pyExposureSetting
                    mono.ml_set_exposure(exposure=exposure)
                    # capture single image from camera
                    mono.ml_capture_image_syn()
                    img = mono.ml_get_image()
                    # mono calibration
                    average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                    average_gray+=gray_offset
                    # get exposure time
                    exposure_time = mono.ml_get_exposure_time() + expusure_offset
                    update_status(f"{str(gray)}_{mlcm.MLFilterEnum_to_str(xyz)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                    gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                    luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                    radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                    # add result to the list
                    results.append({
                        "Gray Range": f"{gray * 100}" + "%",
                        "NDFilter": "None",
                        "XYZFilter": mlcm.MLFilterEnum_to_str(xyz),
                        "AVEGray": average_gray,
                        "ExposureTime": exposure_time,
                        "G/ET": gray_ET,
                        "Luminance": Luminance,
                        "K(L)":luminance_k,
                        "Radiance": radiance,
                        "K(R)": radiance_k
                    })

    else:
        for nd in nd_list:
            # switch nd filter
            nd_enum = mlcm.MLFilterEnum(int(nd)) # et MLFilterEnum.ND0
            mono.ml_move_nd_syn(nd_enum)
            for gray in gray_range:
                aeparams = mlcm.pyAEParams(dynamic_range=gray,target_max=gray + 0.05,target_min=gray - 0.05, max_time=19000, rate=1000000)
                ret = mono.ml_update_AE_params(aeparams)
                if xyz_list == []:
                    mono.ml_set_exposure(exposure=exposure)
                    mono.ml_capture_image_syn()
                    img = mono.ml_get_image()
                    average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                    average_gray+=gray_offset
                    exposure_time = mono.ml_get_exposure_time() + expusure_offset
                    update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{str(gray)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                    gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                    luminance_k= luminance_no_xyz / gray_ET if gray_ET > 0 else 0
                    radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                    results.append({
                        "Gray Range": f"{gray * 100}" + "%",
                        "NDFilter": mlcm.MLFilterEnum_to_str(nd_enum),
                        "AVEGray": average_gray,
                        "ExposureTime": exposure_time,
                        "G/ET": gray_ET,
                        "Luminance": luminance_no_xyz,
                        "K(L)":luminance_k,
                        "Radiance": radiance,
                        "K(R)": radiance_k
                    })
                else:
                    for xyz in xyz_list:
                        Luminance = luminance_values[xyz]
                        # move color filter
                        mono.ml_move_xyz_syn(xyz)
                        # set exposure by pyExposureSetting
                        mono.ml_set_exposure(exposure=exposure)
                        # capture single image from camera
                        mono.ml_capture_image_syn()
                        img = mono.ml_get_image()
                        # mono calibration
                        average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                        average_gray+=gray_offset
                        # get exposure time
                        exposure_time = mono.ml_get_exposure_time() + expusure_offset
                        update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{str(gray)}_{mlcm.MLFilterEnum_to_str(xyz)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                        gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                        luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                        radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                        # add result to the list
                        results.append({
                            "Gray Range": f"{gray * 100}" + "%",
                            "NDFilter": mlcm.MLFilterEnum_to_str(nd_enum),
                            "XYZFilter": mlcm.MLFilterEnum_to_str(xyz),
                            "AVEGray": average_gray,
                            "ExposureTime": exposure_time,
                            "G/ET": gray_ET,
                            "Luminance": Luminance,
                            "K(L)":luminance_k,
                            "Radiance": radiance,
                            "K(R)": radiance_k
                        })
        
    time.sleep(1)
    update_status("写入配置中...")
    
    # 将results中灰度值在80%的luminance_k和radiance_k写入配置文件，b为0
    for item in results:
        if item["Gray Range"] == "80.0%":
            if nd_list==[]:
                if xyz_list == []:
                    file_name="" + apturate + "_" + light_source
                else:
                    xyz_filter = item["XYZFilter"]
                    file_name="" + apturate + "_" + xyz_filter + "_" + light_source
            else:
                # 文件夹命名格式为Aperture_NDFilter_LightSource
                nd_filter = item["NDFilter"]
                if xyz_list == []:
                    file_name="" + apturate + "_" + nd_filter + "_" + light_source
                else:
                    xyz_filter = item["XYZFilter"]
                    file_name="" + apturate + "_" + nd_filter + "_" + xyz_filter + "_" + light_source
            luminance_k = item["K(L)"]
            radiance_k = item["K(R)"]
            luminance_config_path = os.path.join(eye1_path, "Luminance")
            create_directory(luminance_config_path)
            radiance_config_path = os.path.join(eye1_path, "Radiance")
            create_directory(radiance_config_path)

            luminance_file_path = os.path.join(luminance_config_path, file_name)
            os.makedirs(luminance_file_path, exist_ok=True)
            # 完整的文件路径
            luminance_json_file_path= os.path.join(luminance_file_path, "Luminance.json")
            # 创建要写入的字典
            data={
                "Luminance": [[float(luminance_k),0]]
            }
            save_json(data, luminance_json_file_path)

            radiance_file_path = os.path.join(radiance_config_path, file_name)
            os.makedirs(radiance_file_path, exist_ok=True)
            # 完整的文件路径
            radiance_json_file_path= os.path.join(radiance_file_path, "Radiance.json")
            # 创建要写入的字典
            data1={
                "Radiance": [[float(radiance_k),0]]
            }
            save_json(data1, radiance_json_file_path)
    time.sleep(1)
    update_status("写入完成，保存数据表")
    save_results_to_excel(results,out_path)


def mono_calibration_do_ffc(
        colorimeter:mlcm.ML_Colorimeter,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        gray_range:List[float],
        apturate:str,
        light_source:str,
        luminance_values:Dict[mlcm.MLFilterEnum, float],
        luminance_no_xyz:float,
        radiance:float,
        eye1_path:str,
        out_path:str,
        image_point:List[int],
        roi_size:List[int],
        is_rx:bool=False,
        sph_list:List[float]=[0.0],
        cyl_list:List[float]=[0.0],
        axis_list:List[int]=[0],
        expusure_offset:float=0,
        gray_offset:float=0,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    
    image_x,image_y=map(int,image_point[:2]) if len(image_point)>=2 else (0,0)
    roi_width,roi_height=map(int,roi_size[:2]) if len(roi_size)>=2 else (0,0)

    module_id = 1
    mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    # set light source
    mono.ml_set_light_source(light_source)
    configurations={
        "binn_selector":binn_selector,
        "binning_mode":binn_mode,
        "binning":binn,
        "pixel_format":pixel_format
    }
    for config_name,config_value in configurations.items():
        ret=getattr(mono,f'ml_set_{config_name}')(config_value)
        if not ret.success:
            raise RuntimeError(f"ml_set_{config_name} error")
    exposure = mlcm.pyExposureSetting(
            exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100
        )
    results = []
    capture_data_dict = dict()
    if is_rx:
        if nd_list==[]:
            for gray in gray_range:
                aeparams = mlcm.pyAEParams(dynamic_range=gray,target_max=gray + 0.05,target_min=gray - 0.05, max_time=19000, rate=1000000)
                ret = mono.ml_update_AE_params(aeparams)
                for sph in sph_list:
                    for cyl in cyl_list:
                        for axis in axis_list:
                            rx=mlcm.pyRXCombination(sph=sph,cyl=cyl,axis=axis)
                            ret=mono.ml_set_rx_syn(rx)
                            RX_str = mlcm.pyRXCombination_to_str(rx)
                            if not ret.success:
                                raise RuntimeError("ml_set_rx_syn error")
                            cali_config=mlcm.pyCalibrationConfig(
                                input_path=mono.ml_get_config_path(),
                                aperture=mono.ml_get_aperture(),
                                nd_filter_list=[mlcm.MLFilterEnum.ND0],
                                color_filter_list=xyz_list,
                                rx=rx,
                                light_source_list=[mono.ml_get_light_source()],
                                dark_flag=True,
                                ffc_flag=True,
                                color_shift_flag=False,
                                distortion_flag=False,
                                exposure_flag=False,
                                four_color_flag=False
                            )
                            if xyz_list == []:
                                cali_config.color_filter_list=[mlcm.MLFilterEnum.X]
                                mono.ml_set_exposure(exposure=exposure)
                                mono.ml_capture_image_syn()
                                capture_data = mono.ml_get_CaptureData()
                                # 这里给一个默认XYZ值
                                capture_data_dict[mlcm.MLFilterEnum.X] = capture_data
                                # set capture data for measurement
                                ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                                if not ret.success:
                                    raise RuntimeError("ml_set_CaptureData error")
                                # load calibration data by calbration config
                                ret = colorimeter.ml_load_calibration_data(cali_config)
                                if not ret.success:
                                    raise RuntimeError("ml_load_calibration_data error")

                                # execute calibration process for capture data by calibration config
                                ret = colorimeter.ml_image_process(cali_config)
                                if not ret.success:
                                    raise RuntimeError("ml_image_process error")

                                # get calibration data after calibration process
                                processed_data = colorimeter.ml_get_processed_data(module_id)

                                img = processed_data[mlcm.CalibrationEnum.FFC][mlcm.MLFilterEnum.X].image
                                    
                                average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                                average_gray+=gray_offset
                                exposure_time = mono.ml_get_exposure_time() + expusure_offset
                                update_status(f"{str(gray)}_{RX_str}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                                gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                                luminance_k= luminance_no_xyz / gray_ET if gray_ET > 0 else 0
                                radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                                results.append({
                                    "Gray Range": f"{gray * 100}" + "%",
                                    "NDFilter": "None",
                                    "AVEGray": average_gray,
                                    "ExposureTime": exposure_time,
                                    "G/ET": gray_ET,
                                    "Luminance": luminance_no_xyz,
                                    "K(L)":luminance_k,
                                    "Radiance": radiance,
                                    "K(R)": radiance_k
                                })
                            else:
                                for xyz in xyz_list:
                                    # move color filter
                                    mono.ml_move_xyz_syn(xyz)
                                    # set exposure by pyExposureSetting
                                    mono.ml_set_exposure(exposure=exposure)
                                    mono.ml_capture_image_syn()
                                    capture_data = mono.ml_get_CaptureData()
                                    capture_data_dict[xyz] = capture_data
                                # set capture data for measurement
                                ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                                if not ret.success:
                                    raise RuntimeError("ml_set_CaptureData error")
                                # load calibration data by calbration config
                                ret = colorimeter.ml_load_calibration_data(cali_config)
                                if not ret.success:
                                    raise RuntimeError("ml_load_calibration_data error")

                                # execute calibration process for capture data by calibration config
                                ret = colorimeter.ml_image_process(cali_config)
                                if not ret.success:
                                    raise RuntimeError("ml_image_process error")

                                # get calibration data after calibration process
                                processed_data = colorimeter.ml_get_processed_data(module_id)
                                for xyz in xyz_list:
                                    Luminance = luminance_values[xyz]
                                    # capture single image from camera
                                    img = processed_data[mlcm.CalibrationEnum.FFC][xyz].image
                                    # mono calibration
                                    average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                                    average_gray+=gray_offset
                                    # get exposure time
                                    exposure_time = mono.ml_get_exposure_time() + expusure_offset
                                    update_status(f"{str(gray)}_{mlcm.MLFilterEnum_to_str(xyz)}_{RX_str}__averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                                    gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                                    luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                                    radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                                    # add result to the list
                                    results.append({
                                        "Gray Range": f"{gray * 100}" + "%",
                                        "NDFilter": "None",
                                        "XYZFilter": mlcm.MLFilterEnum_to_str(xyz),
                                        "AVEGray": average_gray,
                                        "ExposureTime": exposure_time,
                                        "G/ET": gray_ET,
                                        "Luminance": Luminance,
                                        "K(L)":luminance_k,
                                        "Radiance": radiance,
                                        "K(R)": radiance_k
                                    })

        else:
            for nd in nd_list:
                # switch nd filter
                nd_enum = mlcm.MLFilterEnum(int(nd)) # et MLFilterEnum.ND0
                mono.ml_move_nd_syn(nd_enum)
                for gray in gray_range:
                    aeparams = mlcm.pyAEParams(dynamic_range=gray,target_max=gray + 0.05,target_min=gray - 0.05, max_time=19000, rate=1000000)
                    ret = mono.ml_update_AE_params(aeparams)
                    for sph in sph_list:
                        for cyl in cyl_list:
                            for axis in axis_list:
                                rx=mlcm.pyRXCombination(sph=sph,cyl=cyl,axis=axis)
                                ret=mono.ml_set_rx_syn(rx)
                                if not ret.success:
                                    raise RuntimeError("ml_set_rx_syn error")
                                RX_str = mlcm.pyRXCombination_to_str(rx)
                                cali_config=mlcm.pyCalibrationConfig(
                                        input_path=mono.ml_get_config_path(),
                                        aperture=mono.ml_get_aperture(),
                                        nd_filter_list=[nd_enum],
                                        color_filter_list=xyz_list,
                                        rx=mlcm.pyRXCombination(0,0,0),
                                        light_source_list=[mono.ml_get_light_source()],
                                        dark_flag=True,
                                        ffc_flag=True,
                                        color_shift_flag=False,
                                        distortion_flag=False,
                                        exposure_flag=False,
                                        four_color_flag=False
                                    )
                                if xyz_list == []:
                                    cali_config.color_filter_list=[mlcm.MLFilterEnum.X]
                                    mono.ml_set_exposure(exposure=exposure)
                                    mono.ml_capture_image_syn()
                                    capture_data = mono.ml_get_CaptureData()
                                    capture_data_dict[mlcm.MLFilterEnum.X] = capture_data
                                    # set capture data for measurement
                                    ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                                    if not ret.success:
                                        raise RuntimeError("ml_set_CaptureData error")
                                    # load calibration data by calbration config
                                    ret = colorimeter.ml_load_calibration_data(cali_config)
                                    if not ret.success:
                                        raise RuntimeError("ml_load_calibration_data error")

                                    # execute calibration process for capture data by calibration config
                                    ret = colorimeter.ml_image_process(cali_config)
                                    if not ret.success:
                                        raise RuntimeError("ml_image_process error")

                                    # get calibration data after calibration process
                                    processed_data = colorimeter.ml_get_processed_data(module_id)
                                    img = processed_data[mlcm.CalibrationEnum.FFC][mlcm.MLFilterEnum.X].image
                                    average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                                    average_gray+=gray_offset
                                    exposure_time = mono.ml_get_exposure_time() + expusure_offset
                                    update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{str(gray)}_{RX_str}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                                    gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                                    luminance_k= luminance_no_xyz / gray_ET if gray_ET > 0 else 0
                                    radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                                    results.append({
                                        "Gray Range": f"{gray * 100}" + "%",
                                        "NDFilter": mlcm.MLFilterEnum_to_str(nd_enum),
                                        "AVEGray": average_gray,
                                        "ExposureTime": exposure_time,
                                        "G/ET": gray_ET,
                                        "Luminance": luminance_no_xyz,
                                        "K(L)":luminance_k,
                                        "Radiance": radiance,
                                        "K(R)": radiance_k
                                    })
                                else:
                                    for xyz in xyz_list:
                                        # move color filter
                                        mono.ml_move_xyz_syn(xyz)
                                        # set exposure by pyExposureSetting
                                        mono.ml_set_exposure(exposure=exposure)
                                        # capture single image from camera
                                        mono.ml_capture_image_syn()

                                        capture_data = mono.ml_get_CaptureData()
                                        capture_data_dict[xyz] = capture_data
                                    # set capture data for measurement
                                    ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                                    if not ret.success:
                                        raise RuntimeError("ml_set_CaptureData error")
                                    # load calibration data by calbration config
                                    ret = colorimeter.ml_load_calibration_data(cali_config)
                                    if not ret.success:
                                        raise RuntimeError("ml_load_calibration_data error")

                                    # execute calibration process for capture data by calibration config
                                    ret = colorimeter.ml_image_process(cali_config)
                                    if not ret.success:
                                        raise RuntimeError("ml_image_process error")

                                    # get calibration data after calibration process
                                    processed_data = colorimeter.ml_get_processed_data(module_id)
                                    for xyz in xyz_list:
                                        Luminance = luminance_values[xyz]
                                        img = processed_data[mlcm.CalibrationEnum.FFC][xyz].image
                                        # mono calibration
                                        average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                                        average_gray+=gray_offset
                                        # get exposure time
                                        exposure_time = mono.ml_get_exposure_time() + expusure_offset
                                        update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{str(gray)}_{mlcm.MLFilterEnum_to_str(xyz)}_{RX_str}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                                        gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                                        luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                                        radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                                        # add result to the list
                                        results.append({
                                            "Gray Range": f"{gray * 100}" + "%",
                                            "NDFilter": mlcm.MLFilterEnum_to_str(nd_enum),
                                            "XYZFilter": mlcm.MLFilterEnum_to_str(xyz),
                                            "AVEGray": average_gray,
                                            "ExposureTime": exposure_time,
                                            "G/ET": gray_ET,
                                            "Luminance": Luminance,
                                            "K(L)":luminance_k,
                                            "Radiance": radiance,
                                            "K(R)": radiance_k
                                        })
                
    else:
        if nd_list==[]:
            for gray in gray_range:
                aeparams = mlcm.pyAEParams(dynamic_range=gray,target_max=gray + 0.05,target_min=gray - 0.05, max_time=19000, rate=1000000)
                ret = mono.ml_update_AE_params(aeparams)
                if xyz_list == []:
                    mono.ml_set_exposure(exposure=exposure)
                    mono.ml_capture_image_syn()
                    capture_data = mono.ml_get_CaptureData()
                    # 这里给一个默认XYZ值
                    capture_data_dict[mlcm.MLFilterEnum.X] = capture_data
                    # set capture data for measurement
                    ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                    if not ret.success:
                        raise RuntimeError("ml_set_CaptureData error")
                    cali_config=mlcm.pyCalibrationConfig(
                        input_path=mono.ml_get_config_path(),
                        aperture=mono.ml_get_aperture(),
                        nd_filter_list=[mlcm.MLFilterEnum.ND0],
                        xyz_filter_list=[mlcm.MLFilterEnum.X],
                        rx=mlcm.pyRXCombination(0,0,0),
                        light_source_list=[mono.ml_get_light_source()],
                        dark_flag=True,
                        ffc_flag=True,
                        color_shift_flag=False,
                        distortion_flag=False,
                        exposure_flag=False,
                        four_color_flag=False
                    )

                    # load calibration data by calbration config
                    ret = colorimeter.ml_load_calibration_data(cali_config)
                    if not ret.success:
                        raise RuntimeError("ml_load_calibration_data error")

                    # execute calibration process for capture data by calibration config
                    ret = colorimeter.ml_image_process(cali_config)
                    if not ret.success:
                        raise RuntimeError("ml_image_process error")

                    # get calibration data after calibration process
                    processed_data = colorimeter.ml_get_processed_data(module_id)

                    img = processed_data[mlcm.CalibrationEnum.FFC][mlcm.MLFilterEnum.X].image
                        
                    average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                    average_gray+=gray_offset
                    exposure_time = mono.ml_get_exposure_time() + expusure_offset
                    update_status(f"{str(gray)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                    gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                    luminance_k= luminance_no_xyz / gray_ET if gray_ET > 0 else 0
                    radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                    results.append({
                        "Gray Range": f"{gray * 100}" + "%",
                        "NDFilter": "None",
                        "AVEGray": average_gray,
                        "ExposureTime": exposure_time,
                        "G/ET": gray_ET,
                        "Luminance": luminance_no_xyz,
                        "K(L)":luminance_k,
                        "Radiance": radiance,
                        "K(R)": radiance_k
                    })
                else:
                    for xyz in xyz_list:
                        # move color filter
                        mono.ml_move_xyz_syn(xyz)
                        # set exposure by pyExposureSetting
                        mono.ml_set_exposure(exposure=exposure)
                        mono.ml_capture_image_syn()
                        capture_data = mono.ml_get_CaptureData()
                        capture_data_dict[xyz] = capture_data
                    # set capture data for measurement
                    ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                    if not ret.success:
                        raise RuntimeError("ml_set_CaptureData error")
                    cali_config=mlcm.pyCalibrationConfig(
                        input_path=mono.ml_get_config_path(),
                        aperture=mono.ml_get_aperture(),
                        nd_filter_list=[mlcm.MLFilterEnum.ND0],
                        xyz_filter_list=xyz_list,
                        rx=mlcm.pyRXCombination(0,0,0),
                        light_source_list=[mono.ml_get_light_source()],
                        dark_flag=True,
                        ffc_flag=True,
                        color_shift_flag=False,
                        distortion_flag=False,
                        exposure_flag=False,
                        four_color_flag=False
                    )
                    # load calibration data by calbration config
                    ret = colorimeter.ml_load_calibration_data(cali_config)
                    if not ret.success:
                        raise RuntimeError("ml_load_calibration_data error")

                    # execute calibration process for capture data by calibration config
                    ret = colorimeter.ml_image_process(cali_config)
                    if not ret.success:
                        raise RuntimeError("ml_image_process error")

                    # get calibration data after calibration process
                    processed_data = colorimeter.ml_get_processed_data(module_id)
                    for xyz in xyz_list:
                        Luminance = luminance_values[xyz]
                        # capture single image from camera
                        img = processed_data[mlcm.CalibrationEnum.FFC][xyz].image
                        # mono calibration
                        average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                        average_gray+=gray_offset
                        # get exposure time
                        exposure_time = mono.ml_get_exposure_time() + expusure_offset
                        update_status(f"{str(gray)}_{mlcm.MLFilterEnum_to_str(xyz)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                        gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                        luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                        radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                        # add result to the list
                        results.append({
                            "Gray Range": f"{gray * 100}" + "%",
                            "NDFilter": "None",
                            "XYZFilter": mlcm.MLFilterEnum_to_str(xyz),
                            "AVEGray": average_gray,
                            "ExposureTime": exposure_time,
                            "G/ET": gray_ET,
                            "Luminance": Luminance,
                            "K(L)":luminance_k,
                            "Radiance": radiance,
                            "K(R)": radiance_k
                        })

        else:
            for nd in nd_list:
                # switch nd filter
                nd_enum = mlcm.MLFilterEnum(int(nd)) # et MLFilterEnum.ND0
                mono.ml_move_nd_syn(nd_enum)
                for gray in gray_range:
                    aeparams = mlcm.pyAEParams(dynamic_range=gray,target_max=gray + 0.05,target_min=gray - 0.05, max_time=19000, rate=1000000)
                    ret = mono.ml_update_AE_params(aeparams)
                    if xyz_list == []:
                        mono.ml_set_exposure(exposure=exposure)
                        mono.ml_capture_image_syn()
                        capture_data = mono.ml_get_CaptureData()
                        capture_data_dict[mlcm.MLFilterEnum.X] = capture_data
                        # set capture data for measurement
                        ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                        if not ret.success:
                            raise RuntimeError("ml_set_CaptureData error")
                        cali_config=mlcm.pyCalibrationConfig(
                            input_path=mono.ml_get_config_path(),
                            aperture=mono.ml_get_aperture(),
                            nd_filter_list=[nd_enum],
                            xyz_filter_list=[mlcm.MLFilterEnum.X],
                            rx=mlcm.pyRXCombination(0,0,0),
                            light_source_list=[mono.ml_get_light_source()],
                            dark_flag=True,
                            ffc_flag=True,
                            color_shift_flag=False,
                            distortion_flag=False,
                            exposure_flag=False,
                            four_color_flag=False
                        )
                        # load calibration data by calbration config
                        ret = colorimeter.ml_load_calibration_data(cali_config)
                        if not ret.success:
                            raise RuntimeError("ml_load_calibration_data error")

                        # execute calibration process for capture data by calibration config
                        ret = colorimeter.ml_image_process(cali_config)
                        if not ret.success:
                            raise RuntimeError("ml_image_process error")

                        # get calibration data after calibration process
                        processed_data = colorimeter.ml_get_processed_data(module_id)
                        img = processed_data[mlcm.CalibrationEnum.FFC][mlcm.MLFilterEnum.X].image
                        average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                        average_gray+=gray_offset
                        exposure_time = mono.ml_get_exposure_time() + expusure_offset
                        update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{str(gray)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                        gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                        luminance_k= luminance_no_xyz / gray_ET if gray_ET > 0 else 0
                        radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                        results.append({
                            "Gray Range": f"{gray * 100}" + "%",
                            "NDFilter": mlcm.MLFilterEnum_to_str(nd_enum),
                            "AVEGray": average_gray,
                            "ExposureTime": exposure_time,
                            "G/ET": gray_ET,
                            "Luminance": luminance_no_xyz,
                            "K(L)":luminance_k,
                            "Radiance": radiance,
                            "K(R)": radiance_k
                        })
                    else:
                        for xyz in xyz_list:
                            # move color filter
                            mono.ml_move_xyz_syn(xyz)
                            # set exposure by pyExposureSetting
                            mono.ml_set_exposure(exposure=exposure)
                            # capture single image from camera
                            mono.ml_capture_image_syn()

                            capture_data = mono.ml_get_CaptureData()
                            capture_data_dict[xyz] = capture_data
                        # set capture data for measurement
                        ret = colorimeter.ml_set_CaptureData(module_id, capture_data_dict)
                        if not ret.success:
                            raise RuntimeError("ml_set_CaptureData error")
                        cali_config=mlcm.pyCalibrationConfig(
                            input_path=mono.ml_get_config_path(),
                            aperture=mono.ml_get_aperture(),
                            nd_filter_list=[nd_enum],
                            color_filter_list=xyz_list,
                            rx=mlcm.pyRXCombination(0,0,0),
                            light_source_list=[mono.ml_get_light_source()],
                            dark_flag=True,
                            ffc_flag=True,
                            color_shift_flag=False,
                            distortion_flag=False,
                            exposure_flag=False,
                            four_color_flag=False
                        )
                        # load calibration data by calbration config
                        ret = colorimeter.ml_load_calibration_data(cali_config)
                        if not ret.success:
                            raise RuntimeError("ml_load_calibration_data error")

                        # execute calibration process for capture data by calibration config
                        ret = colorimeter.ml_image_process(cali_config)
                        if not ret.success:
                            raise RuntimeError("ml_image_process error")

                        # get calibration data after calibration process
                        processed_data = colorimeter.ml_get_processed_data(module_id)
                        for xyz in xyz_list:
                            Luminance = luminance_values[xyz]
                            img = processed_data[mlcm.CalibrationEnum.FFC][xyz].image
                            # mono calibration
                            average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                            average_gray+=gray_offset
                            # get exposure time
                            exposure_time = mono.ml_get_exposure_time() + expusure_offset
                            update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{str(gray)}_{mlcm.MLFilterEnum_to_str(xyz)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                            gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                            luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                            radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                            # add result to the list
                            results.append({
                                "Gray Range": f"{gray * 100}" + "%",
                                "NDFilter": mlcm.MLFilterEnum_to_str(nd_enum),
                                "XYZFilter": mlcm.MLFilterEnum_to_str(xyz),
                                "AVEGray": average_gray,
                                "ExposureTime": exposure_time,
                                "G/ET": gray_ET,
                                "Luminance": Luminance,
                                "K(L)":luminance_k,
                                "Radiance": radiance,
                                "K(R)": radiance_k
                            })
    time.sleep(1)
    update_status("写入配置中...")
    
    # 将results中灰度值在80%的luminance_k和radiance_k写入配置文件，b为0
    for item in results:
        if item["Gray Range"] == "80.0%":
            if nd_list==[]:
                if xyz_list == []:
                    file_name="" + apturate + "_" + light_source
                else:
                    xyz_filter = item["XYZFilter"]
                    file_name="" + apturate + "_" + xyz_filter + "_" + light_source
            else:
                # 文件夹命名格式为Aperture_NDFilter_LightSource
                nd_filter = item["NDFilter"]
                if xyz_list == []:
                    file_name="" + apturate + "_" + nd_filter + "_" + light_source
                else:
                    xyz_filter = item["XYZFilter"]
                    file_name="" + apturate + "_" + nd_filter + "_" + xyz_filter + "_" + light_source
            luminance_k = item["K(L)"]
            radiance_k = item["K(R)"]
            luminance_config_path = os.path.join(eye1_path, "Luminance")
            create_directory(luminance_config_path)
            radiance_config_path = os.path.join(eye1_path, "Radiance")
            create_directory(radiance_config_path)

            luminance_file_path = os.path.join(luminance_config_path, file_name)
            os.makedirs(luminance_file_path, exist_ok=True)
            # 完整的文件路径
            luminance_json_file_path= os.path.join(luminance_file_path, "Luminance.json")
            # 创建要写入的字典
            data={
                "Luminance": [[float(luminance_k),0]]
            }
            save_json(data, luminance_json_file_path)

            radiance_file_path = os.path.join(radiance_config_path, file_name)
            os.makedirs(radiance_file_path, exist_ok=True)
            # 完整的文件路径
            radiance_json_file_path= os.path.join(radiance_file_path, "Radiance.json")
            # 创建要写入的字典
            data1={
                "Radiance": [[float(radiance_k),0]]
            }
            save_json(data1, radiance_json_file_path)
    time.sleep(1)
    update_status("写入完成，保存数据表")
    save_results_to_excel(results,out_path)

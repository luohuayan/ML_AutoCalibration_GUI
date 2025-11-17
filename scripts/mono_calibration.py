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


# Function to modify the exposure configuration
def modify_exposure_config(
    config_path, dynamic_range=0.5, target_max=0.55, target_min=0.45
):
    # Check if the file exists
    if not os.path.exists(config_path):
        # print(f"Configuration file not found: {config_path}")
        # logging.error(f"Configuration file not found: {config_path}")
        return

    # Read the JSON configuration
    with open(config_path, "r") as file:
        config = json.load(file)

    # Modify the configuration as needed
    for exposure in config["AutoExposure"]:
        exposure["FixedParameters"][
            "dynamic_range"
        ] = dynamic_range  # Set dynamic_range
        exposure["JudgmentMechanism"]["targetMax"] = target_max  # Set targetMax
        exposure["JudgmentMechanism"]["targetMin"] = target_min  # Set targetMin

    # Save the modified configuration back to the file
    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)

    # print(f"Configuration file updated: {config_path}")


# Function to show a message box with the light source information
def show_message(light_source):
    # Create a hidden root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    # Show the message box
    messagebox.showinfo("提示", "请切换光源到: " + light_source)
    root.destroy()

# 配置日志
def setup_logging(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "serial.log")),
            logging.StreamHandler(),
        ],
    )

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
                    xyz_enum = mlcm.MLFilterEnum(int(xyz))
                    Luminance = luminance_values[xyz_enum]
                    # move color filter
                    mono.ml_move_xyz_syn(xyz_enum)
                    # set exposure by pyExposureSetting
                    mono.ml_set_exposure(exposure=exposure)
                    # capture single image from camera
                    mono.ml_capture_image_syn()
                    img = mono.ml_get_image()
                    # mono calibration
                    average_gray = process_image(img,image_x,image_y,roi_width,roi_height)
                    # get exposure time
                    exposure_time = mono.ml_get_exposure_time() + expusure_offset
                    update_status(f"{mlcm.MLFilterEnum_to_str(nd_enum)}_{str(gray)}_{mlcm.MLFilterEnum_to_str(xyz_enum)}_averageGray:{str(average_gray)}_exposureTime:{str(exposure_time)}")
                    gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                    luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                    radiance_k = radiance / gray_ET if gray_ET > 0 else 0
                    # add result to the list
                    results.append({
                        "Gray Range": f"{gray * 100}" + "%",
                        "NDFilter": mlcm.MLFilterEnum_to_str(nd_enum),
                        "XYZFilter": mlcm.MLFilterEnum_to_str(xyz_enum),
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

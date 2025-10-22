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


# Function to modify the exposure configuration
def modify_exposure_config(
    config_path, dynamic_range=0.5, target_max=0.55, target_min=0.45
):
    # Check if the file exists
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        logging.error(f"Configuration file not found: {config_path}")
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

    print(f"Configuration file updated: {config_path}")


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

def process_image(img):
    roi_list = []
    for x, y in [(6688, 4764)]:
        y1,y2 = int(y -125), int(y +125)
        x1, x2 = int(x -125), int(x + 125)
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

if __name__ == "__main__":
    eye1_path = r"D:\MLColorimeter\config\EYE1"
    aperture = "3mm"
    # 选择光源
    light_source = "W"
    # 定义亮度值映射
    luminance_values = {
        mlcm.MLFilterEnum.X: 100,
        mlcm.MLFilterEnum.Y: 150,
        mlcm.MLFilterEnum.Z: 200,
        mlcm.MLFilterEnum.Clear: 0
    }
    # 设置Radiance
    Radiance = 100
    # 输出路径
    out_path = r"D:\Output\calibrations" + "\\" + light_source

    auto_exposure_config_path = os.path.join(eye1_path, "AutoExposureConfig.json")

    luminance_config_path = os.path.join(eye1_path, "Luminance")
    create_directory(luminance_config_path)

    radiance_config_path = os.path.join(eye1_path, "Radiance")
    create_directory(radiance_config_path)

    luminance_json_name="Luminance.json"
    radiance_json_name="Radiance.json"
    log_dir = r"D:\Output\calibrations\logs"
    setup_logging(log_dir)

    # switch light source
    show_message(light_source)
    with mlcm.ML_Colorimeter() as ml_colorimeter:
        path_list = [
            eye1_path,
        ]
        # nd filter keyword, from the "Key" field in NDFilterConfig.json
        nd_key = "NDFilter"
        # xyz filter keyword, from the "Key" field in NDFilterConfig.json
        xyz_key = "ColorFilter"
        # nd filter to switch during measurement
        nd_list = [mlcm.MLFilterEnum.ND0, mlcm.MLFilterEnum.ND1, mlcm.MLFilterEnum.ND2, mlcm.MLFilterEnum.ND3, mlcm.MLFilterEnum.ND4]
        # xyz filter to switch during measurement
        xyz_list = [mlcm.MLFilterEnum.X, mlcm.MLFilterEnum.Y, mlcm.MLFilterEnum.Z, mlcm.MLFilterEnum.Clear]
        # xyz_list=[]
        # xyz_list = [mlcm.MLFilterEnum.Clear]
        # gray range for calibration
        # gray_range = [0.5]
        gray_range = [0.5, 0.6, 0.7, 0.8, 0.9]

        # 1、连接对应模块
        # add mono module into ml_colorimeter system, according to path_list create one or more mono module
        ml_colorimeter.ml_add_module(path_list=path_list)
        # connect all module in the ml_colorimeter system
        ret = ml_colorimeter.ml_connect()
        module_id = 1
        ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)

        # set light source
        ml_mono.ml_set_light_source(light_source)

        # camera binning
        binning = mlcm.Binning.ONE_BY_ONE
        # camera binning mode
        binning_mode = mlcm.BinningMode.AVERAGE
        # camera pixel format
        pixel_format = mlcm.MLPixelFormat.MLMono12
        exposure = mlcm.pyExposureSetting(
            exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100
        )
        
        # create a list for save results
        results = []
        for gray in gray_range:
            aeparams = mlcm.pyAEParams(dynamic_range=gray,target_max=gray + 0.05,target_min=gray - 0.05)
            ret = ml_mono.ml_update_AE_params(aeparams)
            logging.info(f"dynamic_range: {gray}" )

            for nd in nd_list:
                # switch nd filter
                ml_mono.ml_move_nd_syn(nd)
                if xyz_list == []:
                    # set exposure by pyExposureSetting
                    ml_mono.ml_set_exposure(exposure=exposure)
                    # capture single image from camera
                    ml_mono.ml_capture_image_syn()
                    img = ml_mono.ml_get_image()
                    average_gray = process_image(img)
                    logging.info(f"Gray value {nd} filter: {average_gray}")
                    # get exposure time
                    exposure_time = ml_mono.ml_get_exposure_time()
                    gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                    luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                    radiance_k = Radiance / gray_ET if gray_ET > 0 else 0
                    logging.info(f"Exposure time: {exposure_time}")
                    # add result to the list
                    results.append({
                        "Gray Range": f"{gray * 100}" + "%",
                        "NDFilter": mlcm.MLFilterEnum_to_str(nd),
                        "AVEGray": average_gray,
                        "ExposureTime": exposure_time,
                        "G/ET": gray_ET,
                        "Luminance": Luminance,
                        "K(L)":luminance_k,
                        "Radiance": Radiance,
                        "K(R)": radiance_k
                    })
                else:
                    for xyz in xyz_list:
                        Luminance = luminance_values[xyz]
                        # move color filter
                        ml_mono.ml_move_xyz_syn(xyz)
                        # set exposure by pyExposureSetting
                        ml_mono.ml_set_exposure(exposure=exposure)
                        # capture single image from camera
                        ml_mono.ml_capture_image_syn()
                        img = ml_mono.ml_get_image()
                        # cv2.imwrite("D:\\Output\\calibrations" + mlcm.MLFilterEnum_to_str(nd) + "_" + mlcm.MLFilterEnum_to_str(xyz) + ".tif", img[1])
                        # print(type(img))
                        # print(img.keys())
                        # mono calibration
                        average_gray = process_image(img)
                        logging.info(f"Gray value for {xyz} filter with {nd} filter: {average_gray}")
                        # get exposure time
                        exposure_time = ml_mono.ml_get_exposure_time()
                        gray_ET= average_gray / exposure_time if exposure_time > 0 else 0
                        luminance_k= Luminance / gray_ET if gray_ET > 0 else 0
                        radiance_k = Radiance / gray_ET if gray_ET > 0 else 0
                        logging.info(f"Exposure time: {exposure_time}")
                        # add result to the list
                        results.append({
                            "Gray Range": f"{gray * 100}" + "%",
                            "NDFilter": mlcm.MLFilterEnum_to_str(nd),
                            "XYZFilter": mlcm.MLFilterEnum_to_str(xyz),
                            "AVEGray": average_gray,
                            "ExposureTime": exposure_time,
                            "G/ET": gray_ET,
                            "Luminance": Luminance,
                            "K(L)":luminance_k,
                            "Radiance": Radiance,
                            "K(R)": radiance_k
                        })
        # 将results中灰度值在80%的luminance_k和radiance_k写入配置文件，b为0
        for item in results:
            if item["Gray Range"] == "80.0%":
                # 文件夹命名格式为Aperture_NDFilter_LightSource
                nd_filter = item["NDFilter"]
                if xyz_list == []:
                    file_name="" + aperture + "_" + nd_filter + "_" + light_source
                else:
                    xyz_filter = item["XYZFilter"]
                    file_name="" + aperture + "_" + xyz_filter + "_" + nd_filter + "_" + light_source
                luminance_k = item["K(L)"]
                radiance_k = item["K(R)"]
                luminance_file_path = os.path.join(luminance_config_path, file_name)
                os.makedirs(luminance_file_path, exist_ok=True)
                # 完整的文件路径
                luminance_json_file_path= os.path.join(luminance_file_path, luminance_json_name)
                # 创建要写入的字典
                data={
                    "Luminance": [[float(luminance_k),0]]
                }
                save_json(data, luminance_json_file_path)

                radiance_file_path = os.path.join(radiance_config_path, file_name)
                os.makedirs(radiance_file_path, exist_ok=True)
                # 完整的文件路径
                radiance_json_file_path= os.path.join(radiance_file_path, radiance_json_name)
                # 创建要写入的字典
                data1={
                    "Radiance": [[float(radiance_k),0]]
                }
                save_json(data1, radiance_json_file_path)
        save_results_to_excel(results,out_path)

        # 更改配置文件中灰度值为80%
        # modify_exposure_config(
        #     auto_exposure_config_path,
        #     dynamic_range=0.8,
        #     target_max=0.85,
        #     target_min=0.75,
        # )

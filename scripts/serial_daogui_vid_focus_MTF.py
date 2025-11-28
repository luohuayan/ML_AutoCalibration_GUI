from scripts.serial_daogui import serial_daogui
import logging
import os
import time
import mlcolorimeter as mlcm
import cv2
import numpy as np
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
import matplotlib.pyplot as plt
import json
from typing import List


def move_test(
        colorimeter:mlcm.ML_Colorimeter,
        binn:mlcm.Binning,
        binn_mode:mlcm.BinningMode,
        pixel_format:mlcm.MLPixelFormat,
        binn_selector:mlcm.BinningSelector,
        total_pulse:int,


):
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    # 电机名称
    key_name = "CameraMotion"
    ret = ml_mono.ml_set_binning_selector(binn_selector)
    if not ret.success:
        raise RuntimeError("ml_set_binning_selector error")
    ml_mono.ml_set_binning(binn)
    ml_mono.ml_set_binning_mode(binn_mode)
    ml_mono.ml_set_pixel_format(pixel_format)

    pass

# 加载ROI配置文件
def load_roi_config(file_path):
    """
    Load the ROI configuration from a JSON file.
    
    :param file_path: Path to the JSON configuration file.
    :return: Dictionary containing the ROI configuration.
    """
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON.")
        return {}

# 根据vid获取对应的ROI区域
def get_roi_by_vid(vid, config):
    """
    Get the ROI configuration for a specific VID.
    
    :param vid: The VID for which to get the ROI configuration.
    :param config: The loaded configuration dictionary.
    :return: List of ROIs for the specified VID, or an empty list if not found.
    """
    roi_list= config.get(str(vid))
    if roi_list is None:
        print(f"No ROI configuration found for VID: {vid}")
        return []
    roi_focus_list = []
    for roi_params in roi_list:
        roi=mlcm.pyCVRect(**roi_params)
        roi_focus_list.append(roi)
    return roi_focus_list


def set_focus_config(
    focus_max,
    focus_min,
    rough_step,
    focal_length,
    pixel_size=0.0032,
    fine_step=0.01,
    use_fine_adjust=False,
):
    return mlcm.pyThroughFocusConfig(
        focus_max=focus_max,
        focus_min=focus_min,
        inf_position=infinity_position,
        focal_length=focalLength,
        pixel_size=pixel_size,
        use_fine_adjust=use_fine_adjust,
        rough_step=rough_step,
        fine_step=fine_step,
        use_lpmm_unit=True,
        use_chess_mode=True,
        freq=freq,
        average_count=3
    )

def get_image_finefocus(focusvid):
    # 移动电机到指定位置
    ml_mono.ml_set_pos_abs_syn(motion_name=key_name,pos=focusvid)
    time.sleep(0.1)
    # 拍图
    ml_mono.ml_capture_image_syn()
    img = ml_mono.ml_get_image()
    cv2.imwrite("D:\\Output\\throughfocus\\through_focus\\" + str(focusvid) + ".tif", img)

# 根据不同的vid获取不同的过焦范围以及步长
def get_focus_config(vid):
    """
    根据不同的vid获取不同的过焦范围以及步长。

    :param vid: 视距值。
    :return: 过焦配置对象。
    """
    # coef=round(pow(focalLength,2)/1000,2)
    coef=0.80
    # 保留两位小数
    fine_focus = round((infinity_position +1000 / vid * coef),2)
    # get_image_finefocus(fine_focus)
    return set_focus_config(
        focus_max=fine_focus + 1,
        focus_min=fine_focus - 1,
        rough_step=rough_step,
        focal_length=focalLength
    )

def rename_csv_files(directory, new_extension):
    for filename in os.listdir(directory):
        if filename.endswith(".csv") and filename == "coarse_result.csv":
            old_path = os.path.join(directory, filename)
            old_path_1 = csv_to_xlsx_and_insertcurve(old_path, directory)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            new_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{new_extension}"
            new_path = os.path.join(directory, new_filename)
            os.rename(old_path_1, new_path)
            logging.info(f"Renamed {old_path_1} to {new_path}")

            os.remove(old_path)

def csv_to_xlsx_and_insertcurve(filepath, directory):
    data = pd.read_csv(filepath)
    # 将数据保存到Excel文件
    excel_file = directory + "\\coarse_result.xlsx"
    data.to_excel(excel_file, index=False)
    return excel_file

def clear_directory(directory):
    """
    清空指定目录下的所有文件。

    :param directory: 需要清空的目录路径。
    """
    if not os.path.exists(directory):
        logging.warning(f"Directory {directory} does not exist.")
        return
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            logging.info(f"Deleted file: {file_path}")
        elif os.path.isdir(file_path):
            os.rmdir(file_path)
            logging.info(f"Deleted directory: {file_path}")

def delete_files_by_vid(directory, vid):
    """
    删除指定目录下所有包含特定VID的文件。

    :param directory: 需要删除文件的目录路径。
    :param vid: 需要删除的VID。
    """
    if not os.path.exists(directory):
        logging.warning(f"Directory {directory} does not exist.")
        return
    for filename in os.listdir(directory):
        if str(vid) in filename and filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                logging.info(f"Deleted file: {file_path}")
            except Exception as e:
                logging.error(f"Error deleting file {file_path}: {e}")

def mtf_measure(
    modelu_id: int,
    exposure: mlcm.pyExposureSetting,
    binning: mlcm.Binning,
    binning_mode: mlcm.BinningMode,
    pixel_format: mlcm.MLPixelFormat,
    VID,
):
    path = out_path + "\\through_focus"
    os.makedirs(path, exist_ok=True)
    ml_mono.ml_set_exposure(exposure=exposure)
    config=load_roi_config(roi_config_path)
    roi_focus_list = get_roi_by_vid(VID, config)
    through_config = get_focus_config(VID)
    through_config.rois = roi_focus_list
    # 走焦
    ml_mono.ml_vid_scan(motion_name=key_name, focus_config=through_config)
    # 保存走焦结果
    ml_mono.ml_save_vid_scan_result(out_path)
    # 重命名
    rename = "_" + f"{VID}" + "mm.xlsx"
    rename_csv_files(path, rename)

def start_test_daogui(
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    update_status("导轨开始移动")
    total_pulse=2000000
    ser = serial_daogui("COM7",total_pulse)
    ser.move_VID(2000)
    update_status("导轨停止移动")
    # 移动结束后关闭串口
    disconnect = ser.disconnect()
    if disconnect:
        update_status("串口连接已关闭")
    else:
        update_status("串口关闭失败")

def start_capture_image_vid(
        colorimeter:mlcm.ML_Colorimeter,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        vid_list:List[int],
        inf_pos:float,
        pos_offset:float,
        coef:float,
        total_pulse:int,
        out_path:str,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    update_status("开始拍图")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    mydaogui = serial_daogui("COM7", total_pulse=total_pulse)
    ml_mono.ml_set_binning_selector(binn_selector)
    ml_mono.ml_set_binning(binn)
    ml_mono.ml_set_binning_mode(binn_mode)
    ml_mono.ml_set_pixel_format(pixel_format)
    # 电机名称
    key_name = "CameraMotion"

    # exposure mode setting, Auto or Fixed
    exposure_mode = mlcm.ExposureMode.Auto
    # exposure time for fixed exposure, initial time for auto exposure
    exposure_time = 100
    exposure = mlcm.pyExposureSetting(
        exposure_mode=exposure_mode, exposure_time=exposure_time
    )

    for vid in vid_list:
        mydaogui.move_VID(vid)
        # 获取当前vid对应的PI值
        fine_focus = round((inf_pos + pos_offset / vid * coef),2)
        ml_mono.ml_set_exposure(exposure=exposure)
        # 移动电机到当前PI对应的位置，并拍摄图片
        # 移动电机到指定位置
        ml_mono.ml_set_pos_abs_syn(motion_name=key_name,pos=fine_focus)
        time.sleep(0.1)
        # 拍图
        ml_mono.ml_capture_image_syn()
        img = ml_mono.ml_get_image()
        cv2.imwrite(out_path + "\\" + str(fine_focus) + "_" + str(vid) + ".tif", img)
        update_status(f"{str(vid)}最佳位置拍图保存成功")
    update_status("finish")
    mydaogui.disconnect()

def get_all_mtf_config(
        configpath:str
):
    try:
        combined_data={}
        # 遍历目录下的所有JSON文件
        for file_name in os.listdir(configpath):
            if file_name.endswith('.json'):
                full_path = os.path.join(configpath, file_name)
                with open(full_path, 'r') as file:
                    config = json.load(file)
                    vid = os.path.splitext(file_name)[0]
                    combined_data[vid] = config
        return combined_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file {configpath} does not exist.")
    except json.JSONDecodeError:
        raise ValueError(f"Error: The file {configpath} is not a valid JSON.")
    

def start_generate_roi_config(
        roi_set_path:str,
        roi_out_path:str,
):
    try:
        combined_data={}
        # 遍历目录下的所有JSON文件
        for file_name in os.listdir(roi_set_path):
            if file_name.endswith('.json'):
                full_path = os.path.join(roi_set_path, file_name)
                with open(full_path, 'r') as file:
                    config = json.load(file)
                    vid = os.path.splitext(file_name)[0]
                    combined_data[vid] = config
        save_config_path_json=os.path.join(roi_out_path, "roividconfig.json")
        result={}
        for config_key,config_value in combined_data.items():
            # 创建一个新的列表来存储该配置的区域
            result[config_key.split('-')[-1]] = []
            for roi_key,roi_value in config_value.items():
                entry={
                    "x":roi_value["x"],
                    "y":roi_value["y"],
                    "width":roi_value["width"], 
                    "height":roi_value["height"]
                }
                result[config_key.split('-')[-1]].append(entry)

        with open(save_config_path_json, 'w') as file:
            json.dump(result, file, indent=4)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file {roi_set_path} does not exist.")
    except json.JSONDecodeError:
        raise ValueError(f"Error: The file {roi_set_path} is not a valid JSON.")
    

def start_calibration_vid(
        colorimeter:mlcm.ML_Colorimeter,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        pixel_format:mlcm.MLPixelFormat,
        vid_list:List[int],
        inf_pos:float,
        pos_offset:float,
        coef:float,
        total_pulse:int,
        roi_out_path:int,
        out_path:str,
        light_source:str,
        through_focus:mlcm.pyThroughFocusConfig,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    update_status("开始拍图")
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
    mydaogui = serial_daogui("COM7", total_pulse=total_pulse)
    ml_mono.ml_set_binning_selector(binn_selector)
    ml_mono.ml_set_binning(binn)
    ml_mono.ml_set_binning_mode(binn_mode)
    ml_mono.ml_set_pixel_format(pixel_format)
    # 电机名称
    key_name = "CameraMotion"

    # exposure mode setting, Auto or Fixed
    exposure_mode = mlcm.ExposureMode.Auto
    # exposure time for fixed exposure, initial time for auto exposure
    exposure_time = 100
    exposure = mlcm.pyExposureSetting(
        exposure_mode=exposure_mode, exposure_time=exposure_time
    )
    result_path=out_path+"\\"+light_source
    os.makedirs(result_path,exist_ok=True)
    path=result_path+"\\throught_focus"
    os.makedirs(path,exist_ok=True)
    roi_config_path=os.path.join(roi_out_path, "roividconfig.json")


    for vid in vid_list:
        mydaogui.move_VID(vid)
        ml_mono.ml_set_exposure(exposure=exposure)
        config=load_roi_config(roi_config_path)
        roi_focus_list=get_roi_by_vid(vid,config)
        fine_focus=round((inf_pos+pos_offset/vid*coef),2)
        through_focus.focus_max=fine_focus+1
        through_focus.focus_min=fine_focus-1
        through_focus.rois=roi_focus_list
        # 走焦
        ml_mono.ml_vid_scan(motion_name=key_name,focus_config=through_focus)
        # 保存走焦结果
        ml_mono.ml_save_vid_scan_result(result_path)
        rename="_"+f"{vid}"+"mm.xlsx"
        rename_csv_files(path,rename)





if __name__ == "__main__":
    eye1_path = r"D:\MLOptic\MLColorimeter\config\EYE1"
    light_source = "W"
    out_path = r"D:\Output\throughfocus" + "\\" + light_source
    os.makedirs(out_path, exist_ok=True)
    # roi配置路径
    roi_config_path=r"E:\daogui_auto_calibration\roividconfig.json"
    log_dir = r"D:\Output\throughfocus\logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "serial.log")),
            logging.StreamHandler(),
        ],
    )
    station_address = 0x05  # station address
    baudrate = 115200
    rough_step = 0.02
    infinity_position = 6.05
    freq=15
    total_pulse = 2137000
    focalLength = 13.32
    
    ser = serial_daogui.serial_daogui("COM7",total_pulse)
    

    with mlcm.ML_Colorimeter() as ml_colorimeter:
        path_list = [
            eye1_path,
        ]
        # 1、连接对应模块
        # add mono module into ml_colorimeter system, according to path_list create one or more mono module
        ret = ml_colorimeter.ml_add_module(path_list=path_list)
        if not ret.success:
            raise RuntimeError("ml_add_module error")
        # connect all module in the ml_colorimeter system
        ret = ml_colorimeter.ml_connect()
        if not ret.success:
            raise RuntimeError("ml_connect error")

        # exposure mode setting, Auto or Fixed
        exposure_mode = mlcm.ExposureMode.Auto
        # exposure time for fixed exposure, initial time for auto exposure
        exposure_time = 100
        # camera binning
        binning = mlcm.Binning.ONE_BY_ONE
        # camera binning mode
        binning_mode = mlcm.BinningMode.AVERAGE
        # camera pixel format
        pixel_format = mlcm.MLPixelFormat.MLMono12

        exposure = mlcm.pyExposureSetting(
            exposure_mode=exposure_mode, exposure_time=exposure_time
        )

        id_list = ml_colorimeter.id_list

        # 电机名称
        key_name = "CameraMotion"

        module_id = 1
        ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
        ml_mono.ml_set_binning(binning)
        ml_mono.ml_set_binning_mode(binning_mode)
        ret = ml_mono.ml_set_pixel_format(pixel_format)
        if not ret.success:
            raise RuntimeError("ml_set_pixel_format error")

        # 设置过焦参数

        # 这里是镜头到棋盘格的距离,单位mm
        distance = 140

        # 2、VID参数列表 vid list
        # 1米的导轨，2000plus=1mm,下面的列表对应cm单位的距离为[10,20,30,40,50,60,70,80,90,100]
        # vid_list = [200000, 400000, 600000, 800000, 1000000, 1200000, 1400000, 1600000, 1800000, 2000000]  # 1米导轨的距离定义
        # 100000对应100mm即0.1m， 2米的导轨，1000plus=1mm
    # vid_list = [300]
        # vid_list = [250, 333,500, 800, 1000,1200, 1250,1400, 1500,1600, 1800,2000]
        # vid_list = [166,200] 
        vid_list = [250, 300, 333,400, 500,600,700,800,900, 1000,1300, 1600,2000]
        for vid in vid_list:
            ser.move_VID(vid)
            mtf_measure(
                modelu_id=module_id,
                exposure=exposure,
                binning=binning,
                binning_mode=binning_mode,
                pixel_format=pixel_format,
                VID=vid,
            )
            time.sleep(0.2)
        ser.clear_alarm()

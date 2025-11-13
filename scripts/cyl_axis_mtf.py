import mlcolorimeter as mlcm
from typing import List, Dict
import pandas as pd
import os
from datetime import datetime
import cylaxismtf.MTF_cylaxis as mtfca
import cv2
import numpy as np

def extract_rois(image,points,width=30,height=30):
    """
    从给定图像中提取多个 ROI

    参数：
    - image: 输入图像（灰度图或彩色图）。
    - points: 包含中心点坐标的列表，格式为 [(x1, y1), (x2, y2), ...]。
    - width: 每个 ROI 的宽度。
    - height: 每个 ROI 的高度。

    返回：
    - rois: 提取的 ROI 列表。
    """
    rois=[]

    for point in points:
        point_x,point_y=point

        # 计算 ROI 的左上角和右下角坐标
        x1 = int(point_x - width / 2)
        y1 = int(point_y - height / 2)
        x2 = int(point_x + width / 2)
        y2 = int(point_y + height / 2)

        # 确保坐标在合法范围内
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image.shape[1], x2)
        y2 = min(image.shape[0], y2)

        # 提取ROI
        roi=image[y1:y2,x1:x2]
        rois.append(roi)
    
    return rois

def mtf_calculate(
        colorimeter:mlcm.ML_Colorimeter,
        mtfca:mtfca.MTF_cylaxis,
        binn_selector:mlcm.BinningSelector,
        binn_mode:mlcm.BinningMode,
        binn:mlcm.Binning,
        mtf_type:mtfca.MTF_TYPE,
        pixel_format:mlcm.MLPixelFormat,
        freq0:float,
        move_pixel:int,
        save_path:str,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        pixel_size:float,
        focal_length:float,
        cyl_list:List[float],
        axis_list:List[int]
):
    # module_id from the ModuleConfig.json
    module_id = 1
    mtf_data={ax:[] for ax in axis_list}
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
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
    exposure=mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=100)

    mtfca.setpixelsize(pixelsize=pixel_size)
    mtfca.setfocallength(focallength=focal_length)

    for nd in nd_list:
        # move nd filter
        ret = ml_mono.ml_move_nd_syn(nd)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")
        for xyz in xyz_list:
            ret=ml_mono.ml_move_xyz_syn(xyz)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn error")
            # capture spherical 0d for all cylindrical and axis
            # set sphere to 0
            for sph in [0]:
                # cylinder list to set, should match EYE1/config.ini [FFC] Cylinder_Mapping
                for cyl in cyl_list:
                    # axis list to set, should match EYE1/config.ini [FFC] Axis_Mapping
                    for axis in axis_list:
                        results=[]
                        rx = mlcm.pyRXCombination(sph, cyl, axis)
                        ret=ml_mono.ml_set_rx_syn(rx)
                        if not ret.success:
                            raise RuntimeError("ml_set_rx_syn error")
                        ml_mono.ml_set_exposure(exposure=exposure)
                        # capture single image from camera
                        ml_mono.ml_capture_image_syn()
                        img = ml_mono.ml_get_image()
                        # cv2.imwrite(out_path + "\\" + f"img_{str(cyl)}_{str(axis)}.tif",img)
                        point = mtfca.getcrossCenter(img=img)
                        # 十字线中心点坐标
                        center_x = point.get("x")
                        center_y = point.get("y")

                        # 定义四个roi中心点坐标
                        points=[(center_x,center_y-move_pixel),
                                (center_x, center_y+move_pixel),
                                (center_x-move_pixel,center_y),
                                (center_x+move_pixel,center_y)]
                        rois=extract_rois(img,points)
                        for i,roi in enumerate(rois):
                            # cv2.imwrite(out_path + "\\" + f"{str(cyl)}_{str(axis)}_roi_{i+1}.tif",roi)
                            # print(f"ROI {i} shape: {roi.shape}, dtype: {roi.dtype}")  # 打印 ROI 的形状和数据类型
                            roi_array=roi.copy()
                            ret=mtfca.calculateMTF(roi_array,mtf_type,freq0)
                            if ret.flag:
                                results.append(ret.mtf0)
                            else:
                                results.append(0.0)
                        mtf_data[axis].append(", ".join(map(str, results)))  # 将四个值合并为字符串
                        # 在柱面镜转到一个角度后，在下一个角度转动之前，先将柱面镜和轴转到0的位置
                        rx = mlcm.pyRXCombination(0, 0, 0)
                        ret=ml_mono.ml_set_rx_syn(rx)
                        if not ret.success:
                            raise RuntimeError("ml_set_rx_syn error")
            mtf_df=pd.DataFrame(mtf_data,index=cyl_list)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_excel_name="mtf_values" + "_" + timestamp + ".xlsx"
            output_excel_path=os.path.join(save_path,output_excel_name)
            # 保存为 Excel 文件
            mtf_df.to_excel(output_excel_path, sheet_name="MTF_Values")

# if __name__ == "__main__":
#     # set mono module calibration configuration path
#     eye1_path = r"E:\SDK\EYE1"
#     out_path=r"D:\Output"
#     os.makedirs(out_path, exist_ok=True)
#     image_path=r"D\Images"
#     os.makedirs(image_path, exist_ok=True)

#     pixel_size=0.00345
#     focal_length=40
#     freq0=10
#     move_pixel = 50
#     path_list = [
#         eye1_path,
#     ]
#     try:
#         cam=mtfca.MTF_cylaxis()
#         mtf_type=mtfca.MTF_TYPE.CROSS
#         cam.setpixelsize(pixelsize=pixel_size)
#         cam.setfocallength(focallength=focal_length)
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

#         # module_id from the ModuleConfig.json
#         module_id = 1
#         ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
#         ml_process=ml_colorimeter.ml_process_list[module_id]
#         # path to save ffc images
#         save_path = eye1_path

#         # nd filter list to switch during capture
#         nd_list = [mlcm.MLFilterEnum.ND3]
#         # xyz filter list to switch during capture
#         xyz_list = [
#             mlcm.MLFilterEnum.Clear
#         ]
#         cylinders=[-4]
#         # cylinders=[-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0]
#         axiss=[0,90,180,270]
#         mtf_data={ax:[] for ax in axiss}

#         exposure=mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Auto, exposure_time=1000)
        
#         # set pixel format to MLMono12 for capture
#         ret = ml_mono.ml_set_pixel_format(pixel_format=mlcm.MLPixelFormat.MLMono12)
#         if not ret.success:
#             raise RuntimeError("ml_set_pixel_format error")
        
#         # camera binning selector
#         binn_selector = mlcm.BinningSelector.Logic
#         # camera binning，ONE_BY_ONE，TWO_BY_TWO，FOUR_BY_FOUR，EIGHT_BY_EIGHT，SIXTEEN_BY_SIXTEEN
#         binn = mlcm.Binning.ONE_BY_ONE
#         # camera binning mode
#         binn_mode = mlcm.BinningMode.AVERAGE

#         ret = ml_mono.ml_set_binning_selector(binn_selector)
#         if not ret.success:
#             raise RuntimeError("ml_set_binning_selector error")

#         ret = ml_mono.ml_set_binning(binn)
#         if not ret.success:
#             raise RuntimeError("ml_set_binning error")

#         # Set binning mode for camera.
#         ret = ml_mono.ml_set_binning_mode(binn_mode)
#         if not ret.success:
#             raise RuntimeError("ml_set_binning_mode error")

#         for nd in nd_list:
#             # move nd filter
#             ret = ml_mono.ml_move_nd_syn(nd)
#             if not ret.success:
#                 raise RuntimeError("ml_move_nd_syn error")
#             for xyz in xyz_list:
#                 ret=ml_mono.ml_move_xyz_syn(xyz)
#                 if not ret.success:
#                     raise RuntimeError("ml_move_xyz_syn error")
#                 # capture spherical 0d for all cylindrical and axis
#                 # set sphere to 0
#                 for sph in [0]:
#                     # cylinder list to set, should match EYE1/config.ini [FFC] Cylinder_Mapping
#                     for cyl in cylinders:
#                         # axis list to set, should match EYE1/config.ini [FFC] Axis_Mapping
#                         for axis in axiss:
#                             results=[]
#                             rx = mlcm.pyRXCombination(sph, cyl, axis)
#                             ret=ml_mono.ml_set_rx_syn(rx)
#                             if not ret.success:
#                                 raise RuntimeError("ml_set_rx_syn error")
#                             ml_mono.ml_set_exposure(exposure=exposure)
#                             # capture single image from camera
#                             ml_mono.ml_capture_image_syn()
#                             img = ml_mono.ml_get_image()
#                             cv2.imwrite(out_path + "\\" + f"img_{str(cyl)}_{str(axis)}.tif",img)
#                             point = cam.getcrossCenter(img=img)
#                             # 十字线中心点坐标
#                             center_x = point.get("x")
#                             center_y = point.get("y")

#                             # 定义四个roi中心点坐标
#                             points=[(center_x,center_y-move_pixel),
#                                     (center_x, center_y+move_pixel),
#                                     (center_x-move_pixel,center_y),
#                                     (center_x+move_pixel,center_y)]
#                             rois=extract_rois(img,points)
#                             for i,roi in enumerate(rois):
#                                 cv2.imwrite(out_path + "\\" + f"{str(cyl)}_{str(axis)}_roi_{i+1}.tif",roi)
#                                 # print(f"ROI {i} shape: {roi.shape}, dtype: {roi.dtype}")  # 打印 ROI 的形状和数据类型
#                                 roi_array=roi.copy()
#                                 # mtf_result = ml_process.ml_cal_MTF(roi_array,freq0,focal_length,pixel_size,use_lpmm_unit=False,use_chess_mode=False)
#                                 # results.append(mtf_result)
#                                 ret=cam.calculateMTF(roi_array,mtf_type,freq0)
#                                 if ret.flag:
#                                     results.append(ret.mtf0)
#                                 else:
#                                     results.append(0.0)
#                             mtf_data[axis].append(", ".join(map(str, results)))  # 将四个值合并为字符串
#                 mtf_df=pd.DataFrame(mtf_data,index=cylinders)
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 output_excel_name="mtf_values" + "_" + timestamp + ".xlsx"
#                 output_excel_path=os.path.join(out_path,output_excel_name)
#                 # 保存为 Excel 文件
#                 mtf_df.to_excel(output_excel_path, sheet_name="MTF_Values")
#     except Exception as e:
#         print(e)

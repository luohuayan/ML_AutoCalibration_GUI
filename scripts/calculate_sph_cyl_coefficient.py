import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime
from typing import List
import pandas as pd
import time


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def calculate_sph_cyl_coefficinet(
        colorimeter:mlcm.ML_Colorimeter,
        sph_list:List[float],
        cyl_list:List[float],
        save_path:str,
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        exposure_map_obj:Dict[mlcm.MLFilterEnum,Dict[mlcm.MLFilterEnum,mlcm.pyExposureSetting]]={},
        count:int=10,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    update_status("calculate_sph_cyl_coefficinet start")
    time.sleep(5)
    update_status("calculate_sph_cyl_coefficinet finish")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    module_id = 1
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)

    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")
    
    # exposure = mlcm.pyExposureSetting(
    #     exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=21
    # )
    # ret = ml_mono.ml_set_exposure(exposure)
    # if not ret.success:
    #     raise RuntimeError("ml_set_exposure error")
    
    for nd in nd_list:
        # switch nd filter
        nd_enum = mlcm.MLFilterEnum(int(nd))
        ret = ml_mono.ml_move_nd_syn(nd_enum)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")
        for xyz in xyz_list:
            # switch xyz filter
            xyz_enum = mlcm.MLFilterEnum(int(xyz))
            ret = ml_mono.ml_move_xyz_syn(xyz_enum)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn error")
            ret = ml_mono.ml_set_exposure(exposure_map_obj[nd_enum][xyz_enum])
            if not ret.success:
                raise RuntimeError("ml_set_exposure error")
            sph_results=[]
            cyl_results=[]
            for i in range(count):
                sph_coefficient = {}
                cyl_coefficient = {}
                last_sph = 0
                last_cyl = 0
                for sph in sph_list:
                    rx = mlcm.pyRXCombination(sph=sph, cyl=0, axis=0)
                    ret = ml_mono.ml_set_rx_syn(rx)
                    if not ret.success:
                        raise RuntimeError("ml_set_rx_syn error")

                    ret = ml_mono.ml_capture_image_syn()
                    if not ret.success:
                        raise RuntimeError("ml_capture_image_syn error")

                    img = ml_mono.ml_get_image()
                    cv2.imwrite(
                        save_path + "\\" + mlcm.pyRXCombination_to_str(rx) + ".tif", img
                    )
                    gray = cv2.mean(img[2502:3502, 3460:4460])[0]
                    sph_coefficient[sph]=gray

                    if sph == 0:
                        last_sph = gray
                
                # 格式化结果并添加到results列表中
                formatted_results={sph:format(gray / last_sph, ".3f") for sph,gray in sph_coefficient.items()}
                formatted_results['循环次数']=i+1
                sph_results.append(formatted_results)

                for cyl in cyl_list:
                    rx = mlcm.pyRXCombination(sph=0, cyl=cyl, axis=0)
                    ret = ml_mono.ml_set_rx_syn(rx)
                    if not ret.success:
                        raise RuntimeError("ml_set_rx_syn error")

                    ret = ml_mono.ml_capture_image_syn()
                    if not ret.success:
                        raise RuntimeError("ml_capture_image_syn error")

                    img = ml_mono.ml_get_image()
                    cv2.imwrite(
                        save_path + "\\" + mlcm.pyRXCombination_to_str(rx) + ".tif", img
                    )
                    gray = cv2.mean(img[2502:3502, 3460:4460])[0]
                    cyl_coefficient[cyl]=gray

                    if cyl == 0:
                        last_cyl = gray
                formatted_results={sph:format(gray / last_cyl, ".3f") for sph,gray in cyl_coefficient.items()}
                formatted_results['循环次数']=i+1
                cyl_results.append(formatted_results)
            
            df=pd.DataFrame(sph_results)
            sph_filename = f"sph_{nd_enum.value}_{xyz_enum.value}_{datetime_str()}.xlsx"
            df.to_excel(os.path.join(save_path, sph_filename), index=False)
            df=pd.DataFrame(cyl_results)
            cyl_filename = f"cyl_{nd_enum.value}_{xyz_enum.value}_{datetime_str()}.xlsx"
            df.to_excel(os.path.join(save_path, cyl_filename), index=False)

if __name__ == "__main__":
    eye1_path = r"D:\MLColorimeter\config\EYE1"
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

        calculate_sph_cyl_coefficinet()
    except Exception as e:
        # print(e)
        pass

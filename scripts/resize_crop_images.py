import mlcolorimeter as mlcm
from typing import List
import cv2
import os
from pathlib import Path
import shutil


def resize_crop_images1(image, target_size=(5984, 6000)):
    h, w = image.shape[:2]

    # 计算缩放比例，保持长宽比
    scale = max(target_size[0]/w, target_size[1]/h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # 调整大小
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 计算裁剪区域（居中裁剪）
    start_x = (new_w - target_size[0]) // 2
    start_y = (new_h - target_size[1]) // 2

    # 裁剪
    cropped = resized[start_y:start_y+target_size[1],
                    start_x:start_x+target_size[0]]

    return cropped


def cal_synthetic_mean_images(
    ml_colorimeter:mlcm.MLColorimeter,
    module_id: int,
    save_path: str,
    nd: mlcm.MLFilterEnum,
    xyz: mlcm.MLFilterEnum,
    sphere_list: List[float],
    light_source: str,
    aperture: str
):
    # aperture = ml_colorimeter.ml_get_aperture()

    ml_colorimeter.ml_cal_synthetic_mean_images(
        module_id=module_id,
        save_path=save_path,
        aperture=aperture,
        nd=nd,
        xyz=xyz,
        sphere_list=sphere_list,
        light_source=light_source
    )


def find_tif_files(root_dir):
    tif_files = []

    # 遍历目录树
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.tif')):
                # 获取完整文件路径
                full_path = os.path.join(root, file)
                tif_files.append(full_path)

    return tif_files

def modify_parent_directory(file_path, target_dir, suffix):
    """
    修改指定目录的父目录名称
    
    Args:
        file_path: 完整文件路径
        target_dir: 目标目录名称（如 "EYE1"）
        suffix: 要添加的后缀（如 "_2binn"）
    
    Returns:
        修改后的文件路径
    """
    # 标准化路径分隔符
    normalized_path = os.path.normpath(file_path)
    parts = normalized_path.split(os.sep)
    
    # 查找目标目录的位置
    if target_dir in parts:
        target_index = parts.index(target_dir)
        if target_index > 0:  # 确保有父目录
            # 修改父目录名称
            parts[target_index - 1] = f"{parts[target_index - 1]}{suffix}"
    
    # 重新组合路径
    return os.sep.join(parts)

def copy_files_with_new_parent(src_dir, target_dir_name, suffix):
    """
    复制源目录下所有文件到新的目标目录
    目标目录名称为源目录的父目录添加后缀
    
    Args:
        src_dir: 源目录路径
        target_dir_name: 目标目录名称（如 "EYE1"）
        suffix: 要添加的后缀
    """
    # 构建目标路径
    save_path = src_dir.replace(target_dir_name, f"{target_dir_name}{suffix}")
    
    # 确保目标目录存在
    os.makedirs(save_path, exist_ok=True)
    
    # 复制所有文件
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            src_file = os.path.join(root, file)
            rel_path = os.path.relpath(src_file, src_dir)
            dst_file = os.path.join(save_path, rel_path)
            
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            # (f"已复制: {src_file} -> {dst_file}")
        break
    
    # print(f"\n所有文件已复制到: {save_path}")
    return save_path

def resize_crop_images(
        aperture_list:List[str],
        binning_str_list:List[str],
        light_source_list:List[str],
        target_size_list:List[str],
        nd_list:List[mlcm.MLFilterEnum],
        xyz_list:List[mlcm.MLFilterEnum],
        is_generate_FFC:bool,
        is_calculate_synthetic:bool,
        eye1_path:str,
        ffc_path:str,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    if is_generate_FFC:
        for binning_str in binning_str_list:
            save_path=copy_files_with_new_parent(eye1_path,"config",binning_str)
            for target_size in target_size_list:
                # find and resize images
                file_list = find_tif_files(ffc_path)
                for tif_file in file_list:
                    image = cv2.imread(tif_file, -1)
                    cropped_image = resize_crop_images1(image, target_size)
                    path_obj = Path(tif_file)
                    parts = list(path_obj.parts)
                    ffc_index = None
                    for idx, part in enumerate(parts):
                        if "FFC" in part:  # 关键：用in判断是否包含FFC，而非精准匹配
                            ffc_index = idx
                            parts[ffc_index]="FFC"
                            break
                    if ffc_index is None:
                        update_status(f"原始路径 {tif_file} 中未找到包含FFC的路径段")
                        return

                    ffc_subpath = Path(*parts[ffc_index:])
                    final_path = Path(save_path) / ffc_subpath
                    final_path_str = str(final_path)

                    parent_dir = os.path.dirname(final_path_str)
                    os.makedirs(parent_dir, exist_ok=True)
                    cv2.imwrite(final_path_str, cropped_image)
                    update_status(final_path_str)
        update_status("resize all image finish")
    
    if is_calculate_synthetic:
        for binning_str in binning_str_list:
            save_path=eye1_path.replace("config",f"config{binning_str}")
            # save_path=copy_files_with_new_parent(eye1_path,"config",binning_str)
            path_list = [
                save_path,
            ]
            # create a ML_Colorimeter system instance
            ml_colorimeter = mlcm.ML_Colorimeter()
            # add mono module into ml_colorimeter system, according to path_list create one or more mono module
            ret = ml_colorimeter.ml_add_module(path_list=path_list)
            if not ret.success:
                update_status("ml_add_module error")
                return

            module_id = 1
            ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
            # calculate synthetic images
            sphere_list = [0]
            for aperture in aperture_list:
                for light_source in light_source_list:
                    for nd in nd_list:
                        for xyz in xyz_list:
                            cal_synthetic_mean_images(
                                ml_colorimeter=ml_colorimeter,
                                module_id=module_id,
                                save_path=save_path,
                                nd=nd,
                                xyz=xyz,
                                sphere_list=sphere_list,
                                light_source=light_source,
                                aperture=aperture
                            )
                            update_status("calculate mean images for: " +
                                mlcm.MLFilterEnum_to_str(xyz))
                        update_status("calculate mean images for: " +
                            mlcm.MLFilterEnum_to_str(nd))
                    update_status("calculate mean images for: " + light_source)
        update_status("calculate ffc synthetic mean finish")


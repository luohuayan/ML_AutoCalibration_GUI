
import os
import configparser
import pandas as pd
import json
from PIL import Image
from typing import List


def gather_file_data(base_path, folder_names, config, width=12000, height=12000):
    data = []

    def recursive_search(current_path, folder, folder_rule):
        nonlocal width, height  # 声明使用外部作用域的变量
        for entry in os.listdir(current_path):
            entry_path = os.path.join(current_path, entry)
            if os.path.isdir(entry_path):
                # 递归调用,继续遍历子文件夹
                recursive_search(entry_path, folder, folder_rule)
            elif os.path.isfile(entry_path):
                # if entry.endswith(suffix):
                # 获取所有层级的子文件夹名称
                relative_path = os.path.relpath(entry_path, base_path)
                folder_structure = os.path.dirname(
                    relative_path).split(os.sep)

                # 组装数据，folder_structure[-1] 是当前文件的直接子文件夹名称
                if len(folder_structure) > 0:
                    parent_folder = folder_structure[-1]
                else:
                    parent_folder = ''
                if entry.endswith('.json'):
                    file_content = read_json_content(entry_path)  # 读取JSON文件内容
                    x_offset, y_offset = validate_json_format(folder,
                                                              file_content)
                    if folder == 'ColorShift':
                        value = f"x_offset: {x_offset}, y_offset: {y_offset}"
                    if folder == 'Luminance':
                        value = f"k: {x_offset}, b: {y_offset}"
                    if folder == 'Radiance':
                        value = f"k: {x_offset}, b: {y_offset}"
                    if folder == 'Offset':
                        x_offset, y_offset = validate_json_format_Offset(
                            file_content)
                        value = f"ExposureOffset: {x_offset}, GrayOffset: {y_offset}"
                    if folder == 'FourColor':
                        value = ""
                    if folder == 'Distortion':
                        value = ""
                elif entry.endswith('.tif') or entry.endswith('.tiff'):
                    if folder == 'Dark':
                        try:
                            with Image.open(entry_path) as img:
                                width, height = img.size
                            file_content = f"图像有效, size: {img.size}"
                        except (IOError, SyntaxError) as e:  # type: ignore
                            # 如果发生异常，表示图像损坏，因为是Dark图像损坏，所以程序终止，先修改图像后再重新运行
                            raise RuntimeError(
                                f"File {entry_path} is corrupted. Please fix the image and try again.")
                    else:
                        try:
                            with Image.open(entry_path) as img:  # type: ignore
                                # 检查图像是否为空或损坏
                                img.load()  # 强制加载图像数据以检查是否有效
                                if img.size == (0, 0) or img.getbbox() is None:  # 没有有效像素
                                    file_content = "没有有效像素"
                                elif img.width != width or img.height != height:
                                    file_content = f"图像尺寸与Dark图像不匹配, expected: ({width}, {height}), actual: ({img.width}, {img.height})"
                                else:
                                    file_content = f"图像有效, size: {img.size}"

                        except (IOError, SyntaxError) as e:  # type: ignore
                            # 如果发生异常，记录损坏的图像
                            file_content = "图像损坏"
                    value = ""
                data.append([folder_rule] + folder_structure +
                            [entry] + [file_content] + [value])  # 将文件内容添加到数据中

    # 读取base_path下的json文件
    for entry in os.listdir(base_path):
        entry_path = os.path.join(base_path, entry)
        if os.path.isfile(entry_path) and entry.endswith('.json'):
            file_content = read_json_content(entry_path)
            data.append(['']+[entry]+[file_content])

    data.append(['', '', '', '', ''])

    for folder in folder_names:
        folder_path = os.path.join(base_path, folder)
        if folder in config:
            folder_rule = config[folder].get('Folder_Rule', '').strip()
            recursive_search(folder_path, folder, folder_rule)
            data.append(['', '', '', '', ''])  # 添加空行分隔不同文件夹的数据
        else:
            folder_rule = ''
            recursive_search(folder_path, folder, folder_rule)
    return data


def read_json_content(file_path):
    """读取JSON文件内容并返回其解析后的数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)  # 返回解析后的JSON数据
    except Exception as e:
        return f"Error reading file: file format error"  # 返回错误信息

# 检查json文件中的内容是否符合格式


def validate_json_format(folder_name, data):
    # 检查数据是否为字典，并且包含folder_name键
    if isinstance(data, dict) and folder_name in data:
        folder_name_data = data[folder_name]
        # 检查folder_name键对应的值是否为字典，并且其内部结构复合要求
        if isinstance(folder_name_data, list) and len(folder_name_data) == 1:
            inner_list = folder_name_data[0]  # 获取内部的第一个列表
            if isinstance(inner_list, list) and len(inner_list) == 2:
                value1, value2 = inner_list
                return value1, value2
            else:
                return None, None
        return None, None
    else:
        return None, None


def validate_json_format_Offset(data):
    exposure_offset = data["ExposureOffset"]
    gray_offset = data["GrayOffset"]
    return exposure_offset, gray_offset


def config_detection(
        eye1_path: str,
        out_path: str,
        file_name: str,
        folder_name: List[str],
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    data = []
    width, height = None, None
    os.makedirs(out_path, exist_ok=True)
    file = out_path+"\\"+file_name+".xlsx"
    ini_path = eye1_path+"\\"+"config.ini"
    if not os.path.exists(ini_path):
        raise RuntimeError(f"File {ini_path} no exists.")
    config = configparser.ConfigParser()

    config.read(ini_path, encoding='utf-8')

    # 读取base_path下的json文件
    for entry in os.listdir(eye1_path):
        entry_path = os.path.join(eye1_path, entry)
        if os.path.isfile(entry_path) and entry.endswith('.json'):
            file_content = read_json_content(entry_path)
            data.append(
                ['']+[entry]+[json.dumps(file_content, indent=4, ensure_ascii=False)])
            update_status(f"{entry_path}")

    data.append(['', '', '', '', ''])

    def recursive_search(current_path, folder, folder_rule):
        nonlocal width, height  # 声明使用外部作用域的变量
        for entry in os.listdir(current_path):
            entry_path = os.path.join(current_path, entry)
            if os.path.isdir(entry_path):
                # 递归调用,继续遍历子文件夹
                recursive_search(entry_path, folder, folder_rule)
            elif os.path.isfile(entry_path):
                # if entry.endswith(suffix):
                # 获取所有层级的子文件夹名称
                relative_path = os.path.relpath(entry_path, eye1_path)
                folder_structure = os.path.dirname(
                    relative_path).split(os.sep)

                # 组装数据，folder_structure[-1] 是当前文件的直接子文件夹名称
                if len(folder_structure) > 0:
                    parent_folder = folder_structure[-1]
                else:
                    parent_folder = ''
                if entry.endswith('.json'):
                    file_content = read_json_content(entry_path)  # 读取JSON文件内容
                    x_offset, y_offset = validate_json_format(folder,
                                                              file_content)
                    if folder == 'ColorShift':
                        value = f"x_offset: {x_offset}, y_offset: {y_offset}"
                    if folder == 'Luminance':
                        value = f"k: {x_offset}, b: {y_offset}"
                    if folder == 'Radiance':
                        value = f"k: {x_offset}, b: {y_offset}"
                    if folder == 'Offset':
                        x_offset, y_offset = validate_json_format_Offset(
                            file_content)
                        value = f"ExposureOffset: {x_offset}, GrayOffset: {y_offset}"
                    if folder == 'FourColor':
                        value = ""
                    if folder == 'Distortion':
                        value = ""
                    file_content = json.dumps(
                        file_content, indent=4, ensure_ascii=False)
                elif entry.endswith('.tif') or entry.endswith('.tiff'):
                    if folder == 'Dark':
                        try:
                            with Image.open(entry_path) as img:
                                width, height = img.size
                            file_content = f"图像有效, size: {img.size}"
                        except (IOError, SyntaxError) as e:  # type: ignore
                            # 如果发生异常，表示图像损坏，因为是Dark图像损坏，所以程序终止，先修改图像后再重新运行
                            raise RuntimeError(
                                f"File {entry_path} is corrupted. Please fix the image and try again.")
                    else:
                        try:
                            with Image.open(entry_path) as img:  # type: ignore
                                # 检查图像是否为空或损坏
                                img.load()  # 强制加载图像数据以检查是否有效
                                if img.size == (0, 0) or img.getbbox() is None:  # 没有有效像素
                                    file_content = "没有有效像素"
                                elif img.width != width or img.height != height:
                                    file_content = f"图像尺寸与Dark图像不匹配, expected: ({width}, {height}), actual: ({img.width}, {img.height})"
                                else:
                                    file_content = f"图像有效, size: {img.size}"

                        except (IOError, SyntaxError) as e:  # type: ignore
                            # 如果发生异常，记录损坏的图像
                            file_content = "图像损坏"
                    value = ""
                data.append([folder_rule] + folder_structure +
                            [entry] + [file_content] + [value])  # 将文件内容添加到数据中
                update_status(f"{entry_path}")

    for folder in folder_name:
        folder_path = os.path.join(eye1_path, folder)
        if folder in config:
            folder_rule = config[folder].get('Folder_Rule', '').strip()
            recursive_search(folder_path, folder, folder_rule)
            data.append(['', '', '', '', ''])  # 添加空行分隔不同文件夹的数据
        else:
            folder_rule = ''
            recursive_search(folder_path, folder, folder_rule)
            data.append(['', '', '', '', ''])
    df = pd.DataFrame(data)

    df.to_excel(file, index=False)
    update_status(f"Finish,文件已保存在{file}")

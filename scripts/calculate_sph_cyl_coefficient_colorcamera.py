import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime
from openpyxl import Workbook, load_workbook


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def calculate_sph_cyl_coefficinet(
        colorimeter: mlcm.ML_Colorimeter,
        save_path: str,
        file_name: str,
        nd: mlcm.MLFilterEnum,
        exposure: mlcm.pyExposureSetting,
        avg_count: int,
        sph_list: List[float],
        cyl_list: List[float],
        roi: mlcm.pyCVRect,
        status_callback=None
):
    def update_status(message):
        if status_callback:
            status_callback(message)
    ml_mono = colorimeter.ml_bino_manage.ml_get_module_by_id(1)
    pixel_format = mlcm.MLPixelFormat.MLBayerRG12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    ret = ml_mono.ml_move_nd_syn(nd)
    if not ret.success:
        raise RuntimeError("ml_move_nd_syn error")

    ret = ml_mono.ml_set_exposure(exposure)
    if not ret.success:
        raise RuntimeError("ml_set_exposure error")

    save_xlsx = save_path + "\\" + file_name
    wb = Workbook()
    wb.save(save_xlsx)
    wb = load_workbook(save_xlsx)
    wb.remove(wb["Sheet"])
    title = str("coefficient")
    ws = wb.create_sheet(title=title)
    line = []
    ws.append(line)
    line = []

    for i in range(avg_count):
        sph_coefficient = []
        cyl_coefficient = []
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
            X, Y, Z = cv2.split(img)  # type: ignore
            cv2.imwrite(
                save_path + "\\" +
                mlcm.pyRXCombination_to_str(rx) + ".tif", Y
            )
            gray = cv2.mean(
                Y[roi.y:roi.y+roi.height, roi.x:roi.x+roi.width])[0]
            sph_coefficient.append(gray)

            if sph == 0:
                last_sph = gray
        for i in range(len(sph_coefficient)):
            sph_coefficient[i] = format(sph_coefficient[i] / last_sph, ".3f")
        update_status(f"sph coefficient: {sph_coefficient}")
        line = ["sph_coefficient", *sph_coefficient]
        ws.append(line)
        line = []
        ws.append(line)
        line = []

        for cyl in cyl_list:
            rx = mlcm.pyRXCombination(sph=0, cyl=cyl, axis=0)
            ret = ml_mono.ml_set_rx_syn(rx)
            if not ret.success:
                raise RuntimeError("ml_set_rx_syn error")

            ret = ml_mono.ml_capture_image_syn()
            if not ret.success:
                raise RuntimeError("ml_capture_image_syn error")

            img = ml_mono.ml_get_image()
            X, Y, Z = cv2.split(img)  # type: ignore
            cv2.imwrite(
                save_path + "\\" +
                mlcm.pyRXCombination_to_str(rx) + ".tif", Y
            )
            gray = cv2.mean(
                Y[roi.y:roi.y+roi.height, roi.x:roi.x+roi.width])[0]
            cyl_coefficient.append(gray)

            if cyl == 0:
                last_cyl = gray
        for i in range(len(cyl_coefficient)):
            cyl_coefficient[i] = format(cyl_coefficient[i] / last_cyl, ".3f")
        update_status(f"cyl coefficient: {cyl_coefficient}")
        print(cyl_coefficient)
        line = ["cyl_coefficient", *cyl_coefficient]
        ws.append(line)
        line = []
        ws.append(line)
        line = []

    wb.save(save_xlsx)
    update_status("calculate sph cyl coefficient finish")

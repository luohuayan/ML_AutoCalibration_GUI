import mlcolorimeter as mlcm
from typing import List, Dict
import cv2
import csv
import os
import numpy as np
from datetime import datetime


def datetime_str():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def cross_center_identification():
    pass


if __name__ == "__main__":
    eye1_path = r"I:\duling ffc\EYE1"
    ml_colorimeter = mlcm.ML_Colorimeter()
    path_list = [eye1_path]

    ml_colorimeter.ml_add_module(path_list=path_list)
    ml_colorimeter.ml_connect()

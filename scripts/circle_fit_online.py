import mlcolorimeter as mlcm
import cv2
from typing import List, Dict
import os

"""
    center_fit.py is an example script that shows a simplified way to fit rx cross center with circle.
"""


def circle_fit_online():
    # change color filter according to your image
    xyz_list = [mlcm.MLFilterEnum.X]
    nd_list = [mlcm.MLFilterEnum.ND0]
    # change binning according to your image
    binn = mlcm.Binning.ONE_BY_ONE
    ret = ml_mono.ml_set_binning(binn)
    if not ret.success:
        raise RuntimeError("ml_set_binning error")

    pixel_format = mlcm.MLPixelFormat.MLMono12
    ret = ml_mono.ml_set_pixel_format(pixel_format)
    if not ret.success:
        raise RuntimeError("ml_set_pixel_format error")

    cyl_list = [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0]
    axis_list = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180]
    for nd in nd_list:
        ret = ml_mono.ml_move_nd_syn(nd)
        if not ret.success:
            raise RuntimeError("ml_move_nd_syn error")

        for xyz in xyz_list:
            ret = ml_mono.ml_move_xyz_syn(xyz)
            if not ret.success:
                raise RuntimeError("ml_move_xyz_syn error")

            for cyl in cyl_list:
                for axis in axis_list:
                    rx = mlcm.pyRXCombination(sph=0, cyl=cyl, axis=axis)
                    ret = ml_mono.ml_set_rx_syn(rx)
                    if not ret.success:
                        raise RuntimeError("ml_set_rx_syn error")

                    ml_colorimeter.ml_capture_image_syn()
                    img = ml_colorimeter.ml_get_image()[module_id]

                    # excute circle fit
                    # create circle fit instance
                    ml_center_fit = mlcm.pyMLCenterFit(mlcm.MLCenterFit())

                    # load circle fit config
                    ml_center_fit.ml_load_circleFit_config(circle_fit_file)

                    # excute circle fit, after finish, return the fitted image
                    fitted_img = ml_center_fit.ml_circle_fit(img, rx, xyz, binn)

                    roi_img = fitted_img[3000:4000, 4000:5000]

                    cv2.imwrite(
                        out_path + "\\" + mlcm.pyRXCombination_to_str(rx) + ".tif",
                        roi_img,
                    )
                    print("center fit for: " + mlcm.pyRXCombination_to_str(rx))
            print("center fit for: " + mlcm.MLFilterEnum_to_str(xyz))
        print("center fit for: " + mlcm.MLFilterEnum_to_str(nd))
    print("circle fit finish online")


if __name__ == "__main__":
    # circle fit config
    circle_fit_file = r"D:\projectFile01\aolanduo\aolanduo3_RX_center\CircleFit.json"
    # path to save image after center fit
    out_path = r"D:\projectFile01\aolanduo\aolanduo3_RX_center\ND0_X_fitted"
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    eye1_path = r"I:\duling ffc\EYE1"
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

        circle_fit_online()

    except Exception as e:
        print(e)

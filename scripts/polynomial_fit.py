import mlcolorimeter as mlcm
import cv2
from typing import List, Dict
import os

"""
    ploynomial_fit.py is an example script that shows a simplified way to fit rx cross center with polynomial.
"""


def polynomial_fit():
    # change color filter according to your image
    xyz = mlcm.MLFilterEnum.X
    # change binning according to your image
    binn = mlcm.Binning.ONE_BY_ONE
    # Traverse the image_path to obtain all image file names
    file_list = os.listdir(image_path)
    cyl_list = [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0]
    for i in range(len(file_list) - 1):
        if file_list[i].__contains__(".tif"):
            # change rx info according to your image
            rx_str = file_list[i].split(".tif")[0]
            rx = mlcm.str_to_pyRXCombination(rx_str)
            if cyl_list.__contains__(rx.cyl):
                # read an image to do circle fit
                img = cv2.imread(image_path + "\\" + file_list[i], -1)

                # excute circle fit
                # create circle fit instance
                ml_center_fit = mlcm.pyMLCenterFit(mlcm.MLCenterFit())

                # load circle fit config
                ml_center_fit.ml_load_polynomialFit_config(circle_fit_file)

                # excute circle fit, after finish, return the fitted image
                fitted_img = ml_center_fit.ml_polynomial_fit(img, rx, xyz, binn)

                cv2.imwrite(out_path + "\\" + file_list[i], fitted_img)
                print("polynomial fit for: " + mlcm.pyRXCombination_to_str(rx))
    print("polynomial fit finish")


if __name__ == "__main__":
    # circle fit config
    circle_fit_file = (
        r"D:\projectFile01\aolanduo\aolanduo3_RX_center\PolynomialFit.json"
    )
    # path to read image for center fit
    image_path = r"D:\projectFile01\aolanduo\aolanduo3_RX_center\ND0_X"
    # path to save image after center fit
    out_path = r"D:\projectFile01\aolanduo\aolanduo3_RX_center\ND0_X_fitted"
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    try:
        polynomial_fit()

    except Exception as e:
        print(e)

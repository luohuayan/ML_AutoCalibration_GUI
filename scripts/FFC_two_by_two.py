import cv2
from cv2 import blur
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import csv
import os


def get_FFC(filepath, loop):
    srcX = np.array(Image.open(filepath + str(loop) + '0%_ND0_X_FFC.tif'))
    srcY = np.array(Image.open(filepath + str(loop) + '0%_ND0_Y_FFC.tif'))
    srcZ = np.array(Image.open(filepath + str(loop) + '0%_ND0_Z_FFC.tif'))

    srcX = blur(srcX, (10, 10))
    srcY = blur(srcY, (10, 10))
    srcZ = blur(srcZ, (10, 10))

    return [srcX, srcY, srcZ]


if __name__ == "__main__":
    filepath = "E:/YM2/result2/LANGBO_15mm 2X2/"
    savepath = filepath
    if not os.path.exists(savepath):
        os.makedirs(savepath)
    xyz_list = ["X", "Y", "Z"]

    with open(
            savepath + "\\FFC_2X2.csv",
            "a+",
            newline="",
    ) as f:
        mywriter = csv.writer(f)
        mywriter.writerow(
            ["Gray Value","Color Filter", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Uniformity"]
        )
    vrange = {
        5: (1700, 2200),
        7: (2300, 3000),
        9: (3000, 3900)
    }
    for loop_i in range(5, 11, 2):
        img_list = get_FFC(filepath, loop_i)
        for i in range(len(xyz_list)):
            row, col = img_list[i].shape[0], img_list[i].shape[1]
            center_row, center_col = int(row / 2), int(col / 2)
            half_size = 1800
            fig = plt.figure(figsize=(16, 4))
            plt.subplot(1, 2, 1)
            plt.imshow(img_list[i], cmap="jet", vmin=vrange[loop_i][0], vmax=vrange[loop_i][1])
            plt.xlabel("Col(pixel)")
            plt.ylabel("Row(pixel)")
            plt.colorbar(label="(FFC)")
            plt.title("FFC_2X2 " + xyz_list[i] + " " + str(loop_i) + "0%")
            plt.subplot(1, 2, 2)
            plt.plot(
                img_list[i][center_row, (center_col - half_size) : (center_col + half_size)]
            )
            plt.plot(
                img_list[i][(center_row - half_size) : (center_row + half_size), center_col]
            )
            line = []
            line.append(str(loop_i) + "0%")
            line.append(xyz_list[i])
            roi_list = [
            (1350, 1150),
            (2850, 1150),
            (4150, 1150),
            (1350, 2250),
            (2850, 2250),
            (4150, 2250),
            (1350, 3350),
            (2850, 3350),
            (4150, 3350),
        ]
            gray_list = []
            for x, y in roi_list:
                y1 = int(y - 100)
                y2 = int(y + 100)
                x1 = int(x - 100)
                x2 = int(x + 100)
                roi = img_list[i][y1:y2, x1:x2]
                gray = cv2.mean(roi)[0]
                gray_list.append(gray)
                line.append(gray)

            avg = np.mean(gray_list)
            max = np.max(gray_list)
            min = np.min(gray_list)

            uniformity = 1 - 0.5 * (max - min) / avg
            line.append(uniformity)
            with open(
                savepath + "\\FFC_2X2.csv",
                "a+",
                newline="",
            ) as f:
                mywriter = csv.writer(f)
                mywriter.writerow(line)

            plt.grid(which="both")
            plt.xlabel("Position(pixel)")
            plt.ylabel("gray value")
            plt.ylim([vrange[loop_i][0], vrange[loop_i][1]])
            plt.legend(["Along-Col", "Along-Row"])
            # 显示图形
            # plt.show(block=True)
            # 保存图形
            plt.savefig(
                savepath + "/LANGBO_15mm FFC_2X2 " + str(loop_i) + "0% " + xyz_list[i] + ".png",
                bbox_inches="tight",
            )
            plt.close(fig)

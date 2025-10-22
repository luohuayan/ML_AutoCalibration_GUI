import cv2
from cv2 import blur
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import csv


def get_CIEu_CIEv(filepath, loop):
    srcX = np.array(
        cv2.imread(filepath + "\\" + str(loop) + "0%_ND0_X_Result.tif", -1),
        dtype=float,
    )
    srcY = np.array(
        cv2.imread(filepath + "\\" + str(loop) + "0%_ND0_Y_Result.tif", -1),
        dtype=float,
    )
    srcZ = np.array(
        cv2.imread(filepath + "\\" + str(loop) + "0%_ND0_Z_Result.tif", -1),
        dtype=float,
    )
    row, col = srcX.shape[0], srcX.shape[1]
    center_row, center_col = int(row / 2), int(col / 2)
    half_size = 2100
    srcX = blur(srcX, (15, 15))
    srcY = blur(srcY, (15, 15))
    srcZ = blur(srcZ, (15, 15))
    srcX, srcY, srcZ = srcX / 256, srcY / 256, srcZ / 256
    denominator = srcX + srcY + srcZ
    CIEx = np.divide(
        srcX, denominator, out=np.full_like(srcX, np.nan), where=denominator != 0
    )
    CIEy = np.divide(
        srcY, denominator, out=np.full_like(srcY, np.nan), where=denominator != 0
    )
    sumtemp = -2 * CIEx + 12 * CIEy + 3
    u = 4 * CIEx / sumtemp
    v = 9 * CIEy / sumtemp
    return u, v


if __name__ == "__main__":
    loopt = 9
    filepath = r"E:/YM2/result2/LANGBO_15mm 2X2"
    u0, v0 = get_CIEu_CIEv(filepath, loopt)
    for loop_i in [7, 5]:
        with open(
            filepath
            + "\\JNCD_2X2 ("
            + str(loop_i * 10)
            + "% - "
            + "90%).csv",
            "a+",
            newline="",
        ) as f:
            mywriter = csv.writer(f)
            mywriter.writerow(
                ["ROI", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Uniformity"]
            )
        ui, vi = get_CIEu_CIEv(filepath, loop_i)
        JNCD_i = np.sqrt((ui - u0) ** 2 + (vi - v0) ** 2) / 0.004
        row, col = JNCD_i.shape[0], JNCD_i.shape[1]
        center_row, center_col = int(row / 2), int(col / 2)
        half_size = 1800
        # 沿着Row与Col两个方向绘图
        fig = plt.figure(figsize=(16, 4))
        plt.subplot(1, 2, 1)
        plt.imshow(JNCD_i, cmap="jet", vmin=0, vmax=2)
        plt.xlabel("Col(pixel)")
        plt.ylabel("Row(pixel)")
        plt.colorbar(label="(JNCD)")
        plt.title("JNCD_2X2 (" + str(loop_i * 10) + "% - " + "90%)")
        plt.subplot(1, 2, 2)
        plt.plot(
            JNCD_i[center_row, (center_col - half_size) : (center_col + half_size)]
        )
        plt.plot(
            JNCD_i[(center_row - half_size) : (center_row + half_size), center_col]
        )
        line = [""]
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
            roi = JNCD_i[y1:y2, x1:x2]
            gray = cv2.mean(roi)[0]
            gray_list.append(gray)
            line.append(gray)

        avg = np.mean(gray_list)
        max = np.max(gray_list)
        min = np.min(gray_list)

        uniformity = 1 - 0.5 * (max - min) / avg
        line.append(uniformity)
        with open(
            filepath
            + "\\JNCD_2X2 ("
            + str(loop_i * 10)
            + "% - "
            + "90%).csv",
            "a+",
            newline="",
        ) as f:
            mywriter = csv.writer(f)
            mywriter.writerow(line)

        plt.grid(which="both")
        plt.xlabel("Position(pixel)")
        plt.ylabel("JNCD")
        plt.ylim([0, 2])
        plt.legend(["Along-Col", "Along-Row"])
        # 显示图形
        # plt.show(block=True)
        # 保存图形
        plt.savefig(
            filepath + "\\LANGBO_15mm JNCD_2X2 (" + str(loop_i * 10) + "% - " + "90%).png",
            bbox_inches="tight",
        )
        plt.close(fig)

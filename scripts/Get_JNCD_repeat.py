from cv2 import blur
from PIL import Image
import numpy as np
from pandas import read_csv, DataFrame,concat
import os
import json
import matplotlib.pyplot as plt
import cv2

def get_CIEu_CIEv(srXpath, srYpath, srZpath, blursize):
    srcX = np.array(Image.open(srXpath))
    srcY = np.array(Image.open(srYpath))
    srcZ = np.array(Image.open(srZpath))
    ## 获取mask
    # 二值化处理只保留产品区域
    srcY0 = (srcY).astype(np.uint8)
    _, binary_otsu = cv2.threshold(srcY0, 1, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 连通域标记
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_otsu, connectivity=8)
    # 跳过背景（标签0），找到最大面积区域
    max_label = 1  # 初始化为第一个前景区域
    max_area = stats[max_label, cv2.CC_STAT_AREA]
    for label in range(2, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area > max_area:
            max_area = area
            max_label = label
    # 生成结果（仅保留最大区域）
    mask = np.where(labels == max_label, 255, 0).astype(np.uint8)
    mask = mask.astype(bool)
    srcX[~mask] = 0
    srcY[~mask] = 0
    srcZ[~mask] = 0
    srcX = blur(srcX, (blursize, blursize))
    srcY = blur(srcY, (blursize, blursize))
    srcZ = blur(srcZ, (blursize, blursize))
    denominator = srcX + srcY + srcZ
    CIEx= np.divide(srcX, denominator, out=np.full_like(srcX, np.nan), where=denominator != 0)
    CIEy = np.divide(srcY, denominator, out=np.full_like(srcY, np.nan), where=denominator != 0)
    sumtemp = -2 * CIEx + 12 * CIEy +3
    u = 4 * CIEx/sumtemp
    v = 9 * CIEy/sumtemp
    return u, v

if __name__=='__main__':
    rootpath = r'E:\CPYZ\M_06\color'
    savepath = rootpath + '/'
    blursize = 5
    ## 参考数据
    srXpath0 = os.path.join(rootpath, str(1), 'resultX.tif')
    srYpath0 = os.path.join(rootpath, str(1), 'resultY.tif')
    srZpath0 = os.path.join(rootpath, str(1), 'resultZ.tif')
    u0, v0 = get_CIEu_CIEv(srXpath0, srYpath0, srZpath0, blursize)
    for loop_i in range(1, 5):
        print(loop_i)
        srXpathi = os.path.join(rootpath, str(loop_i), 'resultX.tif')
        srYpathi = os.path.join(rootpath, str(loop_i), 'resultY.tif')
        srZpathi = os.path.join(rootpath, str(loop_i), 'resultZ.tif')
        ui, vi = get_CIEu_CIEv(srXpathi, srYpathi, srZpathi, blursize)
        JNCD_i = np.sqrt((ui - u0) ** 2 + (vi - v0) ** 2) / 0.004
        row, col = JNCD_i.shape[0], JNCD_i.shape[1]
        center_row, center_col = int(row / 2), int(col / 2)
        half_size = 1150
        # 沿着Row与Col两个方向绘图
        fig = plt.figure(figsize=(16, 4))
        plt.subplot(1, 2, 1)
        plt.imshow(JNCD_i, cmap='jet', vmin=0, vmax=0.5)
        plt.xlabel('Col(pixel)')
        plt.ylabel('Row(pixel)')
        plt.colorbar(label="(JNCD)")
        # 计算统计值
        mean_val = np.nanmean(JNCD_i)
        p95_val = np.nanpercentile(JNCD_i, 95)
        stats_text = (f"Mean: {mean_val:.4f}\n"
                      f"P95: {p95_val:.4f}")
        plt.text(20, 80, stats_text, color='white', fontsize=8,
                 bbox=dict(facecolor='black', alpha=0.5))

        plt.title('JNCD_' + '(loop' + str(loop_i) + '-loop1)')
        plt.subplot(1, 2, 2)
        Along_col = JNCD_i[center_row, (center_col - half_size): (center_col + half_size)]
        Along_row = JNCD_i[(center_row - half_size): (center_row + half_size), center_col]
        plt.plot(Along_col)
        plt.plot(Along_row)
        plt.grid(which='both')
        plt.xlabel('Position(pixel)')
        plt.ylabel('JNCD')
        plt.ylim([0, 0.5])
        plt.legend(['Along-Col', 'Along-Row'])
        # 显示图形
        # plt.show(block=True)
        # 保存图形
        plt.savefig(savepath + 'JNCD_' + 'loop' + str(loop_i) + '-loop1_blur_'+ str(blursize) + '.png', bbox_inches='tight')
        plt.close(fig)

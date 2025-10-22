'计算重复测试中的亮度波动水平、色坐标波动水平'
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
    return u, v, CIEx, CIEy, srcX, srcY, srcZ

if __name__=='__main__':
    rootpath = r'E:\CPYZ\M_06\color'
    savepath = rootpath + '/'
    blursize = 5

    lvshowmax = 0.5
    CIEshowmax = 0.002

    ciex_list = []
    ciey_list = []
    srcy_list = []
    ## 0-亮度波动水平计算
    for loop_i in range(1, 5):
        print(loop_i)
        srXpathi = os.path.join(rootpath, str(loop_i), 'resultX.tif')
        srYpathi = os.path.join(rootpath, str(loop_i), 'resultY.tif')
        srZpathi = os.path.join(rootpath, str(loop_i), 'resultZ.tif')
        ui, vi, CIExi, CIEyi, srcXi, srcYi, srcZi = get_CIEu_CIEv(srXpathi, srYpathi, srZpathi, blursize)
        row, col = ui.shape[0], ui.shape[1]
        center_row, center_col = int(row / 2), int(col / 2)
        half_size = 1150
        ciex_list.append(CIExi)
        ciey_list.append(CIEyi)
        srcy_list.append(srcYi)
    # 转换为三维矩阵 (shape: [循环次数, 高度, 宽度])
    ciex_3d = np.stack(ciex_list, axis=0)
    ciey_3d = np.stack(ciey_list, axis=0)
    srcy_3d = np.stack(srcy_list, axis=0)
    # 计算第三维(axis=0)的最大/最小/均值
    ciex_max = np.max(ciex_3d, axis=0)
    ciex_min = np.min(ciex_3d, axis=0)
    ciey_max = np.max(ciey_3d, axis=0)
    ciey_min = np.min(ciey_3d, axis=0)
    srcy_max = np.max(srcy_3d, axis=0)
    srcy_min = np.min(srcy_3d, axis=0)
    srcy_mean = np.mean(srcy_3d, axis=0)

    lv_repeat = (srcy_max - srcy_min) / srcy_mean
    lv_repeat = lv_repeat * 100
    CIEx_repeat = (ciex_max - ciex_min)
    CIEy_repeat = (ciey_max - ciey_min)
    ## 绘图01：Lv fluctuation
    fig = plt.figure(figsize=(16, 18))
    plt.subplot(3, 2, 1)
    plt.imshow(lv_repeat, cmap='jet', vmin=0, vmax=lvshowmax)
    plt.xlabel('Col(pixel)')
    plt.ylabel('Row(pixel)')
    plt.colorbar(label="(max-min)/avg (%)")
    mean_val = np.nanmean(lv_repeat)
    p95_val = np.nanpercentile(lv_repeat, 95)
    stats_text = (f"Mean: {mean_val:.4f} %\n"
                  f"P95: {p95_val:.4f} %")
    plt.text(20, 80, stats_text, color='white', fontsize=8,
             bbox=dict(facecolor='black', alpha=0.5))
    plt.title('Lv fluctuation')
    plt.subplot(3, 2, 2)
    Along_col = lv_repeat[center_row, (center_col - half_size): (center_col + half_size)]
    Along_row = lv_repeat[(center_row - half_size): (center_row + half_size), center_col]
    plt.plot(Along_col)
    plt.plot(Along_row)
    plt.grid(which='both')
    plt.xlabel('Position(pixel)')
    plt.ylabel('(max-min)/avg (%)')
    plt.ylim([0, lvshowmax])
    plt.title('Lv fluctuation')
    plt.legend(['Along-Col', 'Along-Row'])
    ## 绘图02：CIEx fluctuation
    plt.subplot(3, 2, 3)
    plt.imshow(CIEx_repeat, cmap='jet', vmin=0, vmax=CIEshowmax)
    plt.xlabel('Col(pixel)')
    plt.ylabel('Row(pixel)')
    plt.colorbar(label="(max-min)")
    mean_val = np.nanmean(CIEx_repeat)
    p95_val = np.nanpercentile(CIEx_repeat, 95)
    stats_text = (f"Mean: {mean_val:.4f}\n"
                  f"P95: {p95_val:.4f}")
    plt.text(20, 80, stats_text, color='white', fontsize=8,
             bbox=dict(facecolor='black', alpha=0.5))
    plt.title('CIEx fluctuation')
    plt.subplot(3, 2, 4)
    Along_col = CIEx_repeat[center_row, (center_col - half_size): (center_col + half_size)]
    Along_row = CIEx_repeat[(center_row - half_size): (center_row + half_size), center_col]
    plt.plot(Along_col)
    plt.plot(Along_row)
    plt.grid(which='both')
    plt.xlabel('Position(pixel)')
    plt.ylabel('(max-min)')
    plt.ylim([0, CIEshowmax])
    plt.title('CIEx fluctuation')
    plt.legend(['Along-Col', 'Along-Row'])

    ## 绘图03：CIEy fluctuation
    plt.subplot(3, 2, 5)
    plt.imshow(CIEy_repeat, cmap='jet', vmin=0, vmax=CIEshowmax)
    plt.xlabel('Col(pixel)')
    plt.ylabel('Row(pixel)')
    plt.colorbar(label="(max-min)")
    mean_val = np.nanmean(CIEy_repeat)
    p95_val = np.nanpercentile(CIEy_repeat, 95)
    stats_text = (f"Mean: {mean_val:.4f}\n"
                  f"P95: {p95_val:.4f}")
    plt.text(20, 80, stats_text, color='white', fontsize=8,
             bbox=dict(facecolor='black', alpha=0.5))
    plt.title('CIEy fluctuation')
    plt.subplot(3, 2, 6)
    Along_col = CIEy_repeat[center_row, (center_col - half_size): (center_col + half_size)]
    Along_row = CIEy_repeat[(center_row - half_size): (center_row + half_size), center_col]
    plt.plot(Along_col)
    plt.plot(Along_row)
    plt.grid(which='both')
    plt.xlabel('Position(pixel)')
    plt.ylabel('(max-min)')
    plt.ylim([0, CIEshowmax])
    plt.title('CIEy fluctuation')
    plt.legend(['Along-Col', 'Along-Row'])

    pngname = 'Lv_JNCD_fluctuation_blur_' + str(blursize) + '.png'
    plt.savefig(savepath + pngname, bbox_inches='tight')
    plt.close(fig)









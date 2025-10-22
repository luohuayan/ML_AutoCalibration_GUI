import mlcolorimeter as mlcm
import integratingSphere.IS_integratingsphere as isphere
from typing import List, Dict
import numpy as np
import os
import cv2

if __name__ == "__main__":
    # set mono module calibration configuration path
    eye1_path = r"E:\TEST\M25393S103MM\EYE1"
    
    # 积分球固定ip和port，运行脚本前需要先打开积分球软件，并且设置好当前的亮度，以及亮度值（最大值）
    ip = "127.0.0.1"
    port = 3434
    # 设置好亮度值后更改nindex为对应的光源
    nindex=-1 # 这里的-1表示None，0表示R，1表示G，2表示B，12表示W
    # 固定曝光时间
    ET=100
    out_path=r"D:\Output\capture_image_fixedET" + "\\" + str(ET)
    os.makedirs(out_path, exist_ok=True)
    path_list = [
        eye1_path,
    ]
    try:
        # create a ML_Colorimeter system instance
        ml_colorimeter = mlcm.ML_Colorimeter()
        # 积分球
        IS = isphere.IS_IntegratingSphere()
        
        # connect
        temp = IS.connect(ip, port)
        if not temp:
            raise RuntimeError("sphere connect error")

        # add mono module into ml_colorimeter system, according to path_list create one or more mono module
        ret = ml_colorimeter.ml_add_module(path_list=path_list)
        if not ret.success:
            raise RuntimeError("ml_add_module error")
        # connect all module in the ml_colorimeter system
        ret = ml_colorimeter.ml_connect()
        if not ret.success:
            raise RuntimeError("ml_connect error")

        # module_id from the ModuleConfig.json
        module_id = 1
        ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
        # path to save ffc images
        save_path = eye1_path

        exposure=mlcm.pyExposureSetting(exposure_mode=mlcm.ExposureMode.Fixed, exposure_time=ET)

        # set pixel format to MLMono12 for capture
        ret = ml_mono.ml_set_pixel_format(pixel_format=mlcm.MLPixelFormat.MLMono12)
        if not ret.success:
            raise RuntimeError("ml_set_pixel_format error")
        
        # camera binning selector
        binn_selector = mlcm.BinningSelector.Logic
        # camera binning，ONE_BY_ONE，TWO_BY_TWO，FOUR_BY_FOUR，EIGHT_BY_EIGHT，SIXTEEN_BY_SIXTEEN
        binn = mlcm.Binning.ONE_BY_ONE
        # camera binning mode
        binn_mode = mlcm.BinningMode.AVERAGE

        ret = ml_mono.ml_set_binning_selector(binn_selector)
        if not ret.success:
            raise RuntimeError("ml_set_binning_selector error")

        ret = ml_mono.ml_set_binning(binn)
        if not ret.success:
            raise RuntimeError("ml_set_binning error")

        # Set binning mode for camera.
        ret = ml_mono.ml_set_binning_mode(binn_mode)
        if not ret.success:
            raise RuntimeError("ml_set_binning_mode error")
        
        # nd filter list to switch during capture
        nd_list = [mlcm.MLFilterEnum.ND0]
        # xyz filter list to switch during capture
        xyz_list = [
            mlcm.MLFilterEnum.Clear,
            mlcm.MLFilterEnum.X,
            mlcm.MLFilterEnum.Y,
            mlcm.MLFilterEnum.Z,
        ]

        # 获取当前积分球设定好亮度后的fscale值
        ret=IS.queryCurrentSolution()
        if not ret.success:
            raise RuntimeError("sphere queryCurrentSolution error")
        fscale_current = float(ret.message)
        print(f"Current IS fscale is {fscale_current}")

        # 将获取到的fscale值按0到fscale_current的范围，均匀分成10份，最小值为0，最大值为fscale_current
        # 使用 np.linspace 生成从 0 到 fscale_current 的 10 个均匀分布的值
        fscale_list = np.linspace(0, fscale_current, num=10).tolist()
        for nd in nd_list:
            # move nd filter
            ret = ml_mono.ml_move_nd_syn(nd)
            if not ret.success:
                raise RuntimeError("ml_move_nd_syn error")
            for xyz in xyz_list:
                # move xyz filter
                ret = ml_mono.ml_move_xyz_syn(xyz)
                if not ret.success:
                    raise RuntimeError("ml_move_xyz_syn error")
                print(f"nd filter: {nd}, color filter: {xyz}")
                ml_mono.ml_set_exposure(exposure=exposure)
                for fscale in fscale_list:
                    print(f"fscale value: {fscale}")
                    # 设定fscale值
                    ret=IS.switchSolution(nindex=nindex, fscale=fscale)
                    if not ret.success:
                        raise RuntimeError("sphere switchSolution error")
                    # 获取当前fscale下对应的亮度值
                    ret=IS.getISBrightness()
                    if not ret.success:
                        raise RuntimeError("sphere getISBrightness error")
                    lumi = float(ret.message)
                    print(f"Current IS Brightness is {lumi}")
                    # capture single image from camera
                    ml_mono.ml_capture_image_syn()
                    img = ml_mono.ml_get_image()
                    img_name = f"ND{nd}_XYZ{xyz}_Light{nindex}_fscale{fscale:.2f}_Lumi{lumi:.2f}.tiff"
                    img_path = os.path.join(out_path, img_name)
                    cv2.imwrite(img_path, img)

    except Exception as e:
        print(e)

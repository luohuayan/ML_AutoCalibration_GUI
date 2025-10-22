import mlcolorimeter as mlcm
import integratingSphere.IS_integratingsphere as isphere
from typing import List, Dict

"""
    capture_ffc_image.py is an example script that shows a simplified way to capture flat filed images 
        for SDK calibration config.
"""


def capture_ffc_image(
    module_id: int,
    save_path: str,
    nd: mlcm.MLFilterEnum,
    xyz_list: List = [
        mlcm.MLFilterEnum.X,
        mlcm.MLFilterEnum.Y,
        mlcm.MLFilterEnum.Z,
    ],
    rx: mlcm.pyRXCombination = mlcm.pyRXCombination(),
    avg_count: int = 5,
    exposure_map: Dict[mlcm.MLFilterEnum, mlcm.pyExposureSetting] = {
        mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(),
        mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(),
        mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(),
    },
):
    # capture ffc images
    ret = ml_colorimeter.ml_capture_ffc2(
        module_id=module_id,
        save_path=save_path,
        nd=nd,
        xyz_list=xyz_list,
        rx=rx,
        avg_count=avg_count,
        exposure_map=exposure_map,
    )
    if not ret.success:
        raise RuntimeError("ml_capture_ffc2 error")


def cal_synthetic_mean_images(
    module_id: int,
    save_path: str,
    nd: mlcm.MLFilterEnum,
    xyz: mlcm.MLFilterEnum,
    sphere_list: List[float],
    light_source: str,
):
    ret = ml_colorimeter.ml_cal_synthetic_mean_images(
        module_id=module_id,
        save_path=save_path,
        aperture=ml_mono.ml_get_aperture(),
        nd=nd,
        xyz=xyz,
        sphere_list=sphere_list,
        light_source=light_source,
    )
    if not ret.success:
        raise RuntimeError("ml_cal_synthetic_mean_images error")


if __name__ == "__main__":
    # set mono module calibration configuration path
    eye1_path = r"E:\TEST\M25393S103MM\EYE1"
    # 积分球固定ip和port，运行脚本前需要先打开积分球软件
    ip = "127.0.0.1"
    port = 3434
    # 光源列表，12-W, 0-R, 1-G, 2-B,0.1-0.4对应fscale即强度，根据需要设定,范围为0-1
    light_index_fscale = {
        12: 0.1,
        0: 0.2,
        1: 0.3,
        2: 0.4,
    }
    light_source_mapping = {
        12: "W",
        0: "R",
        1: "G",
        2: "B",
    }
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

        # nd filter list to switch during capture
        nd_list = [mlcm.MLFilterEnum.ND0]
        # xyz filter list to switch during capture
        xyz_list = [
            mlcm.MLFilterEnum.Clear,
            mlcm.MLFilterEnum.X,
            mlcm.MLFilterEnum.Y,
            mlcm.MLFilterEnum.Z,
        ]
        # exposure map of color filter during capture
        exposure_map = {
            mlcm.MLFilterEnum.X: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Auto, exposure_time=1000
            ),
            mlcm.MLFilterEnum.Y: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Auto, exposure_time=1000
            ),
            mlcm.MLFilterEnum.Z: mlcm.pyExposureSetting(
                exposure_mode=mlcm.ExposureMode.Auto, exposure_time=1000
            ),
        }
        # count to capture and calculate for one image
        avg_count = 5

        # set pixel format to MLMono12 for capture
        ret = ml_mono.ml_set_pixel_format(pixel_format=mlcm.MLPixelFormat.MLMono12)
        if not ret.success:
            raise RuntimeError("ml_set_pixel_format error")
        
        # camera binning selector
        binn_selector = mlcm.BinningSelector.Logic
        # camera binning，ONE_BY_ONE，TWO_BY_TWO，FOUR_BY_FOUR，EIGHT_BY_EIGHT，SIXTEEN_BY_SIXTEEN
        binn = mlcm.Binning.TWO_BY_TWO
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

        # switch light source by interface
        for index, fscale in light_index_fscale.items():
            ret = IS.switchSolution(nindex=index, fscale=fscale)
            if not ret.success:
                raise RuntimeError("sphere switchSolution error")
            # light source setting
            light_source = light_source_mapping[index]
            ml_mono.ml_set_light_source(light_source)

            for nd in nd_list:
                # move nd filter
                ret = ml_mono.ml_move_nd_syn(nd)
                if not ret.success:
                    raise RuntimeError("ml_move_nd_syn error")
                # sph list to set, should match EYE1/config.ini [FFC] Sphere_Mapping
                for sph in [0]:
                # for sph in [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4]:
                    # cylinder set to 0
                    for cyl in [0]:
                        # axis set to 0
                        for axis in [0]:
                            rx = mlcm.pyRXCombination(sph=sph, cyl=cyl, axis=axis)

                            # if want to capture different light source images for ffc, uncomment this line
                            # ml_colorimeter.ml_set_light_source('R')
                            # light source for 'R' 'G' 'B' 'W'
                            # defaulte use "W" light source
                            capture_ffc_image(
                                module_id=module_id,
                                save_path=save_path,
                                nd=nd,
                                xyz_list=xyz_list,
                                rx=rx,
                                avg_count=avg_count,
                                exposure_map=exposure_map,
                            )
                            print("capture sphere image: " + str(sph) + "d")

                # capture spherical 0d for all cylindrical and axis
                # set sphere to 0
                # for sph in [0]:
                #     # cylinder list to set, should match EYE1/config.ini [FFC] Cylinder_Mapping
                #     for cyl in [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0]:
                #         # axis list to set, should match EYE1/config.ini [FFC] Axis_Mapping
                #         for axis in [
                #             0,
                #             15,
                #             30,
                #             45,
                #             60,
                #             75,
                #             90,
                #             105,
                #             120,
                #             135,
                #             150,
                #             165,
                #         ]:
                #             rx = mlcm.pyRXCombination(sph, cyl, axis)

                #             # capture ffc image for each module in id list
                #             # for id in id_list:
                #             # if want to capture different light source images for ffc, uncomment this line
                #             # ml_colorimeter.ml_set_light_source('R') # light source for 'R' 'G' 'B' 'W'
                #             capture_ffc_image(
                #                 module_id=module_id,
                #                 save_path=save_path,
                #                 nd=nd,
                #                 xyz_list=xyz_list,
                #                 rx=rx,
                #                 avg_count=avg_count,
                #                 exposure_map=exposure_map,
                #             )
                #             print(
                #                 "capture cylinder image: "
                #                 + mlcm.pyRXCombination_to_str(rx)
                #             )

                # print("capture ffc finish for " + mlcm.MLFilterEnum_to_str(nd))

            # for nd in nd_list:
            #     sphere_list = [0]
            #     for xyz in xyz_list:
            #         cal_synthetic_mean_images(
            #             module_id=module_id,
            #             save_path=save_path,
            #             nd=nd,
            #             xyz=xyz,
            #             sphere_list=sphere_list,
            #             light_source=ml_mono.ml_get_light_source(),
            #         )
            #     print(
            #         "calculate ffc synthetic mean finish for "
            #         + mlcm.MLFilterEnum_to_str(nd)
            #     )
            # print("capture all image finish")
    
    except Exception as e:
        print(e)

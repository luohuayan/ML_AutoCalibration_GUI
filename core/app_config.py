import mlcolorimeter as mlcm


class AppConfig:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.colorimeter = mlcm.ML_Colorimeter()  # 初始化色度计对象
            # cls._instance.cylaxis=mtfca.MTF_cylaxis() # 初始化
        return cls._instance

    @classmethod
    def get_colorimeter(cls) -> mlcm.ML_Colorimeter:
        return cls().colorimeter

    @classmethod
    def delete_instance(cls):
        if cls._instance is not None:
            ret = None
            ret = AppConfig.get_colorimeter().ml_bino_manage.ml_disconnect_modules()
            if not ret.success:
                return ret.success
            id_list = AppConfig.get_colorimeter().ml_bino_manage.ml_get_modules_id_list()
            for i in id_list:
                ret = AppConfig.get_colorimeter().ml_bino_manage.ml_remove_module(i)
                if not ret.success:
                    return ret.success
            cls._instance = None
            return True
    # @classmethod
    # def get_cylaxis(cls) -> mtfca.MTF_cylaxis:
    #     return cls().cylaxis

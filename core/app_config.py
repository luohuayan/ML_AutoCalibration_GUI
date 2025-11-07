import mlcolorimeter as mlcm
import cylaxismtf.MTF_cylaxis as mtfca

class AppConfig:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.colorimeter = mlcm.ML_Colorimeter()  # 初始化色度计对象
            cls._instance.cylaxis=mtfca.MTF_cylaxis() # 初始化
        return cls._instance

    @classmethod
    def get_colorimeter(cls) -> mlcm.ML_Colorimeter:
        return cls().colorimeter
    
    @classmethod
    def get_cylaxis(cls) -> mtfca.MTF_cylaxis:
        return cls().cylaxis
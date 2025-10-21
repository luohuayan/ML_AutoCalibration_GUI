import mlcolorimeter as mlcm

class AppConfig:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.colorimeter = mlcm.ML_Colorimeter()  # 初始化色度计对象
        return cls._instance

    @classmethod
    def get_colorimeter(cls) -> mlcm.ML_Colorimeter:
        return cls().colorimeter
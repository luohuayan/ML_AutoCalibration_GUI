import serial
import logging
import os
import mlcolorimeter as mlcm
import cv2
import struct
import time

__all__ = ["serial_daogui"]


class serial_daogui:
    def __init__(
        self,
        port: str,
        total_pulse:int,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = serial.PARITY_EVEN,
        stopbits: int = 1,
        station: int = 0x05,
    ):
        self.myserial = serial.Serial(
            port,
            baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=1,
        )
        self.station = station
        self.total_pulse = total_pulse
        logging.info(f"Connected to {port} at {baudrate} baud.")
        self.srv_on()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.srv_off()

    def is_connected(self) -> bool:
        """
        Check if the serial connection is open.

        :param ser: The serial connection object.
        :return: True if connected, False otherwise.
        """
        if self.myserial is not None and self.myserial.is_open:
            logging.info("Serial connection is open.")
            return True
        return False
    
    def disconnect(self) -> bool:
        if self.myserial is not None and self.myserial.is_open:
            self.myserial.close()
            return True
        return False

    def calculate_crc(self, data):
        crc = 0xFFFF
        for byte in data:
            crc = crc ^ byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        # 调整CRC为低位在前，高位在后
        return (crc << 8) & 0xFF00 | (crc >> 8) & 0xFF

    def check_serial(self):
        """
        检查串口。
        :param station_address: 设备站地址。
        :return: True if connected, False otherwise.
        """
        data = struct.pack(">B", self.station)
        for byte in [0x06, 0x44, 0x14, 0x00, 0x00]:
            data += struct.pack(">B", byte)
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)
        logging.info(f"Sent check command to station address: {self.station}")
        print(f"Sent check command to station address: {self.station}")

    def stb_on(self):
        data = struct.pack(">B", self.station)
        for byte in [0x05, 0x01, 0x20, 0xFF, 0x00]:
            data += struct.pack(">B", byte)
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)
        logging.info(f"Sent STBON command for home at station address: {self.station}")
        print(f"Sent STBON command for home at station address: {self.station}")
        time.sleep(0.1)  # 等待一段时间，确保指令发送完成
        # data = b''  # 清空数据
        read_data = self.myserial.read(8)
        return read_data

    def stb_off(self):
        # STBOff
        data = struct.pack(">B", self.station)
        for byte in [0x05, 0x01, 0x20, 0x00, 0x00]:
            data += struct.pack(">B", byte)
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)
        logging.info(f"Sent STBOFF command for home at station address: {self.station}")
        print(f"Sent STBOFF command for home at station address: {self.station}")
        time.sleep(0.1)  # 等待一段时间，确保指令发送完成
        # data = b''  # 清空数据
        read_data = self.myserial.read(8)
        return read_data

    def srv_on(self):
        """
        SRVON
        :param station_address: 设备站地址。
        """
        if self.is_connected():
            # 使能开启
            data = struct.pack(">B", self.station)
            for byte in [0x05, 0x00, 0x60, 0xFF, 0x00]:
                data += struct.pack(">B", byte)
            crc = self.calculate_crc(data)
            data += struct.pack(">H", crc)
            self.myserial.write(data)
            data_list = list(data)
            print(data_list)
            response = self.myserial.read(8)
            logging.info(f"Sent home command to station address: {self.station}")
            print(f"Sent home command to station address: {self.station}")
            read_data = self.myserial.read(8)

    def srv_off(self):
        """
        SRVOFF
        :param station_address: 设备站地址。
        """
        if self.is_connected():
            # 使能开启
            data = struct.pack(">B", self.station)
            for byte in [0x05, 0x00, 0x60, 0x00, 0x00]:
                data += struct.pack(">B", byte)
            crc = self.calculate_crc(data)
            data += struct.pack(">H", crc)
            self.myserial.write(data)
            data_list = list(data)
            print(data_list)
            response = self.myserial.read(8)
            logging.info(f"Sent home command to station address: {self.station}")
            print(f"Sent home command to station address: {self.station}")
            read_data = self.myserial.read(8)

    def query_status(self, data):
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)
        logging.info(
            f"Sent is_moving command for home at station address: {self.station}"
        )
        print(f"Sent is_moving command for home at station address: {self.station}")
        time.sleep(0.1)  # 等待一段时间，确保指令发送完成
        data = b""  # 清空数据
        response = self.myserial.read(8)  # 读取响应
        logging.info(f"Checked moving status for station address: {self.station}")
        response_list = list(response)
        temp = response_list[3]
        if response:
            return temp
        else:
            return False

    def is_moving(self):
        data = struct.pack(">B", self.station)
        for byte in [0x01, 0x01, 0x40, 0x00, 0x01]:
            data += struct.pack(">B", byte)
        return self.query_status(data)

    def is_alarm(self):
        data = struct.pack(">B", self.station)
        for byte in [0x01, 0x01, 0xA1, 0x00, 0x01]:
            data += struct.pack(">B", byte)
        return self.query_status(data)

    def is_home_complete(self):
        if self.is_connected():
            data = struct.pack(">B", self.station)
            for byte in [0x01, 0x01, 0xA2, 0x00, 0x01]:
                data += struct.pack(">B", byte)
            rt = self.query_status(data)
            if not rt:
                return False

            data2 = struct.pack(">B", self.station)
            for byte in [0x01, 0x01, 0x41, 0x00, 0x01]:
                data2 += struct.pack(">B", byte)
            rt = self.query_status(data2)
            if not rt:
                return False
            return True
        else:
            return False

    def wait_for_stop(self, timeout=10):
        count = 1
        if self.is_connected():
            while self.is_moving():
                time.sleep(0.1)
                count = count + 1
                if count > (timeout * 10):
                    logging.warn(f"time out: {self.station}")
                    return False
            return True
        else:
            return False

    def home(self):
        """
        发送home指令。
        :param station_address: 设备站地址。
        """
        if self.is_home_complete():
            return True
        # 选择block
        data = struct.pack(">B", self.station)
        for byte in [0x06, 0x44, 0x14, 0x00, 0x0F]:
            data += struct.pack(">B", byte)
        self.select_bock(data)
        logging.info(
            f"Selected block for home command at station address: {self.station}"
        )
        print(f"Selected block for home command at station address: {self.station}")
        time.sleep(3)  # 等待一段时间，确保指令发送完成

        data = b""  # 清空数据

        self.stb_on()
        self.stb_off()
        self.wait_for_stop()

        if not self.is_home_complete():
            return False
        else:
            return True

    def select_bock(self, data):
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)

    def num_to_hex_bytes(self, num):
        """
        将数字转换为指定字节数的16进制字节数组。

        """
        hex_str = format(num, "08x")  # 转换为16进制字符串
        # 将十六进制字符串分割为两个字节
        bytes_list = [hex_str[i : i + 2] for i in range(0, len(hex_str), 2)]
        # 这里手动调整顺序
        ordered_bytes = [bytes_list[2], bytes_list[3], bytes_list[0], bytes_list[1]]
        # 将字节顺序反转，并转换为字节对象
        bytes_obj = bytes.fromhex(" ".join(ordered_bytes))
        return bytes_obj

    def move_254(self):
        """
        发送home指令。
        :param station_address: 设备站地址。
        """
        # 选择block
        data = struct.pack(">B", self.station)
        for byte in [0x06, 0x44, 0x14, 0x00, 0xFE]:
            data += struct.pack(">B", byte)
        self.select_bock(data)
        logging.info(
            f"Selected block for home command at station address: {self.station}"
        )
        print(f"Selected block for home command at station address: {self.station}")
        time.sleep(3)  # 等待一段时间，确保指令发送完成

        data = b""  # 清空数据

        self.stb_on()
        self.stb_off()
        self.wait_for_stop()

        return True

    def move_255(self):
        """
        发送home指令。
        :param station_address: 设备站地址。
        """
        # 选择block
        data = struct.pack(">B", self.station)
        for byte in [0x06, 0x44, 0x14, 0x00, 0xFF]:
            data += struct.pack(">B", byte)
        self.select_bock(data)
        logging.info(
            f"Selected block for home command at station address: {self.station}"
        )
        print(f"Selected block for home command at station address: {self.station}")
        time.sleep(3)  # 等待一段时间，确保指令发送完成

        data = b""  # 清空数据

        self.stb_on()
        self.stb_off()
        self.wait_for_stop()

        return True

    def move_pulse(self, pulse: int):
        logging.info(f"Start Moving rail to target position: {pulse}")
        # 将接收的目标位置转换为16进制，并且是32个字节
        target_position_hex = self.num_to_hex_bytes(pulse)
        # 1、向block254发送绝对位置指令
        data = struct.pack(">B", self.station)
        for byte in [0x10, 0x48, 0x02, 0x00, 0x02, 0x04]:
            data += struct.pack(">B", byte)
        for byte in target_position_hex:
            data += struct.pack(">B", byte)
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)
        time.sleep(0.2)
        data = b""  # 清空数据

        # 选择block
        data = struct.pack(">B", self.station)
        for byte in [0x06, 0x44, 0x14, 0x00, 0x00]:
            data += struct.pack(">B", byte)
        self.select_bock(data)
        logging.info(
            f"Selected block for home command at station address: {self.station}"
        )
        print(f"Selected block for home command at station address: {self.station}")
        time.sleep(0.2)  # 等待一段时间，确保指令发送完成

        # data = b''  # 清空数据

        self.stb_on()
        self.stb_off()
        self.wait_for_stop()

    def clear_alarm(self):
        """
        清除报警。
        :param station_address: 设备站地址。
        """
        data = struct.pack(">B", self.station)
        for byte in [0x05, 0x00, 0x61, 0xFF, 0x00]:
            data += struct.pack(">B", byte)
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)
        logging.info(f"Sent clear alarm command to station address: {self.station}")
        print(f"Sent clear alarm command to station address: {self.station}")

    def get_pulse(self):
        """
        获取当前绝对位置的函数。
        :param ser: 串口连接对象。
        :param station_address: 设备站地址。
        :return: 当前绝对位置。
        """
        data = struct.pack(">B", self.station)
        for byte in [0x03, 0x60, 0x0D, 0x00, 0x02]:
            data += struct.pack(">B", byte)
        crc = self.calculate_crc(data)
        data += struct.pack(">H", crc)
        self.myserial.write(data)
        time.sleep(0.1)  # 等待一段时间，确保指令发送完成
        response = self.myserial.read(8)  # 读取响应
        if len(response) == 8:
            response_list = list(response)
            # 解析响应数据
            position = (
                (response_list[3] << 24)
                | (response_list[4] << 16)
                | (response_list[5] << 8)
                | response_list[6]
            )
            logging.info(f"Current position: {position}")
            return position

    def move_VID(self, VID: int):
        # pulse = 2000000
        pulse = self.total_pulse - VID * 1000
        self.move_pulse(pulse)

    def get_VID(self):
        pulse = self.get_pulse()
        VID = int((self.total_pulse - pulse) / 1000)
        return VID


if __name__ == "__main__":
    eye1_path = r"D:\MLOptic\MLColorimeter\config\EYE1"
    mydaogui = serial_daogui("COM7", total_pulse=2137000)
    image_path = r"d:\Output\throughfocus\through_focus"
    os.makedirs(image_path, exist_ok=True)
    log_dir = r"D:\Output\throughfocus\logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "serial.log")),
            logging.StreamHandler(),
        ],
    )
    # test
    # mydaogui.clear_alarm()
    # rt = mydaogui.home()
    # mydaogui.move_VID(300)

    with mlcm.ML_Colorimeter() as ml_colorimeter:
        path_list = [
            eye1_path,
        ]
        # 1、连接对应模块
        # add mono module into ml_colorimeter system, according to path_list create one or more mono module
        ml_colorimeter.ml_add_module(path_list=path_list)
        # connect all module in the ml_colorimeter system
        ml_colorimeter.ml_connect()

        # exposure mode setting, Auto or Fixed
        exposure_mode = mlcm.ExposureMode.Auto
        # exposure time for fixed exposure, initial time for auto exposure
        exposure_time = 100
        # camera binning
        binning = mlcm.Binning.ONE_BY_ONE
        # camera binning mode
        binning_mode = mlcm.BinningMode.AVERAGE
        # camera pixel format
        pixel_format = mlcm.MLPixelFormat.MLMono12

        exposure = mlcm.pyExposureSetting(
            exposure_mode=exposure_mode, exposure_time=exposure_time
        )

        id_list = ml_colorimeter.id_list

        # 电机名称
        key_name = "CameraMotion"

        module_id = 1
        ml_mono = ml_colorimeter.ml_bino_manage.ml_get_module_by_id(module_id)
        ml_mono.ml_set_binning(binning)
        ml_mono.ml_set_binning_mode(binning_mode)
        ml_mono.ml_set_pixel_format(pixel_format)
        # vid_list = [ 250, 300, 333,400, 500,600,700,800,900, 1000,1300, 1600,2000]
        vid_list = [2000]
        infinity_position =6.05
        rt = mydaogui.home()

        for vid in vid_list:
            mydaogui.move_VID(vid)
            # 获取当前vid对应的PI值
            fine_focus = round((infinity_position + 1000 / vid * 0.8),2)
            ml_mono.ml_set_exposure(exposure=exposure)
            # 移动电机到当前PI对应的位置，并拍摄图片
            # 移动电机到指定位置
            ml_mono.ml_set_pos_abs_syn(motion_name=key_name,pos=fine_focus)
            time.sleep(0.1)
            # 拍图
            ml_mono.ml_capture_image_syn()
            img = ml_mono.ml_get_image()
            cv2.imwrite(image_path + "\\" + str(fine_focus) + "_" + str(vid) + ".tif", img)
            get_vid = mydaogui.get_VID()

        # rt = mydaogui.move_254()

        # rt = mydaogui.move_255()

        # vid_list = [2000000]
        
        
            

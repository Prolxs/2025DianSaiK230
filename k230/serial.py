import time
from machine import UART
from machine import FPIOA

class Serial:
    def __init__(self,id, baudrate, bits, parity, stop):
        self.id = id
        self.baudrate = baudrate
        self.bits = bits
        self.parity = parity
        self.stop = stop
        
        self.uart = UART(self.id, baudrate=self.baudrate, bits=self.bits, parity=self.parity, stop=self.stop)
        
    def write(self, data):
        self.uart.write(data)

    def read(self, length=None):
        if length is None:  
            return self.uart.read()     
        else:   
            return self.uart.read(length)
        
    def readline(self):
        return self.uart.readline()

    def readinto(self, buf, nbytes=None):
        if nbytes is None:
            return self.uart.readinto(buf)
        else:
            return self.uart.readinto(buf, nbytes)

    def close(self):
        self.uart.deinit()

class serial_2(Serial):
    def __init__(self, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE):
        self.fpioa = FPIOA()
        self.fpioa.set_function(11, FPIOA.UART2_TXD)
        self.fpioa.set_function(12, FPIOA.UART2_RXD)
        super().__init__(UART.UART2, baudrate=baudrate, bits=bits, parity=parity, stop=stop)


class serial_3(Serial):
    def __init__(self, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE):
        self.fpioa = FPIOA()
        self.fpioa.set_function(51, FPIOA.UART3_RXD)
        self.fpioa.set_function(50, FPIOA.UART3_TXD)
        super().__init__(UART.UART3, baudrate=baudrate, bits=bits, parity=parity, stop=stop)

class serial_4(Serial):
    def __init__(self, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE):
        self.fpioa = FPIOA()
        self.fpioa.set_function(37, FPIOA.UART4_RXD)
        self.fpioa.set_function(36, FPIOA.UART4_TXD)
        super().__init__(UART.UART4, baudrate=baudrate, bits=bits, parity=parity, stop=stop)
class tools:
    def __init__(self):
        pass

    # 计算校验和
    def calculate_checksum(xy,str1):
        # 构建字符串：帧头$ + x坐标 + , + y坐标 + ,
        data_str = f"${str1},{xy[0]},{xy[1]}"
        # 初始化校验和
        checksum = 0
        # 遍历字符串中的每个字符（不包括校验和本身）
        for char in data_str:
            # 将字符转换为ASCII值并累加
            checksum += ord(char)

        # 取校验和的低8位（模256）
        C = checksum % 256
        #    print(C)
        return (C,data_str+f",{C}")
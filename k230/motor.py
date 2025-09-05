from .serial import Serial

class Motor:
    def __init__(self, serial: Serial, address):
        if not isinstance(serial, Serial):
            raise TypeError("serial 必须是Serial类型")
        self.serial = serial
        self.address = address
        
    def velocity_control(self, direction, velocity, acceleration, sync_flag):
        """
        控制电机速度
        
        Args:
            direction: 运动方向 (1字节)
            velocity: 目标速度 (RPM, 2字节)
            acceleration: 加速度值 (1字节)
            sync_flag: 同步运动标志 (布尔值)
        """
        # 构建命令帧
        cmd = bytearray(8)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0xF6               # 命令码
        cmd[2] = direction          # 方向
        cmd[3] = (velocity >> 8) & 0xFF  # 速度高字节
        cmd[4] = velocity & 0xFF    # 速度低字节
        cmd[5] = acceleration       # 加速度
        cmd[6] = 1 if sync_flag else 0  # 同步标志
        cmd[7] = 0x6B               # 校验和
        
        # 发送命令
        self.serial.write(cmd)

    def enable_control(self, state: bool, sync_flag: bool):
        """
        控制电机使能状态
        :param state: 使能状态 (True=开启, False=关闭)
        :param sync_flag: 多机同步标志 (True=同步运动, False=独立运动)
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address      # 设备地址
        cmd[1] = 0xF3              # 命令码 (使能控制)
        cmd[2] = 0xAB              # 固定标识值
        cmd[3] = 1 if state else 0 # 状态转换 (bool→int)
        cmd[4] = 1 if sync_flag else 0  # 同步标志转换
        cmd[5] = 0x6B              # 固定校验和
        
        # Send command
        self.serial.write(cmd)

    def position_control(self, direction, velocity, acceleration, position, relative_absolute, sync_flag):
        """
        控制电机位置
        :param direction: 运动方向 (1 byte)
        :param velocity: 目标速度 RPM (2 bytes)
        :param acceleration: 加速度值 (1 byte)
        :param position: 目标位置 (脉冲数, 4 bytes)
        :param relative_absolute: 相对/绝对位置标志 (True=相对, False=绝对)
        :param sync_flag: 多机同步标志 (True=同步运动, False=独立运动)
        """
        # Build command frame
        cmd = bytearray(13)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0xFD               # 命令码 (位置控制)
        cmd[2] = direction          # 方向
        cmd[3] = (velocity >> 8) & 0xFF  # 速度高字节
        cmd[4] = velocity & 0xFF    # 速度低字节
        cmd[5] = acceleration       # 加速度
        cmd[6] = (position >> 24) & 0xFF  # 位置字节3 (最高位)
        cmd[7] = (position >> 16) & 0xFF  # 位置字节2
        cmd[8] = (position >> 8) & 0xFF   # 位置字节1
        cmd[9] = position & 0xFF          # 位置字节0 (最低位)
        cmd[10] = 1 if relative_absolute else 0  # 相对/绝对标志
        cmd[11] = 1 if sync_flag else 0   # 同步标志
        cmd[12] = 0x6B              # 固定校验和
        
        # Send command
        self.serial.write(cmd)

    def stop_immediately(self, sync_flag: bool):
        """
        立即停止电机
        :param sync_flag: 多机同步标志 (True=同步运动, False=独立运动)
        """
        # Build command frame
        cmd = bytearray(3)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0xFE               # 命令码 (立即停止)
        cmd[2] = 1 if sync_flag else 0  # 同步标志
        
        # Send command
        self.serial.write(cmd)

    def trigger_sync_motion(self):
        """
        触发多机同步运动
        """
        # Build command frame
        cmd = bytearray(3)
        cmd[0] = 0x00               # 广播地址
        cmd[1] = 0xFF               # 命令码 (触发多机同步运动)
        cmd[2] = 0x00               # 保留字节
        
        # Send command
        self.serial.write(cmd)

    def homing_trigger(self, homing_mode: int, sync_flag: bool):
        """
        触发回零操作
        :param homing_mode: 回零模式 (0单圈就近回零, 1单圈方向回零, 2多圈无限位碰撞回零, 3多圈限位开关回零)
        :param sync_flag: 多机同步标志 (True=同步运动, False=独立运动)
        """
        # Build command frame
        cmd = bytearray(5)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x9A               # 命令码 (触发回零)
        cmd[2] = homing_mode        # 回零模式
        cmd[3] = 1 if sync_flag else 0  # 同步标志
        cmd[4] = 0x6B              # 固定校验和
        
        # Send command
        self.serial.write(cmd)

    def set_homing_position(self, store_flag: bool):
        """
        设置单圈回零的零点位置
        :param store_flag: 存储标志 (True=存储到Flash, False=仅临时设置)
        """
        # Build command frame
        cmd = bytearray(5)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x93               # 命令码 (设置单圈回零的零点位置)
        cmd[2] = 0x88
        cmd[3] = 1 if store_flag else 0  # 存储标志
        cmd[4] = 0x6B              # 固定校验和
        
        # Send command
        self.serial.write(cmd)

    def clear_motor_block(self):
        """
        解除堵转保护
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x06               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x0E               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数据高字节
        cmd[5] = 0x01               # 寄存器数据低字节
        
        # Send command
        self.serial.write(cmd)

    def calibrate_encoder(self):
        """
        校准编码器
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x06               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x06               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数据高字节
        cmd[5] = 0x01               # 寄存器数据低字节
        
        # Send command
        self.serial.write(cmd)

    def set_current_position_as_zero(self):
        """
        将当前位置清零
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x06               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x0A               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数据高字节
        cmd[5] = 0x01               # 寄存器数据低字节
        
        # Send command
        self.serial.write(cmd)

    def restore_factory_settings(self):
        """
        恢复出厂设置
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x06               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x0F               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数据高字节
        cmd[5] = 0x01               # 寄存器数据低字节
        
        # Send command
        self.serial.write(cmd)

    def read_motor_status(self):
        """
        读取电机状态标志位
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x3A               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x01               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_homing_status(self):
        """
        读取回零状态标志位
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x3B               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x01               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_encoder_value(self):
        """
        读取编码器值
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x31               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x01               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_motor_real_time_speed(self):
        """
        读取电机实时转速
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x35               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x02               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_motor_real_time_position(self):
        """
        读取电机实时位置
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x36               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x03               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_pid_parameters(self):
        """
        读取PID参数
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x21               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x06               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_bus_voltage(self):
        """
        读取总线电压
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x24               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x01               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_phase_current(self):
        """
        读取相电流
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x27               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x01               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def read_driver_parameters(self):
        """
        读取驱动参数
        """
        # Build command frame
        cmd = bytearray(6)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x04               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x42               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x0F               # 寄存器数量低字节
        
        # Send command
        self.serial.write(cmd)

    def modify_driver_parameters(self, parameters):
        """
        修改驱动参数
        :param parameters: 驱动参数列表 (15个参数)
        """
        if len(parameters) != 15:
            raise ValueError("驱动参数必须包含15个元素")
            
        # Build command frame
        cmd = bytearray(21)  # 6字节固定头部 + 15字节参数
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x10               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x48               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x0F               # 寄存器数量低字节
        
        # 添加参数
        for i in range(15):
            cmd[6 + i] = parameters[i]
        
        # Send command
        self.serial.write(cmd)

    def modify_pid_parameters(self, store_flag: bool, kp: int, ki: int, kd: int):
        """
        修改PID参数
        :param store_flag: 存储标志 (True=存储到Flash, False=仅临时设置)
        :param kp: 比例项
        :param ki: 积分项
        :param kd: 微分项
        """
        # Build command frame
        cmd = bytearray(22)  # 6字节固定头部 + 1字节存储标志 + 15字节参数(Kp,Ki,Kd各4字节+1字节保留)
        cmd[0] = self.address       # 设备地址
        cmd[1] = 0x10               # 功能码
        cmd[2] = 0x00               # 寄存器地址高字节
        cmd[3] = 0x4A               # 寄存器地址低字节
        cmd[4] = 0x00               # 寄存器数量高字节
        cmd[5] = 0x07               # 寄存器数量低字节
        cmd[6] = 1 if store_flag else 0  # 存储标志
        cmd[7] = (kp >> 24) & 0xFF  # Kp高字节
        cmd[8] = (kp >> 16) & 0xFF
        cmd[9] = (kp >> 8) & 0xFF
        cmd[10] = kp & 0xFF         # Kp低字节
        cmd[11] = (ki >> 24) & 0xFF # Ki高字节
        cmd[12] = (ki >> 16) & 0xFF
        cmd[13] = (ki >> 8) & 0xFF
        cmd[14] = ki & 0xFF         # Ki低字节
        cmd[15] = (kd >> 24) & 0xFF # Kd高字节
        cmd[16] = (kd >> 16) & 0xFF
        cmd[17] = (kd >> 8) & 0xFF
        cmd[18] = kd & 0xFF         # Kd低字节
        # 保留1个字节为0
        cmd[19] = 0x00
        cmd[20] = 0x00
        cmd[21] = 0x00
        
        # Send command
        self.serial.write(cmd)

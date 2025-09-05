import time

class Pid:
    def __init__(self, Kp=0.0, Ki=0.0, Kd=0.0, setpoint=0.0, sample_time=0.01,out_info=False):
        """
        初始化PID控制器
        
        参数:
            Kp: 比例增益
            Ki: 积分增益
            Kd: 微分增益
            setpoint: 目标值
            sample_time: 控制器更新之间的时间（秒）
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.sample_time = sample_time
        
        self._auto_mode = True
        self._last_output = 0.0
        self._last_input = 0.0
        self._integral = 0.0
        self._last_time = None
        self._last_error = 0.0
        self._out_min = -float('inf')
        self._out_max = float('inf')
        self._out_info = out_info
        self.arrived = False
        self.dead_zone = 2
        # print(self._out_max,self._out_min)
        
    def compute(self, input_val):
        """
        计算PID控制输出
        
        参数:
            input_val: 当前过程变量测量值
            
        返回:
            控制输出值
        """
        # 特殊情况：所有增益为0时直接返回0
        if self.Kp == 0 and self.Ki == 0 and self.Kd == 0:
            self._last_input = input_val
            self._last_output = 0
            self._last_time = time.time()
            return 0
        # if abs(self._last_input - input_val)<2:
        #     error = 0
        # else:
        error = self.setpoint - input_val
        if abs(error) < self.dead_zone :
            self.arrived = True
            error = 0
        else:
            self.arrived = False
        # 计算时间增量
        # 计算时间增量
        # current_time = time.time()
        # if self._last_time is None:
        #     self._last_time = current_time
        #     return self._last_output
            
        # dt = current_time - self._last_time
        # if dt < self.sample_time:
        #     return self._last_output
            
        # 计算比例项
        # proportional = 0
        proportional = self.Kp * error
        
        # 计算积分项（抗饱和）
        if self.Ki != 0:
            self._integral += self.Ki * error
            self._integral = min(max(self._integral, self._out_min), self._out_max)
        else:
            self._integral = 0  # Ki为0时清除积分项
        # print(self._integral)
        
        # 计算微分项（基于误差变化率）：修正符号问题
        # if dt == 0:
        #     derivative = 0
        # else:
        #     derivative = self.Kd * (error - self._last_error) / dt
        derivative = self.Kd * (error - self._last_error)
        # 计算输出
        output = proportional + self._integral + derivative
        output = min(max(output, self._out_min), self._out_max)
        # 更新状态
        self._last_input = input_val
        self._last_output = output
        self._last_error = error
        # self._last_time = current_time
        if self._out_info:
            print("================")
            print(f"Input:{input_val}")
            print(f"Setpoint:{self.setpoint}")
            print(f"E:{error}")
            print(f"Kp:{self.Kp}")
            print(f"Ki:{self.Ki}")
            print(f"Kd:{self.Kd}")
            print(f"P:{proportional}")
            print(f"I:{self._integral}")
            print(f"D:{derivative}")
            print(f"O:{output}")
            print("================")
        return output
        
    def reset(self):
        """重置控制器状态"""
        self._integral = 0.0
        self._last_output = 0.0
        self._last_input = 0.0
        self._last_time = None
        
    def set_auto_mode(self, auto, last_output=None):
        """
        启用/禁用自动控制模式（无扰切换）
        
        参数:
            auto: True为自动模式，False为手动模式
            last_output: 从手动切换到自动时的输出值
        """
        if auto and not self._auto_mode:
            # 从手动切换到自动
            if last_output is not None:
                self._last_output = last_output
                self._integral = last_output - self.Kp * (self.setpoint - self._last_input)
            else:
                self.reset()
                
        self._auto_mode = auto
        
    def set_output_limits(self, min_val, max_val):
        """将控制器输出限制在指定范围内"""
        self._out_min = min_val
        self._out_max = max_val
        self._last_output = min(max(self._last_output, min_val), max_val)
        self._integral = min(max(self._integral, min_val), max_val)
        
    def set_tunings(self, Kp, Ki, Kd):
        """更新PID增益"""
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        
    def set_sample_time(self, sample_time):
        """更新控制器采样时间"""
        if sample_time > 0:
            ratio = sample_time / self.sample_time
            self.Ki *= ratio
            self.Kd /= ratio
            self.sample_time = sample_time
            
    def set_setpoint(self, setpoint):
        """更新控制器目标值"""
        self.setpoint = setpoint

# 立创·庐山派-K230-CanMV开发板资料与相关扩展板软硬件资料官网全部开源
# 开发板官网：www.lckfb.com
# 技术支持常驻论坛，任何技术问题欢迎随时交流学习
# 立创论坛：www.jlc-bbs.com/lckfb
# 关注bilibili账号：【立创开发板】，掌握我们的最新动态！
# 不靠卖板赚钱，以培养中国工程师为己任

from machine import Pin
from machine import FPIOA
import time

class Key:
    def __init__(self):
        self.fpioa = FPIOA()
        self.fpioa.set_function(53, FPIOA.GPIO53)
        self.button = Pin(53, Pin.IN, Pin.PULL_DOWN)
        self.debounce_delay = 20    # 消抖时间(毫秒)
        self.trigger_delay = 200    # 最小触发间隔(毫秒)
        self.last_change_time = 0   # 上次状态变化时间
        self.last_trigger_time = 0  # 上次触发时间
        self.button_last_state = 0  # 上次按钮状态
        self.stable_state = 1       # 当前稳定状态

    def read(self):
        """读取按钮状态（增强消抖处理）"""
        current_state = self.button.value()
        current_time = time.ticks_ms()
        trigger = 0
        
        # 检测状态变化
        if current_state != self.button_last_state:
            self.last_change_time = current_time
            
        # 检查是否超过消抖时间
        if current_time - self.last_change_time > self.debounce_delay:
            # 更新稳定状态
            if current_state != self.stable_state:
                self.stable_state = current_state
                
                # 检测上升沿（按键按下）
                if self.stable_state == 1:
                    # 检查触发间隔
                    if current_time - self.last_trigger_time > self.trigger_delay:
                        trigger = 1
                        self.last_trigger_time = current_time
                
        # 更新上次状态记录
        self.button_last_state = current_state
        return trigger

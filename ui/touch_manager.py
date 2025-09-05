"""
CanMV K230 触摸管理模块
简化版本 - 仅支持真实TOUCH硬件
"""

import time
from machine import TOUCH

try:
    from .ui_core import debug_print
except ImportError:
    # 如果导入失败，创建一个默认的调试函数
    def debug_print(message):
        pass

class TouchPoint:
    """触摸点数据"""
    def __init__(self, x=0, y=0, event=0):
        self.x = x
        self.y = y
        self.event = event
        self.timestamp = time.ticks_ms()

class TouchManager:
    """简化触摸管理器"""
    def __init__(self):
        self.touch_device = None
        self.last_touch_time = 0
        self.touch_threshold = 20  # 减少防抖间隔到20ms，提高响应性
        
        # 双击检测相关变量
        self.last_tap_time = 0  # 上次点击时间戳
        self.last_tap_x = -1    # 上次点击x坐标
        self.last_tap_y = -1    # 上次点击y坐标
        self.double_click_threshold = 300  # 双击时间阈值(ms)
        
        self._init_touch()
    
    def _init_touch(self):
        """初始化触摸设备"""
        try:
            # 使用默认CST328触摸控制器
            self.touch_device = TOUCH(0, type=TOUCH.TYPE_CST328)
            debug_print("触摸设备初始化成功")
        except Exception as e:
            debug_print(f"触摸设备初始化失败: {e}")
            self.touch_device = None
    
    def read_touch(self):
        """读取触摸数据"""
        if not self.touch_device:
            return []
        
        current_time = time.ticks_ms()
        # 对于滑块操作，我们需要更频繁的触摸检测
        if time.ticks_diff(current_time, self.last_touch_time) < self.touch_threshold:
            return []
        
        try:
            touch_data = self.touch_device.read()
            if touch_data and len(touch_data) > 0:
                self.last_touch_time = current_time
                # 转换为TouchPoint对象
                points = []
                for data in touch_data[:1]:  # 只取第一个触摸点
                    # TOUCH_INFO对象有属性：event, x, y, id
                    point = TouchPoint(data.x, data.y, data.event)
                    
                    # 双击检测逻辑
                    current_time = time.ticks_ms()
                    if point.event == 1:  # 按下事件
                        # 检查是否构成双击
                        if (current_time - self.last_tap_time < self.double_click_threshold and
                            abs(point.x - self.last_tap_x) < 20 and
                            abs(point.y - self.last_tap_y) < 20):
                            # 标记为双击事件
                            point.event = 3  # 3=双击事件
                            debug_print(f"[双击检测] 坐标:({point.x},{point.y})")
                            # 重置点击记录
                            self.last_tap_time = 0
                        else:
                            # 记录点击信息
                            self.last_tap_time = current_time
                            self.last_tap_x = point.x
                            self.last_tap_y = point.y
                    
                    debug_print(f"[触摸调试] 原始数据 - 坐标:({data.x},{data.y}) 事件:{data.event} -> {point.event}")
                    points.append(point)
                return points
            else:
                # 没有触摸数据时，返回空列表
                return []
        except Exception as e:
            debug_print(f"读取触摸数据失败: {e}")
        
        return []
    
    def is_available(self):
        """检查触摸设备是否可用"""
        return self.touch_device is not None

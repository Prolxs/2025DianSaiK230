"""
CanMV K230 UI组件库
简化版本 - Button, Slider等基础组件
"""

import time  # 🔧 新增：用于按钮防重复触发的时间戳

# 🔧 导入调试函数
try:
    from .ui_core import debug_print
except ImportError:
    # 如果导入失败，创建一个默认的调试函数
    def debug_print(message):
        pass

# 导入触摸点类
from .touch_manager import TouchPoint

class UIComponent:
    """UI组件基类"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.name = ""
    
    def contains_point(self, x, y):
        """检查点是否在组件内"""
        return (self.x <= x <= self.x + self.width and 
                    self.y <= y <= self.y + self.height)
    
    def draw(self, img):
        """绘制组件 - 子类实现"""
        pass
    
    def handle_touch(self, event):
        """处理触摸事件 - 子类实现"""
        pass

class Button(UIComponent):
    """按钮组件 - 防重复触发版本"""
    def __init__(self, x, y, width, height, text, callback=None):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.bg_color = (80, 120, 160)  # 默认蓝色
        self.text_color = (255, 255, 255)
        self.pressed = False

        # 🔧 新增：防重复触发状态机
        self.touch_state = "IDLE"  # IDLE, PRESSED, WAITING_RELEASE
        self.last_event_time = 0
        self.debounce_delay = 200  # 防抖延迟(ms)
        self.callback_triggered = False  # 标记回调是否已触发
    
    def draw(self, img):
        """绘制按钮"""
        if not self.visible:
            return
        
        # 按下状态反馈
        if self.pressed:
            color = (max(0, self.bg_color[0] - 40), 
                    max(0, self.bg_color[1] - 40), 
                    max(0, self.bg_color[2] - 40))
            border_color = (255, 255, 0)  # 黄色边框
            offset = 2
        else:
            color = self.bg_color
            border_color = (200, 200, 200)
            offset = 0
        
        # 绘制按钮背景和边框
        img.draw_rectangle(self.x, self.y, self.width, self.height, 
                          color=color, fill=True)
        img.draw_rectangle(self.x, self.y, self.width, self.height, 
                          color=border_color, fill=False, thickness=2)
        
        # 绘制文字
        text_x = self.x + (self.width - len(self.text) * 8) // 2 + offset
        text_y = self.y + (self.height - 16) // 2 + offset
        text_color = (255, 255, 100) if self.pressed else self.text_color
        
        img.draw_string_advanced(text_x, text_y, 16, self.text, color=text_color)
    
    def handle_touch(self, event):
        """处理触摸事件 - 防重复触发版本"""
        current_time = time.time() * 1000  # 转换为毫秒

        debug_print(f"[按钮] 收到事件:{event.event} 状态:{self.touch_state} 时间:{current_time:.0f}")

        # 🔧 防重复触发状态机
        if event.event == 2:  # EVENT_DOWN - 按下
            if self.touch_state == "IDLE":
                debug_print(f"[按钮] 按下事件 - 状态转换: IDLE → PRESSED")
                self.touch_state = "PRESSED"
                self.pressed = True
                self.last_event_time = current_time
                self.callback_triggered = False

                # 🎯 关键：只在首次按下时触发回调
                if self.callback and not self.callback_triggered:
                    debug_print(f"[按钮] 触发回调函数")
                    self.callback_triggered = True
                    try:
                        self.callback(self, event)
                    except Exception as e:
                        debug_print(f"[按钮] 回调函数执行出错: {e}")
            else:
                debug_print(f"[按钮] 按下事件被忽略 - 当前状态: {self.touch_state}")

        elif event.event == 3:  # EVENT_MOVE - 移动
            if self.touch_state == "PRESSED":
                debug_print(f"[按钮] 移动事件 - 状态转换: PRESSED → WAITING_RELEASE")
                self.touch_state = "WAITING_RELEASE"
                self.last_event_time = current_time
            elif self.touch_state == "WAITING_RELEASE":
                # 更新时间戳但不改变状态
                self.last_event_time = current_time
                debug_print(f"[按钮] 移动事件 - 保持WAITING_RELEASE状态")
            else:
                debug_print(f"[按钮] 移动事件被忽略 - 当前状态: {self.touch_state}")

        elif event.event == 0:  # 按下后不移动（静态点击）
            if self.touch_state == "PRESSED":
                debug_print(f"[按钮] 静态点击事件 - 状态转换: PRESSED → WAITING_RELEASE")
                self.touch_state = "WAITING_RELEASE"
                self.last_event_time = current_time
            elif self.touch_state == "WAITING_RELEASE":
                # 更新时间戳但不触发回调
                self.last_event_time = current_time
                debug_print(f"[按钮] 重复静态点击事件被忽略")
            else:
                debug_print(f"[按钮] 静态点击事件被忽略 - 当前状态: {self.touch_state}")

        elif event.event == 1:  # 真正的释放事件 - 但无法获得
            debug_print(f"[按钮] 收到事件1 - 释放事件")
            self._reset_button_state()

        else:
            debug_print(f"[按钮] 未知事件类型: {event.event}")

    def _reset_button_state(self):
        """重置按钮状态"""
        debug_print(f"[按钮] 重置状态: {self.touch_state} → IDLE")
        self.touch_state = "IDLE"
        self.pressed = False
        self.callback_triggered = False

    def update_state(self):
        """更新按钮状态 - 处理超时重置"""
        if self.touch_state != "IDLE":
            current_time = time.time() * 1000
            if current_time - self.last_event_time > self.debounce_delay:
                debug_print(f"[按钮] 超时重置 - 时间差: {current_time - self.last_event_time:.0f}ms")
                self._reset_button_state()

    def get_value(self):
        """获取按钮当前值 - 按下时为True，未按下时为False"""
        return self.pressed

    def set_value(self, value):
        """设置按钮状态 - 主要用于编程控制"""
        if isinstance(value, bool):
            self.pressed = value
            if not value:
                # 如果设置为False，重置整个状态机
                self._reset_button_state()
        else:
            debug_print(f"[按钮] 警告：set_value只接受布尔值，收到: {type(value)}")

class Slider(UIComponent):
    """简化滑块组件 - 稳定性优先"""
    def __init__(self, x, y, width, height, min_val, max_val, value, orientation="horizontal", callback=None):
        super().__init__(x, y, width, height)
        
        # 核心属性
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.value = float(value)
        self.orientation = orientation
        self.callback = callback
        
        # 步长控制 - 默认0.1
        self.step_size = 0.1
        
        # 状态控制
        self.dragging = False
        
        # 外观属性
        self.track_color = (100, 100, 100)
        self.handle_color = (200, 200, 200)
        
        # 确保初始值在有效范围内
        self.value = self._clamp_value(self.value)
        
    def get_value(self):
        """获取当前值"""
        return self.value
    
    def set_value(self, value):
        """设置值"""
        try:
            new_value = float(value)
            old_value = self.value
            self.value = self._clamp_value(new_value)
            
            # 如果值发生变化，触发回调
            if abs(self.value - old_value) > 0.001 and self.callback:
                try:
                    self.callback(self, None, self.value)
                except Exception as e:
                    debug_print(f"[滑块] 设置值回调执行出错: {e}")
            return True
        except (ValueError, TypeError):
            debug_print(f"[滑块] 设置值失败: 无效值 {value}")
            return False
            
    def set_step_size(self, step):
        """设置步长"""
        try:
            if step > 0:
                self.step_size = float(step)
                # 重新对齐当前值到新步长
                self.value = self._align_to_step(self.value)
        except (ValueError, TypeError):
            debug_print(f"[滑块] 设置步长失败: 无效步长 {step}")
    
    def _clamp_value(self, value):
        """限制值在有效范围内并对齐到步长"""
        # 先限制在范围内
        clamped = max(self.min_val, min(self.max_val, value))
        # 然后对齐到步长
        return self._align_to_step(clamped)
    
    def _align_to_step(self, value):
        """对齐值到步长的倍数"""
        if self.step_size <= 0:
            return value
        
        # 计算相对于最小值的步数
        relative_value = value - self.min_val
        steps = round(relative_value / self.step_size)
        aligned_value = self.min_val + steps * self.step_size
            
        # 确保在范围内
        return max(self.min_val, min(self.max_val, aligned_value))
    
    def draw(self, img):
        """绘制滑块"""
        if not self.visible:
            return
        
        # 绘制滑轨
        img.draw_rectangle(self.x, self.y, self.width, self.height, 
                          color=self.track_color, fill=True)
        
        # 计算手柄位置
        if self.max_val <= self.min_val:
            value_ratio = 0
        else:
            value_ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        
        if self.orientation == "horizontal":
            handle_size = min(self.height, 20)
            handle_x = self.x + int(value_ratio * (self.width - handle_size))
            handle_y = self.y
            handle_w, handle_h = handle_size, self.height
        else:  # vertical
            handle_size = min(self.width, 20)
            handle_x = self.x
            handle_y = handle_y = self.y + int((1 - value_ratio) * (self.height - handle_size))
            handle_w, handle_h = self.width, handle_size
        
        # 根据拖拽状态调整手柄颜色
        if self.dragging:
            handle_color = (min(255, self.handle_color[0] + 50), 
                          min(255, self.handle_color[1] + 50), 
                          min(255, self.handle_color[2] + 50))
            border_color = (255, 255, 0)
        else:
            handle_color = self.handle_color
            border_color = (255, 255, 255)
        
        # 绘制手柄
        img.draw_rectangle(handle_x, handle_y, handle_w, handle_h, 
                          color=handle_color, fill=True)
        img.draw_rectangle(handle_x, handle_y, handle_w, handle_h, 
                          color=border_color, fill=False, thickness=2)
        
        # 显示数值
        value_text = f"{self.value:.1f}"
        if self.orientation == "horizontal":
            text_x = self.x + self.width + 10
            text_y = self.y + self.height // 2 - 8
        else:
            text_x = self.x - 60
            text_y = self.y - 20
        
        img.draw_string_advanced(text_x, text_y, 16, value_text, color=(255, 255, 255))

    def _update_value_from_position(self, x, y):
        """根据触摸位置更新数值 - 基于最终澄清的真实事件映射"""
        old_value = self.value

        debug_print(f"[滑块数值] 更新位置 - 触摸:({x},{y}) 滑块区域:({self.x},{self.y},{self.x+self.width},{self.y+self.height})")

        # 🔧 修复：不要强制限制触摸点，允许超出滑块区域的触摸
        # 这样可以避免边界锁定问题
        if self.orientation == "horizontal":
            # 🚨 除零保护：检查宽度是否为0
            if self.width <= 0:
                debug_print(f"[滑块数值] 错误：宽度为0，无法计算比例")
                return

            # 🔧 修复：直接使用原始触摸坐标计算比例
            relative_pos = x - self.x
            ratio = relative_pos / self.width  # 已有除零保护
            debug_print(f"[滑块数值] 水平计算 - 原始相对位置:{relative_pos} 比例:{ratio:.3f}")

        else:  # vertical
            # 🚨 除零保护：检查高度是否为0
            if self.height <= 0:
                debug_print(f"[滑块数值] 错误：高度为0，无法计算比例")
                return

            # 🔧 修复：垂直滑块计算，直接使用原始坐标
            relative_pos = y - self.y
            # 垂直滑块：顶部是最大值，所以需要反转
            ratio = 1 - (relative_pos / self.height)  # 已有除零保护
            debug_print(f"[滑块数值] 垂直计算 - 原始相对位置:{relative_pos} 比例:{ratio:.3f}")

        # 🔧 修复：在这里才限制比例在0-1之间，而不是限制坐标
        ratio = max(0.0, min(1.0, ratio))
        debug_print(f"[滑块数值] 限制后比例:{ratio:.3f}")

        # 计算新值
        new_value = self.min_val + ratio * (self.max_val - self.min_val)
        debug_print(f"[滑块数值] 原始新值:{new_value:.3f}")

        # 应用步长对齐和范围限制
        self.value = self._clamp_value(new_value)
        debug_print(f"[滑块数值] 数值变化: {old_value:.3f} -> {self.value:.3f}")

        # 如果值发生变化，触发回调
        if abs(self.value - old_value) > 0.001 and self.callback:
            debug_print(f"[滑块数值] 触发回调函数")
            try:
                self.callback(self, None, self.value)
            except Exception as e:
                debug_print(f"[滑块] 触摸回调执行出错: {e}")
        else:
            debug_print(f"[滑块数值] 值变化太小或无回调函数，不触发回调")

    def handle_touch(self, event):
        """处理触摸事件 - 基于最终澄清的真实事件映射"""
        # 处理字典形式的事件对象
        event_data = event if isinstance(event, dict) else {
            "x": event.x,
            "y": event.y,
            "event": event.event
        }
        
        debug_print(f"[滑块触摸] {self.name if hasattr(self, 'name') else '滑块'} 收到事件:{event_data['event']} 坐标:({event_data['x']},{event_data['y']})")

        # 🎯 最终修正：基于完整测试的真实事件映射：
        # 2 = 按下 (EVENT_DOWN)
        # 3 = 按下后移动 (EVENT_MOVE)
        # 0 = 按下后不移动（静态点击，不是释放）
        # 1 = 真正的释放事件 (EVENT_UP) - 但无法获得

        if event.event == 2:  # EVENT_DOWN - 按下事件
            debug_print(f"[滑块触摸] 按下事件 - 开始拖拽")
            self.dragging = True
            self._update_value_from_position(event.x, event.y)

        elif event.event == 3:  # EVENT_MOVE - 按下后移动事件
            debug_print(f"[滑块触摸] 移动事件 - 拖拽状态:{self.dragging}")
            # 处理移动事件
            if self.dragging:
                self._update_value_from_position(event.x, event.y)
            else:
                # 如果收到移动事件但没有拖拽状态，可能错过了按下事件
                debug_print(f"[滑块触摸] 警告：收到移动事件但未处于拖拽状态，自动开始拖拽")
                self.dragging = True
                self._update_value_from_position(event.x, event.y)

        elif event.event == 0:  # 按下后不移动（静态点击）
            debug_print(f"[滑块触摸] 静态点击事件 - 直接设置位置")
            # 这不是释放事件，而是按下后不移动的静态点击
            self._update_value_from_position(event.x, event.y)
            # 注意：由于无法获得真正的释放事件(1)，我们需要其他方式检测拖拽结束

        elif event.event == 1:  # 真正的释放事件 - 但无法获得
            debug_print(f"[滑块触摸] 收到事件1 - 这应该是释放事件，但理论上无法获得")
            # 如果真的收到了，说明系统行为可能有变化
            if self.dragging:
                self.dragging = False
                debug_print(f"[滑块触摸] 意外收到释放事件，结束拖拽")

        else:
            debug_print(f"[滑块触摸] 未知事件类型: {event.event}")

class StaticText(UIComponent):
    """静态文本组件 - 基于draw_string_advanced封装"""
    def __init__(self, x, y, font_size, text, color=(255, 255, 255)):
        # 计算文本的大概尺寸（简单估算）
        estimated_width = len(text) * (font_size * 1.2)  # 字符宽度约为字体大小的0.6倍
        estimated_height = font_size

        super().__init__(x, y, int(estimated_width), int(estimated_height))

        self.font_size = font_size
        self.text = text
        self.color = color
        self.background_color = None  # 可选背景色
        self.alignment = "left"  # 对齐方式: left, center, right
        self.auto_size = True  # 是否自动调整尺寸

    def set_text(self, text):
        """设置文本内容"""
        self.text = text
        if self.auto_size:
            # 重新计算尺寸
            self.width = int(len(text) * (self.font_size * 0.6))
            self.height = self.font_size

    def set_color(self, color):
        """设置文本颜色"""
        self.color = color

    def set_background_color(self, color):
        """设置背景颜色"""
        self.background_color = color

    def set_alignment(self, alignment):
        """设置对齐方式"""
        if alignment in ["left", "center", "right"]:
            self.alignment = alignment

    def draw(self, img):
        """绘制静态文本 - 修复文本重叠问题"""
        if not self.visible or not self.text:
            return
        
        # 关键修复：始终清除整个控件区域
        # 使用背景色（如果设置了）或默认背景色（深灰色）
        clear_color = self.background_color if self.background_color else (0, 0, 0)
        img.draw_rectangle(self.x, self.y, self.width, self.height,
                         color=clear_color, fill=True)

        # 计算文本绘制位置
        text_x = self.x
        if self.alignment == "center":
            text_x = self.x + (self.width - len(self.text) * (self.font_size * 0.6)) // 2
        elif self.alignment == "right":
            text_x = self.x + self.width - len(self.text) * (self.font_size * 0.6)

        text_y = self.y

        # 绘制文本
        img.draw_string_advanced(int(text_x), int(text_y), self.font_size,
                               self.text, color=self.color)

    def handle_touch(self, event):
        """静态文本通常不处理触摸事件，但可以被子类重写"""
        pass

class Panel(UIComponent):
    """面板组件 - 基于创建空白图像方法封装"""
    def __init__(self, x, y, width, height, background_color=(50, 50, 50)):
        super().__init__(x, y, width, height)

        self.background_color = background_color
        self.border_color = None  # 边框颜色
        self.border_width = 0  # 边框宽度
        self.child_components = []  # 子组件列表
        self.padding = 5  # 内边距

    def set_background_color(self, color):
        """设置背景颜色"""
        self.background_color = color

    def set_border(self, color, width=1):
        """设置边框"""
        self.border_color = color
        self.border_width = width

    def add_child(self, component):
        """添加子组件（相对于面板的坐标）"""
        # 保持子组件的相对坐标不变
        # 注意：子组件的坐标应该是相对于面板的
        self.child_components.append(component)
        return component

    def remove_child(self, component):
        """移除子组件"""
        if component in self.child_components:
            self.child_components.remove(component)

    def clear_children(self):
        """清空所有子组件"""
        self.child_components.clear()

    def draw(self, img):
        """绘制面板"""
        if not self.visible:
            return

        # 绘制背景
        img.draw_rectangle(self.x, self.y, self.width, self.height,
                         color=self.background_color, fill=True)

        # 绘制边框
        if self.border_color and self.border_width > 0:
            img.draw_rectangle(self.x, self.y, self.width, self.height,
                             color=self.border_color, fill=False,
                             thickness=self.border_width)

        # 绘制子组件
        for child in self.child_components:
            if hasattr(child, 'draw'):
                # 保存原始坐标
                orig_x, orig_y = child.x, child.y
                # 应用面板偏移
                child.x += self.x + self.padding
                child.y += self.y + self.padding
                # 绘制子组件
                child.draw(img)
                # 恢复原始坐标
                child.x, child.y = orig_x, orig_y

    def handle_touch(self, event):
        """面板将触摸事件传递给子组件"""
        # 检查触摸点是否在面板内
        if not self.contains_point(event.x, event.y):
            return

        # 将触摸事件传递给子组件
        for child in reversed(self.child_components):  # 后添加的组件优先
            if hasattr(child, 'visible') and child.visible:
                # 保存原始坐标
                orig_x, orig_y = child.x, child.y
                # 应用面板偏移
                child.x += self.x + self.padding
                child.y += self.y + self.padding
                
                # 检查触摸点是否在子组件内
                if hasattr(child, 'contains_point') and child.contains_point(event.x, event.y):
                    if hasattr(child, 'handle_touch'):
                        # 创建子组件的局部坐标事件（使用字典代替TouchPoint类）
                        local_event = {
                            "x": event.x - child.x,   # 相对于子组件的坐标
                            "y": event.y - child.y,
                            "event": event.event
                        }
                        child.handle_touch(local_event)
                    break  # 只处理最上层的组件
                
                # 恢复原始坐标
                child.x, child.y = orig_x, orig_y


class ParameterControl(UIComponent):
    """重构版参数调节控件 - 使用相对坐标和灵活布局"""
    
    def __init__(self, x, y, width, height, name, value=0, min_val=0, max_val=100, step=1, callback=None):
        """
        初始化参数调节控件（重构版）
        
        Args:
            x, y, width, height: 控件位置和大小
            name: 参数名称
            value: 初始值
            min_val: 最小值
            max_val: 最大值
            step: 步长
            callback: 值改变时的回调函数，格式：callback(control, value)
        """
        super().__init__(x, y, width, height)
        self.name = name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.callback = callback
        self.bg_color = (60, 60, 60)
        self.padding = 5  # 内边距
        
        # 创建子组件（使用相对坐标）
        self.name_label = StaticText(
            self.padding, 
            self.padding, 
            16, 
            name, 
            color=(255, 255, 200)
        )
        
        # 值标签居中
        value_text = f"{value:.1f}" if isinstance(value, float) else str(value)
        text_width = len(value_text) * 10  # 估算文本宽度
        value_x = (width - text_width) // 2
        
        self.value_label = StaticText(
            value_x, 
            self.padding, 
            16, 
            value_text, 
            color=(255, 255, 255)
        )
        self.value_label.background_color = (80, 80, 100)
        
        # 按钮使用相对位置
        button_size = min(30, height - self.padding * 2)
        minus_x = width - button_size * 2 - self.padding
        plus_x = width - button_size - self.padding
        
        self.minus_button = Button(
            minus_x, 
            self.padding, 
            button_size, 
            button_size, 
            "-", 
            self._on_minus
        )
        self.minus_button.bg_color = (180, 60, 60)
        
        self.plus_button = Button(
            plus_x, 
            self.padding, 
            button_size, 
            button_size, 
            "+", 
            self._on_plus
        )
        self.plus_button.bg_color = (60, 180, 60)
    
    def draw(self, img):
        """绘制控件"""
        if not self.visible:
            return
        
        # 绘制背景
        img.draw_rectangle(
            self.x, self.y, 
            self.width, self.height,
            color=self.bg_color, 
            fill=True
        )
        
        # 绘制子组件（转换为绝对坐标）
        components = [
            self.name_label,
            self.value_label,
            self.minus_button,
            self.plus_button
        ]
        
        for comp in components:
            orig_x, orig_y = comp.x, comp.y
            comp.x = self.x + comp.x
            comp.y = self.y + comp.y
            comp.draw(img)
            comp.x, comp.y = orig_x, orig_y
    
    def handle_touch(self, event):
        """处理触摸事件"""
        if not self.visible:
            return
        
        # 转换为控件内坐标
        local_x = event.x - self.x
        local_y = event.y - self.y
        
        # 检查触摸点是否在控件内
        if not (0 <= local_x <= self.width and 0 <= local_y <= self.height):
            return
        
        # 创建局部事件
        local_event = TouchPoint(local_x, local_y, event.event)
        
        # 按Z顺序检查子控件（从后向前）
        components = [
            self.plus_button,
            self.minus_button,
            self.value_label,
            self.name_label
        ]
        
        for comp in components:
            if comp.contains_point(local_x, local_y):
                comp.handle_touch(local_event)
                break
    
    def _on_minus(self, button, event):
        """减号按钮回调"""
        self.set_value(self.value - self.step)
    
    def _on_plus(self, button, event):
        """加号按钮回调"""
        self.set_value(self.value + self.step)
    
    def set_value(self, value, trigger_callback=True):
        """
        设置当前值，并更新显示
        
        Args:
            value: 新值
            trigger_callback: 是否触发回调
        """
        # 限制在范围内
        new_value = max(self.min_val, min(self.max_val, value))
        
        # 应用步长对齐
        if self.step > 0:
            steps = round((new_value - self.min_val) / self.step)
            new_value = self.min_val + steps * self.step
        
        # 更新值和显示
        if abs(new_value - self.value) > 1e-3:
            self.value = new_value
            value_text = f"{self.value:.1f}" if isinstance(self.value, float) else str(self.value)
            self.value_label.set_text(value_text)
            
            # 触发回调
            if trigger_callback and self.callback:
                try:
                    self.callback(self, self.value)
                except Exception as e:
                    debug_print(f"[参数控件] 回调函数执行出错: {e}")
    
    def get_value(self):
        return self.value
    
    def set_step(self, step):
        """设置步长"""
        if step > 0:
            self.step = step
            # 重新对齐当前值
            self.set_value(self.value, False)
    
    def set_range(self, min_val, max_val):
        """设置取值范围"""
        if min_val < max_val:
            self.min_val = min_val
            self.max_val = max_val
            # 确保当前值在新范围内
            self.set_value(self.value, False)
    
    def set_name(self, name):
        """设置参数名称"""
        self.name = name
        self.name_label.set_text(name)

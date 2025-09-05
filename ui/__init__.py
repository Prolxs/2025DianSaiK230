"""
CanMV K230 TouchUI 库
简化架构版本 - 仅支持真实触摸硬件

使用示例:
    from UI_Library import TouchUI
    
    ui = TouchUI(800, 480)
    ui.add_button(100, 100, 120, 60, "按钮", callback_func)
    ui.update(img)
"""

__version__ = "2.0.0"
__author__ = "AI Assistant"
__description__ = "CanMV K230简化TouchUI库 - 仅支持真实触摸"

# 导出核心类
from .ui_core import TouchUI, set_debug, debug_print
from .components import Button, Slider, StaticText, Panel, ParameterControl
from .touch_manager import TouchManager

# 便捷别名
UI = TouchUI

__all__ = [
    'TouchUI',
    'UI',
    'Button',
    'Slider',
    'StaticText',
    'Panel',
    'TouchManager',
    'set_debug',
    'debug_print',
    'ParameterControl'
]
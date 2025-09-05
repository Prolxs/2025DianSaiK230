#!/usr/bin/env python3
"""
CanMV K230 UI组件库完整演示程序
展示所有组件功能：Button、Slider、StaticText、Panel
包括：手指跟随、0.1步长、负数范围、回调函数、文本显示、面板布局
"""

import time, os, sys
from media.display import *
from media.media import *

# 处理导入问题 - 支持不同的运行方式
try:
    from ui.ui_core import TouchUI
except ImportError:
    # 如果相对导入失败，尝试直接导入
    try:
        from ui_core import TouchUI
    except ImportError:
        # 如果还是失败，添加当前目录到路径
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from ui_core import TouchUI

# 显示参数配置
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

# 全局变量存储滑块引用
slider1 = None
slider2 = None
slider3 = None

def on_slider1_change(component, event, value):
    """滑块1回调函数 - 正数范围测试"""
    print(f"===== 滑块1数值: {value:.1f} =====")

def on_slider2_change(component, event, value):
    """滑块2回调函数 - 负数范围测试"""
    print(f"===== 滑块2数值: {value:.1f} =====")

def on_slider3_change(component, event, value):
    """滑块3回调函数 - 垂直滑块测试"""
    print(f"===== 滑块3数值: {value:.1f} =====")

def on_button_click(component, event):
    """按钮回调函数 - 测试设置值功能"""
    global slider1, slider2, slider3
    print("===== 按钮被点击！重置滑块数值 =====")
    
    try:
        if slider1:
            slider1.set_value(50.0)
        if slider2:
            slider2.set_value(0.0) 
        if slider3:
            slider3.set_value(25.0)
        print("滑块数值已重置")
    except Exception as e:
        print(f"重置滑块时出错: {e}")

def create_enhanced_ui():
    """创建增强的UI界面 - 展示所有组件"""
    global slider1, slider2, slider3

    ui = TouchUI(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    # 主标题 - StaticText组件演示
    title = ui.add_static_text(50, 20, 24, "CanMV K230 UI组件库演示", (255, 255, 100))
    title.set_alignment("left")

    # 版本信息
    version_text = ui.add_static_text(50, 50, 16, "版本: v2.0 | 组件: Button, Slider, StaticText, Panel", (200, 200, 200))

    # 创建左侧控制面板 - Panel组件演示
    control_panel = ui.add_panel(30, 80, 450, 280, (40, 40, 60))
    control_panel.set_border((100, 100, 150), 2)

    # 面板标题
    panel_title = ui.add_static_text(10, 10, 18, "控制面板", (255, 255, 255))
    panel_title.set_background_color((60, 60, 80))

    # 滑块1 - 水平滑块，正数范围 (0-100)，步长0.1
    slider1 = ui.add_slider(10, 50, 350, 40, 0, 100, 50, "horizontal", on_slider1_change)
    slider1.name = "正数滑块"
    slider1.set_step_size(0.1)

    # 滑块1标签
    slider1_label = ui.add_static_text(10, 30, 14, "正数滑块 (0-100):", (200, 255, 200))

    # 滑块2 - 水平滑块，负数范围 (-50到50)，步长0.1
    slider2 = ui.add_slider(10, 130, 350, 40, -50, 50, 0, "horizontal", on_slider2_change)
    slider2.name = "负数滑块"
    slider2.set_step_size(0.1)

    # 滑块2标签
    slider2_label = ui.add_static_text(10, 110, 14, "负数滑块 (-50到50):", (200, 255, 200))

    # 重置按钮
    reset_button = ui.add_button(10, 200, 100, 50, "重置", on_button_click)
    reset_button.bg_color = (180, 80, 80)
    reset_button.text_color = (255, 255, 255)

    # 状态显示
    status_text = ui.add_static_text(120, 220, 14, "状态: 就绪", (100, 255, 100))

    # 创建右侧信息面板 - Panel组件演示
    info_panel = ui.add_panel(500, 80, 270, 280, (60, 40, 40))
    info_panel.set_border((150, 100, 100), 2)

    # 信息面板标题
    info_title = ui.add_static_text(10, 10, 18, "组件信息", (255, 255, 255))
    info_title.set_background_color((80, 60, 60))

    # 垂直滑块 - 在信息面板中
    slider3 = ui.add_slider(220, 50, 40, 180, 0, 50, 25, "vertical", on_slider3_change)
    slider3.name = "垂直滑块"
    slider3.set_step_size(0.1)

    # 垂直滑块标签
    slider3_label = ui.add_static_text(170, 30, 14, "垂直:", (200, 255, 200))

    # 组件统计信息
    info_texts = [
        "• 组件统计:",
        "  - Button: 1个",
        "  - Slider: 3个",
        "  - StaticText: 多个",
        "  - Panel: 2个",
        "",
        "• 功能特性:",
        "  - 触摸响应",
        "  - 手指跟随",
        "  - 数值回调",
        "  - 面板嵌套",
        "  - 文本显示"
    ]

    for i, text in enumerate(info_texts):
        if text:  # 非空行
            color = (200, 200, 200) if not text.startswith("•") else (255, 200, 100)
            ui.add_static_text(10, 50 + i * 16, 12, text, color)

    return ui

def test_slider_api():
    """测试滑块API功能"""
    print("\n===== 滑块API测试 =====")
    
    # 创建测试滑块
    ui = TouchUI(800, 480)
    
    def test_callback(component, event, value):
        print(f"测试回调: {value:.1f}")
    
    slider = ui.add_slider(0, 0, 200, 30, -10, 10, 0, "horizontal", test_callback)
    
    # 测试设置值
    print("测试 set_value 方法:")
    slider.set_value(5.0)
    print(f"设置5.0，实际值: {slider.get_value():.1f}")
    
    slider.set_value(5.55)  # 应该对齐到5.5
    print(f"设置5.55，实际值: {slider.get_value():.1f}")
    
    slider.set_value(-3.27)  # 应该对齐到-3.3
    print(f"设置-3.27，实际值: {slider.get_value():.1f}")
    
    slider.set_value(100)  # 超出范围，应该限制到10
    print(f"设置100，实际值: {slider.get_value():.1f}")
    
    # 测试步长
    print("\n测试 set_step_size 方法:")
    slider.set_step_size(0.5)
    slider.set_value(5.3)  # 应该对齐到5.5
    print(f"步长0.5，设置5.3，实际值: {slider.get_value():.1f}")
    
    slider.set_step_size(1.0)
    slider.set_value(5.7)  # 应该对齐到6.0
    print(f"步长1.0，设置5.7，实际值: {slider.get_value():.1f}")
    
    print("===== API测试完成 =====\n")

def main():
    """主程序"""
    try:
        # API测试
        test_slider_api()
        
        # 初始化显示器
        Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
        
        # 初始化媒体管理器
        MediaManager.init()
        
        # 创建增强UI
        ui = create_enhanced_ui()

        print("UI组件库完整演示程序启动")
        print("组件展示：")
        print("- StaticText: 标题、标签、信息显示")
        print("- Panel: 控制面板、信息面板(带边框)")
        print("- Slider: 3个滑块(水平正数、水平负数、垂直)")
        print("- Button: 重置按钮")
        print("功能特性：")
        print("- 触摸响应: 拖拽滑块，点击按钮")
        print("- 回调函数: 实时显示数值变化")
        print("- 面板嵌套: 组件相对坐标布局")
        print("- 文本显示: 多种字体大小和颜色")
        
        frame_count = 0
        last_time = time.time()
        
        # 主循环
        while True:
            try:
                # 创建空白图像
                img = image.Image(DISPLAY_WIDTH, DISPLAY_HEIGHT, image.RGB565)
                img.clear()
                
                # 更新UI - 所有组件(包括StaticText和Panel)会自动绘制
                ui.update(img)
                
                # 显示图像
                Display.show_image(img)
                
                # FPS计算和显示
                frame_count += 1
                if frame_count % 30 == 0:
                    current_time = time.time()
                    time_diff = current_time - last_time
                    # 🚨 除零保护：防止时间差为0
                    if time_diff > 0:
                        fps = 30 / time_diff
                        print(f"FPS: {fps:.1f}")
                    else:
                        print("FPS: 计算中...")
                    last_time = current_time
                
                # 控制帧率
                time.sleep(0.02)  # 50FPS
                
            except KeyboardInterrupt:
                print("程序被用户中断")
                break
            except Exception as e:
                print(f"主循环出错: {e}")
                time.sleep(0.1)
                continue
                
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            # 清理资源
            MediaManager.deinit()
            print("演示程序结束")
        except:
            pass

if __name__ == "__main__":
    main()
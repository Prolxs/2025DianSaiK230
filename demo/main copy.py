# 立创·庐山派-K230-CanMV开发板资料与相关扩展板软硬件资料官网全部开源
# 开发板官网：www.lckfb.com
# 技术支持常驻论坛，任何技术问题欢迎随时交流学习
# 立创论坛：www.jlc-bbs.com/lckfb
# 关注bilibili账号：【立创开发板】，掌握我们的最新动态！
# 不靠卖板赚钱，以培养中国工程师为己任

import time, os, sys, math
import image  # 添加image模块导入

from media.sensor import *
from media.display import *
from media.media import *
from k230.serial import serial_2,serial_3
from k230.motor import Motor
from k230.pid import Pid
from k230.laserDraw import *  # 导入图形绘制模块
from ui.ui_core import TouchUI,set_debug
from machine import Pin
from machine import FPIOA
import _thread

# 全局状态变量
DRAW_STATE = "IDLE"  # 状态: IDLE, DRAWING, EXECUTING
current_shape = None
shapes = []  # 存储绘制的图形
#import cv_lite
#import ulab.numpy as np     # MicroPython NumPy 类库
sensor = None
# 红色激光点颜色阈值，可根据实际情况调整
RED_LASER_THRESHOLD = [(39, 100, 19, 127, -128, 127)]
# 显示模式选择：可以是 "VIRT"、"LCD" 或 "HDMI"
DISPLAY_MODE = "LCD"

# 根据模式设置显示宽高
if DISPLAY_MODE == "VIRT":
    # 虚拟显示器模式
    DISPLAY_WIDTH = ALIGN_UP(1920, 16)
    DISPLAY_HEIGHT = 1080
elif DISPLAY_MODE == "LCD":
    # 3.1寸屏幕模式
    DISPLAY_WIDTH = 800
    DISPLAY_HEIGHT = 480
elif DISPLAY_MODE == "HDMI":
    # HDMI扩展板模式
    DISPLAY_WIDTH = 1920
    DISPLAY_HEIGHT = 1080
else:
    raise ValueError("未知的 DISPLAY_MODE，请选择 'VIRT', 'LCD' 或 'HDMI'")


def btn_callback(component, event):
    # component.get_value()
    LASER_R.value(LASER_R.value() ^ 1)

def laser_detection(img):
    # lock.acquire()
    # 中值滤波
    img = img.median(1)
    # img.gamma_corr(1.3)
#    print(img.size())
    Rxy = None
#    Gxy = None
    # 查找红色激光点
    red_blobs = img.find_blobs(RED_LASER_THRESHOLD, pixels_threshold=5, area_threshold=5, merge=True)
    
    # print(red_blobs)
    
    if red_blobs:
        sumX = 0
        sumY = 0
        for blob in red_blobs:
            # 获取激光点的中心位置
            sumX += blob.cx()
            sumY += blob.cy()
        num = len(red_blobs)
        # print(num)
        if num:
            Rxy = (int(sumX/num),int(sumY/num))
#            img.draw_cross(Rxy[0], Rxy[1], color=(255, 0, 0), size=10, thickness=1)
        else:
            Rxy = None

    # 查找绿色激光点
    # green_blobs = img.find_blobs(GREEN_LASER_THRESHOLD, pixels_threshold=1, area_threshold=3, merge=True,roi=(31,19,313,204))
    # if green_blobs:
    #     sumX = 0
    #     sumY = 0
    #     for blob in green_blobs:
    #         # 获取激光点的中心位置
    #         sumX += blob.cx()
    #         sumY += blob.cy()
    #     num = len(red_blobs)
    #     if num:
    #         Gxy = (int(sumX/num),int(sumY/num))
    #         # 在图像上绘制激光点的中心位置
    #         img.draw_cross(Gxy[0], Gxy[1], color=(0, 255, 0), size=10, thickness=1)
    #     else :
    #         Gxy = None
#                print(f"Green laser point detected at ({x}, {y})")

    # 显示图片
    # Display.show_image(img, x=0,y=0)
    # lock.release()
    return Rxy

def base_init():
    # 构造一个具有默认配置的摄像头对象
    sensor = Sensor(width=1280,height=960)
    # 重置摄像头sensor
    sensor.reset()
    # 无需进行镜像翻转
    # 设置水平镜像
    # sensor.set_hmirror(False)
    # 设置垂直翻转
    # sensor.set_vflip(False)
    # 设置通道0的输出尺寸为1920x1080
    sensor.set_framesize(width=400, height=240)
    # 设置通道0的输出像素格式为RGB888
    sensor.set_pixformat(Sensor.RGB565)
    # 根据模式初始化显示器
    if DISPLAY_MODE == "VIRT":
        Display.init(Display.VIRT, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, fps=60)
    elif DISPLAY_MODE == "LCD":
        Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    elif DISPLAY_MODE == "HDMI":
        Display.init(Display.LT9611, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    # 初始化媒体管理器
    MediaManager.init()
    # 启动传感器
    sensor.run()
    return sensor



if __name__ == "__main__":
#    global img
    try:
        redLaser = None
        
        sensor = base_init()
        motory_ctrl = serial_2()
        motorx_ctrl = serial_3()
#        time.sleep_ms(100)
        motorx = Motor(motorx_ctrl, 0x01)  # 地址为0x01的电机对象
        motory = Motor(motory_ctrl, 0x01)  # 地址为0x01的电机对象
        motorx.enable_control(True,False)  # 使能电机控制
        motory.enable_control(True,False)  # 使能电机控制
        # P=0.5 D=0.13
        pidx = Pid(Kp=0.17, Ki=0.0, Kd=0.001, setpoint=200, sample_time=0.008,out_info=False)
        pidx.set_output_limits(-200, 200)
        pidy = Pid(Kp=0.2, Ki=0.0, Kd=0.001, setpoint=120, sample_time=0.01,out_info=False)
        pidy.set_output_limits(-200, 200)
        # fps = time.clock()
        fpioa = FPIOA()
        fpioa.set_function(32,FPIOA.GPIO32)
        LASER_R = Pin(32, Pin.OUT, pull=Pin.PULL_UP, drive=15)
        
        # 设置绘图状态的回调函数
        def set_draw_state(component, event, state):
            global DRAW_STATE, shapes, current_shape
            DRAW_STATE = state
            if state == "IDLE":
                shapes = []
                current_shape = None
        
        ui = TouchUI(400, 240)
        # 添加控制按钮
        btn_laser = ui.add_button(0, 0, 100, 50, "激光开关", btn_callback)
        set_debug(False)
        
        back = image.Image(400, 240, image.RGB565)
        # ui.update(img)
        # Display.show_image(img,x=0,y=0)
#        _thread.start_new_thread(laser_detection, (1,))
        while True:
            os.exitpoint()
            img = sensor.snapshot(chn=CAM_CHN_ID_0)
            img.lens_corr(1.7)
            # motorx.velocity_control(1, 20, 0, False)
            redLaser = laser_detection(img)
            if redLaser is not None:
                img.draw_cross(redLaser[0], redLaser[1], color=(255, 0, 0), size=10, thickness=1)
                
                # 根据当前状态处理激光点
                # if DRAW_STATE == "IDLE":
                    # PID跟踪模式
                xout = round(pidx.compute(redLaser[0]))
                yout = round(pidy.compute(redLaser[1]))
                if xout > 0:
                    motorx.velocity_control(1, abs(xout), 0, False)
                else:
                    motorx.velocity_control(0, abs(xout), 0, False)
                if yout > 0:
                    motory.velocity_control(1, abs(yout), 0, False)
                else:
                    motory.velocity_control(0, abs(yout), 0, False)
                redLaser = None
                
#            motorx.velocity_control(0, 100, 0, False)  # 控制电机速度
            # a = u.read()
#            if a != None:
#                if a == b'\x01\xf6\x02\x6B':
#                    print("正确")``
#                print(a)
#                a = None
            # time.sleep_ms(200)
            
#            print(f"FPS: {fps.fps()}")
            # 绘制已完成的图形
            
            
            ui.update(img)
            Display.show_image(img,x=0,y=0,layer=Display.LAYER_OSD0)
#            Display.show_image(back,x=400,y=0,layer=Display.LAYER_OSD1)

    except KeyboardInterrupt as e:
        print("用户停止: ", e)
    except BaseException as e:
        print(f"异常: {e}")
    finally:
        # 停止传感器运行
        motorx.velocity_control(0, 0, 0, False)
        motory.velocity_control(0, 0, 0, False)
        if isinstance(sensor, Sensor):
            sensor.stop()
        # 反初始化显示模块
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
        time.sleep_ms(100)
        # 释放媒体缓冲区
        MediaManager.deinit()

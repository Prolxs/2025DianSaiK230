# 立创·庐山派-K230-CanMV开发板资料与相关扩展板软硬件资料官网全部开源
# 开发板官网：www.lckfb.com
# 技术支持常驻论坛，任何技术问题欢迎随时交流学习
# 立创论坛：www.jlc-bbs.com/lckfb
# 关注bilibili账号：【立创开发板】，掌握我们的最新动态！
# 不靠卖板赚钱，以培养中国工程师为己任

import time, os, sys, math
import image  # 添加image模块导入
import cv_lite                 # cv_lite扩展模块 / cv_lite extension module
import ulab.numpy as np
from media.sensor import *
from media.display import *
from media.media import *
from k230.serial import serial_2,serial_3,serial_4
from k230.motor import Motor
from k230.pid import Pid
from k230.laserDraw import *  # 导入图形绘制模块
from ui.ui_core import TouchUI,set_debug
from ui.components import ParameterControl
from machine import Pin
from machine import FPIOA
from k230.laserDraw import LaserCanvas
import _thread
from k230.findBlobs import *
import gc
# 全局状态变量
DRAW_STATE = "IDLE"  # 状态: IDLE, EXECUTING
#laser_canvas = LaserCanvas(320, 240)  # 创建绘图画布
#laser_canvas.set_origin(160, 120)    # 设置原点为中心
#import ulab.numpy as np     # MicroPython NumPy 类库
sensor = None
PID_Flag = True
# 红色激光点颜色阈值，可根据实际情况调整
RED_LASER_THRESHOLD = [(0, 100, -128, 33, -128, -40)]
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




def btn_BP_callback(component, event):
    # component.get_value()
    LASER_BP.value(LASER_BP.value() ^ 1)
#    print(f"当前值:{LASER_BP.value()}")

def btn_PID_callback(component, event):
    global PID_Flag
    motorx.velocity_control(0, 0, 0, False)
    motory.velocity_control(0, 0, 0, False)
    PID_Flag = not PID_Flag

def laser_detection(img):
    # lock.acquire()
    # 中值滤波
#    img = img.median(1)
    # img.gamma_corr(1.3)
#    print(img.size())
    Rxy = None
#    Gxy = None
    # 查找红色激光点
    red_blobs = img.find_blobs(RED_LASER_THRESHOLD, pixels_threshold=10, area_threshold=5, merge=True)
    
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


    # 显示图片
    # Display.show_image(img, x=0,y=0)
    # lock.release()
    return Rxy

def base_init():
    # 构造一个具有默认配置的摄像头对象
    sensor = Sensor(width=320,height=240)
    sensor.reset()
    sensor.set_framesize(width=320, height=240)
    # 设置通道0的输出像素格式为RGB888
    sensor.set_pixformat(Sensor.RGB888)
    # 根据模式初始化显示器
    if DISPLAY_MODE == "VIRT":
        Display.init(Display.VIRT, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, fps=60)
    elif DISPLAY_MODE == "LCD":
#        Display.init(Display.ILI9881, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
        Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)

    elif DISPLAY_MODE == "HDMI":
        Display.init(Display.LT9611, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    # 初始化媒体管理器
    MediaManager.init()
    # 启动传感器
    sensor.run()
    return sensor

        # 设置绘图状态的回调函数
def set_draw_state(component, event, state):
    global DRAW_STATE
    DRAW_STATE = state
    if state == "EXECUTING":
        laser_canvas.start_drawing(0)  # 开始绘制第一个图形

def disp_thread(ui,img, layer):
    try:
        ui.update(img)  # 修复：使用update方法更新UI
        Display.show_image(img, layer=layer)
    except RuntimeError as e:
        pass
    except ValueError as e:
        pass
        


if __name__ == "__main__":
#    global img
    threshold = [60, 110, 90, 125, 200, 255]
    try:
        redLaser = None
#        fps = time.clock()
#        sensor = base_init()
        motory_ctrl = serial_2()
        motorx_ctrl = serial_3()
        u = serial_4()
#        time.sleep_ms(100)
        motorx = Motor(motorx_ctrl, 0x01)  # 地址为0x01的电机对象
        motory = Motor(motory_ctrl, 0x01)  # 地址为0x01的电机对象
        motorx.enable_control(True,False)  # 使能电机控制
        motory.enable_control(True,False)  # 使能电机控制
        # P=0.5 D=0.13
        # X轴速度、加速度
        pidx = Pid(Kp=5, Ki=0.021, Kd=0.6, setpoint=160, sample_time=0.0,out_info=False)
        pidx.set_output_limits(-3200, 3200)
        # pidx_acc = Pid(Kp=2, Ki=0.5, Kd=1, setpoint=160, sample_time=0.0,out_info=False)
        # pidx_acc.set_output_limits(1, 255)
        
        # Y轴速度、加速度
        pidy = Pid(Kp=1, Ki=0, Kd=0, setpoint=120, sample_time=0.0,out_info=False)
        pidy.set_output_limits(-3200, 3200)
        # pidy_acc = Pid(Kp=0, Ki=0.0, Kd=0.0, setpoint=120, sample_time=0.0,out_info=False)
        # pidy_acc.set_output_limits(1, 255)
        # fps = time.clock()
        fpioa = FPIOA()
        fpioa.set_function(32,FPIOA.GPIO32)
        LASER_BP = Pin(32, Pin.OUT, pull=Pin.PULL_UP, drive=15)
        

        
        ui = TouchUI(800, 480)
       
        
        # 添加控制按钮
        btn_laserBP = ui.add_button(0, 360, 100, 50, "蓝紫", btn_BP_callback)
#        btn_heart = ui.add_button(600, 120, 100, 50, "爱心", btn_heart_callback)
        btn_start_draw = ui.add_button(200, 290, 100, 50, "开始绘图", lambda c,e: set_draw_state(c, e, "EXECUTING"))
        btn_PID = ui.add_button(0, 420, 100, 50, "PID", btn_PID_callback)
        set_Z = uiadd_button()
        set_debug(False)
       
            
        
        back = image.Image(800, 480, image.RGB888)
        back.clear()

        # 绘制测试图形
#        laser_canvas.add_rectangle(100,100,100,100,10)
#        laser_canvas.add_triangle(200,120,100,0)
#        laser_canvas.add_circle(160,120,60,128)
        # laser_canvas.add_heart(100, 100, 100)
#        laser_canvas.add_line(200,120,200,180,10)
#        laser_canvas.add_waveform(160,120,math.sin,-150,150,1,50,1)
        canny_thresh1       = 50        # Canny 边缘检测低阈值 / Canny edge low threshold
        canny_thresh2       = 150       # Canny 边缘检测高阈值 / Canny edge high threshold
        approx_epsilon      = 0.04      # 多边形拟合精度（比例） / Polygon approximation precision (ratio)
        area_min_ratio      = 0.001     # 最小面积比例（0~1） / Minimum area ratio (0~1)
        max_angle_cos       = 0.5       # 最大角余弦（值越小越接近矩形） / Max cosine of angle (smaller closer to rectangle)
        gaussian_blur_size  = 5         # 高斯模糊核大小（奇数） / Gaussian blur kernel size (odd number)
        keypoints = []
        while True:
            os.exitpoint()
            img = sensor.snapshot()
#            img.lens_corr(1.5)
#            motorx.velocity_control(0, 100, 0, False)
            motory.velocity_control(0, 100, 0, False)
#            Cxy = find_rectangles_565(img,MIN_AREA=10000,MAX_AREA=20000)
#            if Cxy is not None:
# #               xy = ((rect[0]+rect[2])//2,(rect[1]+rect[3])//2)
#                print(f"终点坐标:{Cxy}")
# #                print(rectpoints)
# #                img.draw_cross(Cxy[0], Cxy[1], color=(0, 255, 0), size=10, thickness=1)
#                pidx.setpoint = Cxy[0]
#                pidy.setpoint = Cxy[1]
#            redLaser = laser_detection(img)
#            if redLaser is not None:
#                img.draw_cross(redLaser[0], redLaser[1], color=(255, 0, 0), size=10, thickness=1)
                # pidx_acc.setpoint = Cxy[0]
                # pidy_acc.setpoint = Cxy[1]
#            rect = find_rectangles([320,240],img)
#            print(rect)
#            if len(rect) > 3:
#                img.draw_rectangle(rect[0],rect[1],rect[2],rect[3],color=(255,0,0),thickness=1)
            # 绘制测试图形
#            recData = find_blobs([320,240], img.to_rgb888(), threshold, min_area=20, kernel_size=1)
#            if recData is not None:
#                print(recData[0])
#                redLaser = recData[0]
                # 根据当前状态处理激光点
                # if DRAW_STATE == "EXECUTING":
                #     laser_canvas.update_position(redLaser[0], redLaser[1])
                #     # 绘图执行模式
                #     target = laser_canvas.get_next_target()
                #     if target:
                        
                #         # 设置PID目标点为绝对坐标 (原点+相对坐标)
                #         pidx.setpoint = laser_canvas.origin[0] + target[0]
                #         pidy.setpoint = laser_canvas.origin[1] + target[1]
                #         pidx_acc.setpoint = laser_canvas.origin[0] + target[0]
                #         pidy_acc.setpoint = laser_canvas.origin[1] + target[1]
                #         keypoints.append((round(pidx.setpoint),round(pidy.setpoint),1))
                #     elif laser_canvas.is_drawing_complete():
                #         keypoints.clear()
                #         # 绘图完成，返回IDLE状态
                #         DRAW_STATE = "IDLE"

#                if PID_Flag:
                    
#                    # PID控制（同时适用于IDLE和EXECUTING状态）
#                    xout = round(pidx.compute(redLaser[0]))
##                    xacc = 256 - round(pidx_acc.compute(redLaser[0]))
                    
#                    yout = round(pidy.compute(redLaser[1]))
##                    yacc = 256 - round(pidy_acc.compute(redLaser[1]))
#                    u.write(f"{pidy.setpoint},{redLaser[1]},{yout}\n")
#                    if xout > 0:
#                        motorx.position_control(0,1000,255,abs(xout),0, False)
#                    else:
#                        motorx.position_control(1,1000,255,abs(xout),0, False)
#                    if yout > 0:
#                       motory.position_control(1,1000,255,abs(yout),0, False)
#                    else:
#                       motory.position_control(0,1000,255,abs(yout),0, False)
#                    redLaser = None

            
#            img.draw_keypoints(keypoints,color=(255,0,0),size=10,thickness=1)
            ui.update(back)
            Display.show_image(img, layer=Display.LAYER_OSD1)
            _thread.start_new_thread(disp_thread, (ui, back, Display.LAYER_OSD0))
#            print(fps.fps())
            # _thread.start_new_thread(disp_thread, (img, Display.LAYER_OSD01))
            # Display.show_image(back, layer=Display.LAYER_OSD0)
            gc.collect()
            

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

# ============================================================
# MicroPython 基于 cv_lite 的 RGB888 矩形检测测试代码
# RGB888 Rectangle Detection Test using cv_lite extension
# ============================================================

import time, os, sys, gc
from machine import Pin
from media.sensor import *     # 摄像头接口 / Camera interface
from media.display import *    # 显示接口 / Display interface
from media.media import *      # 媒体资源管理器 / Media manager
import _thread
import cv_lite                 # cv_lite扩展模块 / cv_lite extension module
import ulab.numpy as np
import math
# from k230.findBlobs import find_blobs
# -------------------------------
# 图像尺寸 [高, 宽] / Image size [Height, Width]
# -------------------------------
CROP_WIDTH = 400
CROP_HEIGHT = 240
image_shape = [CROP_HEIGHT, CROP_WIDTH]
# -------------------------------
# 初始化摄像头（RGB888格式） / Initialize camera (RGB888 format)
# -------------------------------
sensor = Sensor(id=2,width=1920, height=1080, fps=60)
sensor.reset()

sensor.set_vflip(True)
sensor.set_hmirror(True)
sensor_width = sensor.width(None) # get sensor output width
sensor_height = sensor.height(None) # get sensor output width
sensor.set_framesize(width = CROP_WIDTH, height = CROP_HEIGHT)
sensor.set_pixformat(Sensor.RGB565)

# -------------------------------
# 初始化显示器（IDE虚拟显示输出） / Initialize display (IDE virtual output)
# -------------------------------
Display.init(Display.ST7701, width=800, height=480, to_ide=True)

# -------------------------------
# 初始化媒体资源管理器并启动摄像头 / Init media manager and start camera
# -------------------------------
MediaManager.init()
sensor.run()

# -------------------------------
# 可选增益设置（亮度/对比度调节）/ Optional sensor gain setting
# -------------------------------
gain = k_sensor_gain()
gain.gain[0] = 20
sensor.again(gain)

# -------------------------------
# 启动帧率计时器 / Start FPS timer
# -------------------------------
clock = time.clock()

# -------------------------------
# 矩形检测可调参数 / Adjustable rectangle detection parameters
# -------------------------------
canny_thresh1      = 50        # Canny 边缘检测低阈值 / Canny low threshold
canny_thresh2      = 150       # Canny 边缘检测高阈值 / Canny high threshold
approx_epsilon     = 0.04      # 多边形拟合精度比例（越小拟合越精确）/ Polygon approximation accuracy
area_min_ratio     = 0.001     # 最小面积比例（相对于图像总面积）/ Min area ratio
max_angle_cos      = 0.3       # 最大角度余弦（越小越接近矩形）/ Max cosine of angle between edges
gaussian_blur_size = 3        # 高斯模糊核尺寸（奇数）/ Gaussian blur kernel size

def laser_detection(img):
    # lock.acquire()
    # 中值滤波
#    img = img.median(1)
    # img.gamma_corr(1.3)
#    print(img.size())
    Rxy = None
#    Gxy = None
    # 查找红色激光点
    red_blobs = img.find_blobs([(0, 100, -128, 33, -128, -40)], pixels_threshold=10, area_threshold=5, merge=True)
    # 20, 60, 15, 70, -70, -20
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

from k230.serial import serial_2,serial_3,serial_4
from k230.motor import Motor
from k230.pid import Pid
PID_Flag = False
EN_Flag = True
turn_R_scan = False
turn_L_scan = False
Find_Flag = False
motory_ctrl = serial_2()
motorx_ctrl = serial_3()
motorx = Motor(motorx_ctrl, 0x01)  # 地址为0x01的电机对象
motory = Motor(motory_ctrl, 0x01)  # 地址为0x01的电机对象
motorx.enable_control(True,False)  # 使能电机控制
motory.enable_control(True,False)  # 使能电机控制
# X轴速度、加速度
pidx = Pid(Kp=0.8, Ki=0.00, Kd=1.9, setpoint=160, sample_time=0.00,out_info=False)
pidx.set_output_limits(-30, 30)
# pidx_acc = Pid(Kp=2, Ki=0.5, Kd=1, setpoint=160, sample_time=0.0,out_info=False)
# pidx_acc.set_output_limits(1, 255)
# Y轴速度、加速度
pidy = Pid(Kp=0.8, Ki=0.00, Kd=1.9, setpoint=120, sample_time=0.00,out_info =False)
pidy.set_output_limits(-30, 30)
# pidy_acc = Pid(Kp=0, Ki=0.0, Kd=0.0, setpoint=120, sample_time=0.0,out_info=False)
# pidy_acc.set_output_limits(1, 255)
# fps = time.clock()

from machine import Pin
from machine import FPIOA
fpioa = FPIOA()
fpioa.set_function(32,FPIOA.GPIO32)
LASER_BP = Pin(32, Pin.OUT, pull=Pin.PULL_DOWN, drive=15)
def btn_BP_callback(component, event):
    # component.get_value()
    LASER_BP.value(LASER_BP.value() ^ 1)

from ui.ui_core import TouchUI,set_debug
def btn_PID_callback(component, event):
    global PID_Flag
    motorx.velocity_control(0, 0, 0, False)
    motory.velocity_control(0, 0, 0, False)
    PID_Flag = not PID_Flag
def btn_CHECK_callback(component, event):
    global BlueLaserFlag
    BlueLaserFlag = not BlueLaserFlag
def set_z_callback(component, event):
    motorx.set_homing_position(True)
    x = motorx.serial.read()
#    print(x)
    motory.set_homing_position(True)
def back_z_callback(component, event):
    motorx.enable_control(True,False)
    motory.enable_control(True,False)
    motorx.homing_trigger(0,False)
    motory.homing_trigger(0,False)
def en_motor_callback(component, event):
    global EN_Flag
    EN_Flag = not EN_Flag
    if EN_Flag:
        motorx.enable_control(True,False)
        motory.enable_control(True,False)
    else:
        motorx.enable_control(False,False)
        motory.enable_control(False,False)
def btn_R_callback(component, event):
    global PID_Flag,turn_R_scan,Find_Flag

    motory.enable_control(True,False)
    time.sleep(0.005)
    motory.homing_trigger(0,False)
    time.sleep(0.005)
    motorx.velocity_control(1,200,0, False)
    time.sleep(0.005)
    PID_Flag = False
    Find_Flag = False
    turn_R_scan = True #开启右扫描
#    print("R")

def btn_L_callback(component, event):
    global PID_Flag,turn_L_scan,Find_Flag
    motory.enable_control(True,False)
    time.sleep(0.005)
    motory.homing_trigger(0,False)
    time.sleep(0.005)
    motorx.velocity_control(0,200,0, False)
    time.sleep(0.005)
    PID_Flag = False
    Find_Flag = False
    turn_L_scan = True #开启左扫描
#    print("L")

def clear_btn_callback(component, event):
    global turn_R_scan,turn_L_scan
    turn_R_scan = False
    turn_L_scan = False

back = image.Image(800, 480, image.RGB888)
back.clear()
ui = TouchUI(800, 480)
btn_PID = ui.add_button(0, 420, 100, 50, "PID", btn_PID_callback)
btn_CHECK = ui.add_button(150, 420, 100, 50, "校准", btn_CHECK_callback)
btn_laserBP = ui.add_button(300, 420, 100, 50, "蓝紫", btn_BP_callback)
set_z = ui.add_button(450, 420, 100, 50, "设置Z", set_z_callback)
back_z = ui.add_button(600, 420, 100, 50, "回原点", back_z_callback)
btn_en_motor = ui.add_button(0, 320, 100, 50, "电机使能", en_motor_callback)
btn_R = ui.add_button(420, 50, 100, 50, "找点R", btn_R_callback)
btn_L = ui.add_button(570, 50, 100, 50, "找点L", btn_L_callback)
clear_btn = ui.add_button(420, 150,100,50,"清除", clear_btn_callback)
set_debug(False)

from k230.button import Key

import _thread
# 原有筛选参数
MIN_AREA = 1000               # 最小面积阈值
MAX_AREA = 100000             # 最大面积阈值
MIN_ASPECT_RATIO = 0.3        # 最小宽高比
MAX_ASPECT_RATIO = 3.0        # 最大宽高比
def calculate_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])** 2)
def sort_corners(corners):
    """将矩形角点按左上、右上、右下、左下顺序排序"""
    center = calculate_center(corners)
    sorted_corners = sorted(corners, key=lambda p: math.atan2(p[1]-center[1], p[0]-center[0]))

    # 调整顺序为左上、右上、右下、左下
    if len(sorted_corners) == 4:
        left_top = min(sorted_corners, key=lambda p: p[0]+p[1])
        index = sorted_corners.index(left_top)
        sorted_corners = sorted_corners[index:] + sorted_corners[:index]
    return sorted_corners
def calculate_center(points):
    if not points:
        return (0, 0)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    return (sum_x / len(points), sum_y / len(points))
def is_valid_rect(corners):
    edges = [calculate_distance(corners[i], corners[(i+1)%4]) for i in range(4)]

    # 对边比例校验
    ratio1 = edges[0] / max(edges[2], 0.1)
    ratio2 = edges[1] / max(edges[3], 0.1)
    valid_ratio = 0.5 < ratio1 < 1.5 and 0.5 < ratio2 < 1.5

    # 面积校验
    area = 0
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i+1) % 4]
        area += (x1 * y2 - x2 * y1)
    area = abs(area) / 2
    valid_area = MIN_AREA < area < MAX_AREA

    # 宽高比校验
    width = max(p[0] for p in corners) - min(p[0] for p in corners)
    height = max(p[1] for p in corners) - min(p[1] for p in corners)
    aspect_ratio = width / max(height, 0.1)
    valid_aspect = MIN_ASPECT_RATIO < aspect_ratio < MAX_ASPECT_RATIO

    return valid_ratio and valid_area and valid_aspect
# -------------------------------
# 主循环 / Main loop
# -------------------------------
BlueLaserFlag = True
DisplayFlag = True
key = Key()
cross = (200,120)
while True:
    clock.tick()
    if key.read():
        DisplayFlag = not DisplayFlag
#    motory.velocity_control(0,100,10, False)
    # 拍摄当前帧图像 / Capture current frame
    img = sensor.snapshot()
    if BlueLaserFlag is False:
        redLaser = laser_detection(img)
        if redLaser is not None:
            cross = redLaser
            BlueLaserFlag = True
#    img.lens_corr(2.0)
    gray_img = img.to_grayscale()
    img_np = gray_img.to_numpy_ref()  # 获取 RGB565 ndarray 引用 / Get RGB888 ndarray reference
#    img_np = img.to_numpy_ref()

    # 调用底层矩形检测函数
    # 返回格式：[[x0, y0, w0, h0, c1.x, c1.y, c2.x, c2.y, c3.x, c3.y, c4,x, c4.y], [x1, y1, w1, h1,c1.x, c1.y, c2.x, c2.y, c3.x, c3.y, c4,x, c4.y], ...]
    rects = cv_lite.grayscale_find_rectangles_with_corners(
        image_shape, img_np,
        canny_thresh1, canny_thresh2,
        approx_epsilon,
        area_min_ratio,
        max_angle_cos,
        gaussian_blur_size
    )
    min_area = float('inf')
    smallest_rect = None
    smallest_rect_corners = None  # 存储最小矩形的角点

    # 遍历检测到的矩形并绘制矩形框和角点
    for rect in rects:
        # rect格式: [x, y, w, h, c1.x, c1.y, c2.x, c2.y, c3.x, c3.y, c4.x, c4.y]
        x, y, w, h = rect[0], rect[1], rect[2], rect[3]
        # 提取四个角点
        corners = [
            (rect[4], rect[5]),   # 角点1
            (rect[6], rect[7]),   # 角点2
            (rect[8], rect[9]),   # 角点3
            (rect[10], rect[11])  # 角点4
        ]

        # 验证矩形有效性
        if is_valid_rect(corners):
            # 计算面积
            area = w * h  # 直接使用矩形宽高计算面积（更高效）
            # 更新最小矩形
            if area < min_area:
                min_area = area
                smallest_rect = (x, y, w, h)
                smallest_rect_corners = corners
    
    # 4. 处理最小矩形（修改后：固定虚拟矩形方向）
    if smallest_rect and smallest_rect_corners:
        x, y, w, h = smallest_rect
        corners = smallest_rect_corners

        # 对矩形角点进行排序
        sorted_corners = sort_corners(corners)

        # 绘制矩形边框和角点
        for i in range(4):
            x1, y1 = sorted_corners[i]
            x2, y2 = sorted_corners[(i+1) % 4]
            img.draw_line(x1, y1, x2, y2, color=(255, 0, 0), thickness=2)
        for p in sorted_corners:
            img.draw_circle(p[0], p[1], 5, color=(0, 255, 0), thickness=2)

        # 计算并绘制矩形中心点
        rect_center = calculate_center(sorted_corners)
        xy = (round(rect_center[0]),round(rect_center[1]))
        
        
        img.draw_cross(xy[0], xy[1], color=(0, 255, 0), size=3, thickness=1)
        Find_Flag = True
        pidx.setpoint = xy[0]
        pidy.setpoint = xy[1]
    
    if turn_R_scan and not turn_L_scan:
        
        if Find_Flag:
            turn_R_scan = False
            motorx.velocity_control(0,0,0, False)

            PID_Flag = True
    if turn_L_scan and not turn_R_scan:

        if Find_Flag:
            turn_L_scan = False
            motorx.velocity_control(0,0,0, False)

            PID_Flag = True


    if cross is not None:
#        print(cross)
        if PID_Flag:
            
            # PID控制（同时适用于IDLE和EXECUTING状态）
            xout = round(pidx.compute(cross[0]))
    #                    xacc = 256 - round(pidx_acc.compute(redLaser[0]))
            
            yout = round(pidy.compute(cross[1]))
    #                    yacc = 256 - round(pidy_acc.compute(redLaser[1]))
            # u.write(f"{pidy.setpoint},{redLaser[1]},{yout}\n")
            if xout > 0:
               motorx.velocity_control(1,abs(xout),0, False)
            else:
               motorx.velocity_control(0,abs(xout),0, False)
            if yout > 0:
               motory.velocity_control(1,abs(yout),0, False)
            else:
               motory.velocity_control(0,abs(yout),0, False)
#            if xout > 0:
#                motorx.position_control(1,400,190,abs(xout),0, False)
#            else:
#                motorx.position_control(0,400,190,abs(xout),0, False)
#            if yout > 0:
#               motory.position_control(1,100,100,abs(yout),0, False)
#            else:

#               motory.position_control(0,100,100,abs(yout),0, False)
        img.draw_cross(cross[0], cross[1], color=(255, 0, 0), size=3, thickness=1)
    
    if DisplayFlag:
        Display.show_image(img,layer=Display.LAYER_OSD1)
        ui.update(back)  # 修复：使用update方法更新UI
        Display.show_image(back, layer=Display.LAYER_OSD0)
    # 释放临时变量内存 / Free temporary variables memory
    del img_np
    del img
    del gray_img
#    fps_text.set_text(f"FPS: {int(clock.fps())}")
#    try:
#        _thread.start_new_thread(disp_thread, (ui, back, Display.LAYER_OSD0))
#    except OSErrora as e :
#        pass
#    global back

#    del back
    # 进行垃圾回收 / Perform garbage collection
    gc.collect()

    # 打印当前帧率和检测到的矩形数量 / Print current FPS and number of detected rectangles
#    print("fps:", clock.fps())

# -------------------------------
# 退出时释放资源 / Cleanup on exit
# -------------------------------
sensor.stop()
Display.deinit()
os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
time.sleep_ms(100)
MediaManager.deinit()

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
import json  # 添加JSON导入
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
# sensor.set_framesize(width = CROP_WIDTH, height = CROP_HEIGHT, crop = ((sensor_width - CROP_WIDTH) // 2, (sensor_height - CROP_HEIGHT) // 2, CROP_WIDTH, CROP_HEIGHT))

# , crop = ((sensor_width - CROP_WIDTH) // 2, (sensor_height - CROP_HEIGHT) // 2, CROP_WIDTH, CROP_HEIGHT)
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
#gain = k_sensor_gain()
#gain.gain[0] = 20
#sensor.again(gain)

# -------------------------------
# 启动帧率计时器 / Start FPS timer
# -------------------------------
clock = time.clock()

# -------------------------------
# 矩形检测可调参数 / Adjustable rectangle detection parameters
# -------------------------------
canny_thresh1      = 50        # Canny 边缘检测低阈值 / Canny low threshold
canny_thresh2      = 150       # Canny 边缘检测高阈值 / Canny high threshold
approx_epsilon     = 0.05      # 多边形拟合精度比例（越小拟合越精确）/ Polygon approximation accuracy
area_min_ratio     = 0.0005     # 最小面积比例（相对于图像总面积）/ Min area ratio
max_angle_cos      = 0.6       # 最大角度余弦（越小越接近矩形）/ Max cosine of angle between edges
gaussian_blur_size = 3        # 高斯模糊核尺寸（奇数）/ Gaussian blur kernel size

RECT_WIDTH = 210    # 固定矩形宽度
RECT_HEIGHT = 95    # 固定矩形高度
BASE_RADIUS = 45              # 基础半径（虚拟坐标单位）
POINTS_PER_CIRCLE = 24        # 圆形采样点数量
def laser_detection(img):
    # 查找蓝色激光点（根据用户说明实际检测蓝色激光）
    blue_blobs = img.find_blobs([(0, 100, -128, 33, -128, -40)], pixels_threshold=10, area_threshold=5, merge=True)
    
    if blue_blobs:
        sumX = 0
        sumY = 0
        for blob in blue_blobs:
            # 获取激光点的中心位置
            sumX += blob.cx()
            sumY += blob.cy()
        num = len(blue_blobs)
        if num:
            return (int(sumX/num), int(sumY/num))
    return None

from k230.serial import serial_2,serial_3,serial_4
from k230.motor import Motor
from k230.pid import Pid
PID_Flag = False
Loop_Flag = False
EN_Flag = True
turn_R_scan = False
turn_L_scan = False
Find_Flag = False
loop_dis = [1,1,0,1]
loop_index = 0
motory_ctrl = serial_2()
motorx_ctrl = serial_3()
test_u = serial_4()
motorx = Motor(motorx_ctrl, 0x01)  # 地址为0x01的电机对象
motory = Motor(motory_ctrl, 0x01)  # 地址为0x01的电机对象
motorx.enable_control(True,False)  # 使能电机控制
motory.enable_control(True,False)  # 使能电机控制
# X轴速度、加速度
pidx = Pid(Kp=4, Ki=0.00, Kd=2.5, setpoint=200, sample_time=0.00,out_info=False)
pidx.dead_zone = 1
pidx.set_output_limits(-120, 120)
pidxacc = Pid(Kp=2, Ki=0.00, Kd=1, setpoint=200, sample_time=0.00,out_info=False)
pidxacc.dead_zone = 0
pidxacc.set_output_limits(1, 255)
# pidx_turnRight = Pid(Kp=1, Ki=0.00, Kd=1.9, setpoint=0, sample_time=0.00,out_info=False)
# Y轴速度、加速度
pidy = Pid(Kp=2, Ki=0.00, Kd=2.4, setpoint=120, sample_time=0.00,out_info =False)
pidy.set_output_limits(-90, 90)
pidy.dead_zone = 1
from machine import Pin
from machine import FPIOA
fpioa = FPIOA()
fpioa.set_function(32,FPIOA.GPIO32)
LASER_BP = Pin(32, Pin.OUT, pull=Pin.PULL_DOWN, drive=15)
def btn_BP_callback(component, event):
    # print(LASER_BP.value())
    LASER_BP.value(LASER_BP.value() ^ 1)

from ui.ui_core import TouchUI,set_debug


def btn_PID_callback(component, event):
    global PID_Flag
    motorx.velocity_control(0, 0, 0, False)
    motory.velocity_control(0, 0, 0, False)
    PID_Flag = not PID_Flag
    text.set_text("PID: " + str(PID_Flag))
def btn_CHECK_callback(component, event):
    global BlueLaserFlag
    BlueLaserFlag = not BlueLaserFlag
    text.set_text("CHECK: " + str(BlueLaserFlag))
def set_z_callback(component, event):
    motorx.set_homing_position(True)
    motory.set_homing_position(True)
    
    text.set_text("已设置")
def back_z_callback(component, event):
#    PID_Flag = True
    global PID_Flag
    motorx.enable_control(True,False)
    motory.enable_control(True,False)
    time.sleep(0.005)
    motorx.homing_trigger(0,False)
    motory.homing_trigger(0,False)
    PID_Flag = True
    text.set_text("已回原点")
    
    
def en_motor_callback(component, event):
    global EN_Flag
    EN_Flag = not EN_Flag
    if EN_Flag:
        motorx.enable_control(True,False)
        motory.enable_control(True,False)
        text.set_text("电机使能: 已开启")
    else:
        motorx.enable_control(False,False)
        motory.enable_control(False,False)
        text.set_text("电机使能: 已关闭")
def btn_R_callback(component, event):
    global PID_Flag,turn_R_scan,Find_Flag
    motory.enable_control(True,False)
    time.sleep(0.005)
    motorx.enable_control(True,False)
    time.sleep(0.005)
    motory.homing_trigger(0,False)
    time.sleep(0.005)
    motorx.velocity_control(1,200,0, False)
    time.sleep(0.005)
    PID_Flag = False
    Find_Flag = False
    turn_R_scan = True #开启右扫描
    text.set_text("已开启右扫描")

def btn_L_callback(component, event):
    global PID_Flag,turn_L_scan,Find_Flag
    motory.enable_control(True,False)
    time.sleep(0.005)
    motorx.enable_control(True,False)
    time.sleep(0.005)
    motory.homing_trigger(0,False)
    time.sleep(0.005)
    motorx.velocity_control(0,200,0, False)
    time.sleep(0.005)
    PID_Flag = False
    Find_Flag = False
    turn_L_scan = True #开启左扫描
    text.set_text("已开启左扫描")

def clear_btn_callback(component, event):
    global turn_R_scan,turn_L_scan
    turn_R_scan = False
    turn_L_scan = False
    text.set_text("已清除扫描")

def loop_line_mode_callback(component, event):
    global PID_Flag,Loop_Flag
    Loop_Flag = not Loop_Flag
    if Loop_Flag:

        motory.enable_control(True,False)
        time.sleep(0.005)
        motorx.enable_control(True,False)
        time.sleep(0.005)
        text.set_text("巡线模式开启")
        PID_Flag = True
        LASER_BP.value(1)
    else:
        pidx.Kp = 4
        pidx.Ki = 0
        pidx.Kd = 2.5
        text.set_text("巡线模式关闭")
        PID_Flag = False
        Loop_Flag = False
        LASER_BP.value(0)

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
loop_line_mode = ui.add_button(570,150,100,50,"巡线模式", loop_line_mode_callback)
text = ui.add_static_text(150, 320, 20, "待指示",(255,255,255))

# ================== 阈值调节控件 ==================
# 可调参数
params = {
    "canny_thresh1": 50,
    "canny_thresh2": 150,
    "approx_epsilon": 0.05,
    "area_min_ratio": 0.0005,
    "max_angle_cos": 0.6,
    "gaussian_blur_size": 3
}
param_names = list(params.keys())
current_index = 0
storage_path = "/sdcard/calibration_coordinates.json"

# 创建UI元素 (空闲区域: x=410, y=250)
param_name_text = ui.add_static_text(410, 250, 20, "Parameter: ", (255,255,255))
param_value_text = ui.add_static_text(410, 280, 20, "Value: ", (255,255,255))
prev_button = ui.add_button(410, 310, 60, 30, "Prev", lambda c,e: prev_param())
next_button = ui.add_button(480, 310, 60, 30, "Next", lambda c,e: next_param())
inc_button = ui.add_button(410, 350, 40, 30, "+", lambda c,e: change_value(1))
dec_button = ui.add_button(460, 350, 40, 30, "-", lambda c,e: change_value(-1))

def load_params():
    """从文件加载参数，同时保留激光坐标"""
    global params
    try:
        with open(storage_path, 'r') as f:
            data = json.load(f)
            if "params" in data:
                for key, value in data["params"].items():
                    if key in params:
                        params[key] = value
    except Exception as e:
        print(f"加载参数失败: {e}")

def save_params():
    """保存参数到文件，同时保留激光坐标"""
    try:
        data = {}
        # 尝试读取现有文件
        try:
            with open(storage_path, 'r') as f:
                data = json.load(f)
        except OSError:  # 文件不存在时忽略
            pass
        
        data["params"] = params
        with open(storage_path, 'w') as f:
            json.dump(data, f)  # MicroPython不支持indent参数
        print(f"参数保存成功: {params}")
    except Exception as e:
        print(f"保存参数失败: {e}")
        
def load_params():
    """从文件参数，同时保留激光坐标"""
    global params
    try:
        # 尝试打开文件
        with open(storage_path, 'r') as f:
            data = json.load(f)
            if "params" in data:
                for key, value in data["params"].items():
                    if key in params:
                        params[key] = value
                print(f"从文件加载参数: {params}")
    except OSError:  # 文件不存在时忽略
        print("参数文件不存在，使用默认参数")
    except Exception as e:
        print(f"加载参数失败: {e}")

def get_current_param():
    """获取当前参数名和值"""
    name = param_names[current_index]
    return name, params[name]

def update_display():
    """更新UI显示"""
    name, value = get_current_param()
    param_name_text.text = f"Parameter: {name}"
    if isinstance(value, float):
        param_value_text.text = f"Value: {value:.4f}"
    else:
        param_value_text.text = f"Value: {value}"

def prev_param():
    """切换到上一个参数"""
    global current_index
    current_index = (current_index - 1) % len(param_names)
    update_display()
    save_params()

def next_param():
    """切换到下一个参数"""
    global current_index
    current_index = (current_index + 1) % len(param_names)
    update_display()
    save_params()

def change_value(delta):
    """改变当前参数值"""
    name, value = get_current_param()
    if name == "gaussian_blur_size":
        # 确保为奇数
        params[name] = max(1, value + 2*delta)
    elif name == "max_angle_cos":
        params[name] = max(-1.0, min(1.0, value + 0.05*delta))
    else:
        params[name] = max(0, value + delta)
    update_display()
    save_params()

# 初始加载参数
load_params()
update_display()
# ==================================================




set_debug(False)

from k230.button import Key

# 坐标持久化函数定义
def save_coordinates(laser_coord):
    """
    保存激光坐标到JSON文件
    :param laser_coord: 激光坐标 (x, y)
    """
    coordinates = {
        "laser": {"x": laser_coord[0], "y": laser_coord[1]}
    }
    try:
        with open("/sdcard/calibration_coordinates.json", "w") as f:
            json.dump(coordinates, f)
        return True
    except Exception as e:
        print(f"保存坐标失败: {e}")
        return False

def load_coordinates():
    """
    从JSON文件加载激光坐标
    返回: 激光坐标元组 (x, y)，如果文件不存在则返回None
    """
    try:
        with open("/sdcard/calibration_coordinates.json", "r") as f:
            data = json.load(f)
            return (data["laser"]["x"], data["laser"]["y"])
    except OSError:  # MicroPython使用OSError代替FileNotFoundError
        print("坐标文件不存在，使用默认坐标")
        return None
    except Exception as e:
        print(f"加载坐标失败: {e}")
        return None

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
    ratio1 = edges[0] / max(edges[2], 0.1)
    ratio2 = edges[1] / max(edges[3], 0.1)
    valid_ratio = 0.5 < ratio1 < 1.5 and 0.5 < ratio2 < 1.5
    area = 0
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i+1) % 4]
        area += (x1 * y2 - x2 * y1)
    area = abs(area) / 2
    valid_area = MIN_AREA < area < MAX_AREA
    width = max(p[0] for p in corners) - min(p[0] for p in corners)
    height = max(p[1] for p in corners) - min(p[1] for p in corners)
    aspect_ratio = width / max(height, 0.1)
    valid_aspect = MIN_ASPECT_RATIO < aspect_ratio < MAX_ASPECT_RATIO
    return valid_ratio and valid_area and valid_aspect
def get_rectangle_orientation(corners):
    """计算矩形的主方向角（水平边与x轴的夹角）"""
    if len(corners) != 4:
        return 0

    # 计算上边和右边的向量
    top_edge = (corners[1][0] - corners[0][0], corners[1][1] - corners[0][1])
    right_edge = (corners[2][0] - corners[1][0], corners[2][1] - corners[1][1])

    # 选择较长的边作为主方向
    if calculate_distance(corners[0], corners[1]) > calculate_distance(corners[1], corners[2]):
        main_edge = top_edge
    else:
        main_edge = right_edge

    # 计算主方向角（弧度）
    angle = math.atan2(main_edge[1], main_edge[0])
    return angle

def get_perspective_matrix(src_pts, dst_pts):
    """计算透视变换矩阵"""
    A = []
    B = []
    for i in range(4):
        x, y = src_pts[i]
        u, v = dst_pts[i]
        A.append([x, y, 1, 0, 0, 0, -u*x, -u*y])
        A.append([0, 0, 0, x, y, 1, -v*x, -v*y])
        B.append(u)
        B.append(v)

    # 高斯消元求解矩阵
    n = 8
    for i in range(n):
        max_row = i
        for j in range(i, len(A)):
            if abs(A[j][i]) > abs(A[max_row][i]):
                max_row = j
        A[i], A[max_row] = A[max_row], A[i]
        B[i], B[max_row] = B[max_row], B[i]

        pivot = A[i][i]
        if abs(pivot) < 1e-8:
            return None
        for j in range(i, n):
            A[i][j] /= pivot
        B[i] /= pivot

        for j in range(len(A)):
            if j != i and A[j][i] != 0:
                factor = A[j][i]
                for k in range(i, n):
                    A[j][k] -= factor * A[i][k]
                B[j] -= factor * B[i]

    return [
        [B[0], B[1], B[2]],
        [B[3], B[4], B[5]],
        [B[6], B[7], 1.0]
    ]
def transform_points(points, matrix):
    """应用透视变换将虚拟坐标映射到原始图像坐标"""
    transformed = []
    for (x, y) in points:
        x_hom = x * matrix[0][0] + y * matrix[0][1] + matrix[0][2]
        y_hom = x * matrix[1][0] + y * matrix[1][1] + matrix[1][2]
        w_hom = x * matrix[2][0] + y * matrix[2][1] + matrix[2][2]
        if abs(w_hom) > 1e-8:
            transformed.append((x_hom / w_hom, y_hom / w_hom))
    return transformed
# 主循环
BlueLaserFlag = True
DisplayFlag = True
key = Key()

def shot_laser():
    LASER_BP.value(1)
    time.sleep_ms(150)
    LASER_BP.value(0)

# 加载保存的坐标
saved_coord = load_coordinates()
if saved_coord:
    cross = saved_coord
    print(f"加载坐标成功: {cross}")
else:
    cross = (200,120)
    print("使用默认坐标")
def parse_pid_parameters(byte_string):
    # 将字节字符串解码为普通字符串
    string_data = byte_string.decode('utf-8')
    
    # 分割键值对
    pairs = string_data.split(',')
    
    # 初始化变量
    kp = ki = kd = None
    
    # 遍历键值对并提取值
    for pair in pairs:
        key, value = pair.split('=')
        if key == 'kp':
            kp = float(value)
        elif key == 'ki':
            ki = float(value)
        elif key == 'kd':
            kd = float(value)
    
    return kp, ki, kd
from machine import Pin
from machine import FPIOA
right_top = None
fpioa = FPIOA()
fpioa.set_function(42, FPIOA.GPIO53)
Turn = Pin(42, Pin.IN, Pin.PULL_DOWN)
while True:
    try:
        clock.tick()
        if key.read():
            # print(1)
            # shot_laser()
            DisplayFlag = not DisplayFlag
        if not Loop_Flag:
            if pidx.arrived and pidy.arrived:
                shot_laser()
                PID_Flag = False
                motorx.velocity_control(0,0,0, False)
                motory.velocity_control(0,0,0, False)
                pidy.arrived = False
                pidx.arrived = False
        meg = test_u.read()
        if meg is not None:
            kp, ki, kd = parse_pid_parameters(meg)
            pidx.Kp = kp
            pidx.Ki = ki
            pidx.Kd = kd
            print(f"更新PID参数: kp={pidx.Kp}, ki={pidx.Ki}, kd={pidx.Kd}")
            meg = None
        # 1. 读取摄像头图像 / Read camera image
        # 拍摄当前帧图像
        img = sensor.snapshot()
        
        # 蓝色激光校准逻辑
        if BlueLaserFlag is False:
            blueLaser = laser_detection(img)
            if blueLaser is not None:
                cross = blueLaser
                BlueLaserFlag = True
                save_coordinates(blueLaser)  # 保存校准后的坐标
                print(f"校准完成并保存坐标: {blueLaser}")
    
        gray_img = img.to_grayscale()
#        gray_img.histeq(adaptive=True)x`x`x
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
            right_top = sorted_corners[1]
            # 绘制矩形边框和角点
            for i in range(4):
                x1, y1 = sorted_corners[i]
                x2, y2 = sorted_corners[(i+1) % 4]
                img.draw_line(x1, y1, x2, y2, color=(255, 0, 0), thickness=2)
            for p in sorted_corners:
                img.draw_circle(p[0], p[1], 5, color=(0, 255, 0), thickness=2)
    
            # # 计算并绘制矩形中心点
            # rect_center = calculate_center(sorted_corners)
            # xy = (round(rect_center[0]),round(rect_center[1]))
            
            
            # img.draw_cross(xy[0], xy[1], color=(0, 255, 0), size=3, thickness=1)
            # Find_Flag = True
            # pidx.setpoint = xy[0]
            # pidy.setpoint = xy[1]
            # pidxacc.setpoint = xy[0]
            rect_center = calculate_center(sorted_corners)
            rect_center_int = (int(round(rect_center[0])), int(round(rect_center[1])))
            img.draw_circle(rect_center_int[0], rect_center_int[1], 4, color=(0, 255, 255), thickness=2)

            # 计算矩形主方向角（仅用于参考，不再影响虚拟矩形方向）
            angle = get_rectangle_orientation(sorted_corners)

            # 【核心修改】移除自动切换方向逻辑，固定使用预设的虚拟矩形尺寸和方向
            # 固定虚拟矩形（不再根据实际宽高比切换）
            virtual_rect = [
                (0, 0),
                (RECT_WIDTH, 0),
                (RECT_WIDTH, RECT_HEIGHT),
                (0, RECT_HEIGHT)
            ]

            # 【核心修改】固定圆形半径参数（不再根据实际宽高比调整）
            radius_x = BASE_RADIUS
            radius_y = BASE_RADIUS

            # 【核心修改】固定虚拟中心（基于固定的宽高）
            virtual_center = (RECT_WIDTH / 2, RECT_HEIGHT / 2)

            # 在虚拟矩形中生成椭圆点集（映射后为正圆）
            # virtual_circle_points = []
            # for i in range(POINTS_PER_CIRCLE):
            #     angle_rad = 2 * math.pi * i / POINTS_PER_CIRCLE
            #     x_virt = virtual_center[0] + radius_x * math.cos(angle_rad)
            #     y_virt = virtual_center[1] + radius_y * math.sin(angle_rad)
                # virtual_circle_points.append((x_virt, y_virt))

            # 计算透视变换矩阵并映射坐标
            matrix = get_perspective_matrix(virtual_rect, sorted_corners)
            if matrix:
                # mapped_points = transform_points(virtual_circle_points, matrix)
                # int_points = [(int(round(x)), int(round(y))) for x, y in mapped_points]

                # # 绘制圆形
                # for (px, py) in int_points:
                #     img.draw_circle(px, py, 2, color=(255, 0, 255), thickness=2)

                # 绘制圆心
                mapped_center = transform_points([virtual_center], matrix)
                if mapped_center:
                    cx, cy = map(int, map(round, mapped_center[0]))
                    # img.draw_circle(cx, cy, 3, color=(0, 0, 255), thickness=1)
                    # xy = (round(rect_center[0]),round(rect_center[1]))
                    img.draw_cross(cx, cy, color=(0, 255, 0), size=3, thickness=1)
                    Find_Flag = True
                    pidx.setpoint = cx
                    pidy.setpoint = cy
                    pidxacc.setpoint = cx
        
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
        if Loop_Flag:
            if Turn.value():
                PID_Flag = False
#                motorx.velocity_control(0,0,0, False)
#                motorx.position_control(
#                    direction=loop_dis[loop_index],           # 反方向
#                    velocity=1000,            # 100 RPM，对应输入值（注意缩放）
#                    acceleration=50,          # 合理加速度
#                    position=800,             # 对应90°
#                    relative_absolute=True,   # 相对运动
#                    sync_flag=False           # 独立控制
#                )
#                time.sleep(0.6)
                loop_index += 1
                if loop_index >= len(loop_dis):
                    loop_index = 0
                if loop_index == 0:
                    pidx.Kp = 4
                    pidx.Ki = 0
                    pidx.Kd = 2.5
                else:
                    pidx.Kp = 7
                    pidx.Ki = 0.025
                    pidx.Kd = 5
                PID_Flag = True
            
            
#            else: 
##                motorx.velocity_control(1,0,0, False)
#                PID_Flag = True
            
        if cross is not None:
    #        print(cross)
            if PID_Flag:
                
                # PID控制（同时适用于IDLE和EXECUTING状态）
                xout = round(pidx.compute(cross[0]))
        #                    xacc = 256 - round(pidx_acc.compute(redLaser[0]))
                xacc = round(pidxacc.compute(cross[0]))
                yout = round(pidy.compute(cross[1]))
        #                    yacc = 256 - round(pidy_acc.compute(redLaser[1]))
                test_u.write(f"{xout},{pidx.setpoint},{cross[0]},{pidx.Kd},{pidx.Ki},{pidx.Kp}\r\n")
                if xout > 0:
                   motorx.velocity_control(1,abs(xout),256-xacc, False)
                else:
                   motorx.velocity_control(0,abs(xout),256-xacc, False)
                if yout > 0:
                   motory.velocity_control(0,abs(yout),0, False)
                else:
                   motory.velocity_control(1,abs(yout),0, False)
            img.draw_cross(cross[0], cross[1], color=(255, 0, 0), size=3, thickness=1)
        
        if DisplayFlag:
            Display.show_image(img,layer=Display.LAYER_OSD1)
            ui.update(back)  # 这会自动绘制所有UI组件，包括threshold_adjuster
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
#        print(f"fps: {clock.fps()}")
        # 进行垃圾回收 / Perform garbage collection
        gc.collect()
    except KeyboardInterrupt as e:
        print("用户停止: ", e)
    except BaseException as e:
        pass
#        sensor.stop()
#        Display.deinit()
#        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
#        time.sleep_ms(100)
#        MediaManager.deinit()
#        print(f"异常: {e}")
# 退出时释放资源

sensor.stop()
Display.deinit()
os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
time.sleep_ms(100)
MediaManager.deinit()

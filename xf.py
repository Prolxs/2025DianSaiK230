import time, os, sys
import math
import cv_lite  # 导入cv_lite扩展模块
import ulab.numpy as np  # 导入numpy库
from media.sensor import *
from media.display import *
from media.media import *
from machine import UART, FPIOA

# --------------------------- 硬件初始化 ---------------------------
# 串口初始化
fpioa = FPIOA()
fpioa.set_function(3, FPIOA.UART1_TXD)
fpioa.set_function(4, FPIOA.UART1_RXD)
uart = UART(UART.UART1, 115200)

# 屏幕分辨率设置
lcd_width = 800
lcd_height = 480

# 摄像头初始化（注意：保留RGB模式用于色块检测，后续转为灰度图用于矩形检测）
sensor = Sensor(width=1920, height=1080)
sensor.reset()
sensor.set_framesize(width=400, height=240)  # 降低分辨率提高帧率
sensor.set_pixformat(Sensor.RGB565)  # 保留彩色用于紫色色块检测

# 显示初始化
Display.init(Display.ST7701, width=lcd_width, height=lcd_height, to_ide=True)
MediaManager.init()
sensor.run()

# --------------------------- 配置参数 ---------------------------
# 矩形检测核心参数（基于cv_lite）
canny_thresh1      = 50        # Canny边缘检测低阈值
canny_thresh2      = 150       # Canny边缘检测高阈值
approx_epsilon     = 0.04      # 多边形拟合精度（越小越精确）
area_min_ratio     = 0.005     # 最小面积比例（相对于图像总面积）
max_angle_cos      = 0.3       # 角度余弦阈值（越小越接近矩形）
gaussian_blur_size = 3         # 高斯模糊核尺寸（奇数）

# 原有筛选参数
MIN_AREA = 100               # 最小面积阈值
MAX_AREA = 100000             # 最大面积阈值
MIN_ASPECT_RATIO = 0.3        # 最小宽高比
MAX_ASPECT_RATIO = 3.0        # 最大宽高比

# 虚拟坐标与圆形参数
BASE_RADIUS = 45              # 基础半径（虚拟坐标单位）
POINTS_PER_CIRCLE = 24        # 圆形采样点数量
PURPLE_THRESHOLD = (20, 60, 15, 70, -70, -20)  # 紫色色块阈值

# 基础矩形参数（固定方向，不再自动切换）
RECT_WIDTH = 210    # 固定矩形宽度
RECT_HEIGHT = 95    # 固定矩形高度
# 移除自动切换方向的逻辑，始终使用固定宽高的虚拟矩形

# --------------------------- 工具函数 ---------------------------
def calculate_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])** 2)

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

def detect_purple_blobs(img):
    return img.find_blobs(
        [PURPLE_THRESHOLD],
        pixels_threshold=100,
        area_threshold=100,
        merge=True
    )

def send_circle_points(points):
    if not points:
        return
    count = len(points)
    msg = f"$$C,{count},"
    for x, y in points:
        msg += f"{x},{y},"
    msg = msg.rstrip(',') + "##"
    uart.write(msg)
    # print(f"发送圆形点: {msg}")

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

# --------------------------- 主循环 ---------------------------
clock = time.clock()
image_shape = [sensor.height(), sensor.width()]  # [高, 宽] 用于cv_lite
while True:
    clock.tick()
    img = sensor.snapshot()

    # 1. 检测紫色色块（保留原有功能）
    purple_blobs = detect_purple_blobs(img)
    for blob in purple_blobs:
        img.draw_rectangle(blob[0:4], color=(255, 0, 255), thickness=1)
        img.draw_cross(blob.cx(), blob.cy(), color=(255, 0, 255), thickness=1)

    # 2. 矩形检测（使用cv_lite替换原有实现）
    # 2.1 将RGB图像转为灰度图（用于矩形检测）
    gray_img = img.to_grayscale()
    img_np = gray_img.to_numpy_ref()  # 转为numpy数组供cv_lite使用

    # 2.2 调用cv_lite矩形检测函数（带角点）
    rects = cv_lite.grayscale_find_rectangles_with_corners(
        image_shape,       # 图像尺寸 [高, 宽]
        img_np,            # 灰度图数据
        canny_thresh1,     # Canny低阈值
        canny_thresh2,     # Canny高阈值
        approx_epsilon,    # 多边形拟合精度
        area_min_ratio,    # 最小面积比例
        max_angle_cos,     # 角度余弦阈值
        gaussian_blur_size # 高斯模糊尺寸
    )

    # 3. 筛选最小矩形（保留原有逻辑）
    min_area = float('inf')
    smallest_rect = None
    smallest_rect_corners = None  # 存储最小矩形的角点

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
        virtual_circle_points = []
        for i in range(POINTS_PER_CIRCLE):
            angle_rad = 2 * math.pi * i / POINTS_PER_CIRCLE
            x_virt = virtual_center[0] + radius_x * math.cos(angle_rad)
            y_virt = virtual_center[1] + radius_y * math.sin(angle_rad)
            virtual_circle_points.append((x_virt, y_virt))

        # 计算透视变换矩阵并映射坐标
        matrix = get_perspective_matrix(virtual_rect, sorted_corners)
        if matrix:
            mapped_points = transform_points(virtual_circle_points, matrix)
            int_points = [(int(round(x)), int(round(y))) for x, y in mapped_points]

            # 绘制圆形
            for (px, py) in int_points:
                img.draw_circle(px, py, 2, color=(255, 0, 255), thickness=2)

            # 绘制圆心
            mapped_center = transform_points([virtual_center], matrix)
            if mapped_center:
                cx, cy = map(int, map(round, mapped_center[0]))
                img.draw_circle(cx, cy, 3, color=(0, 0, 255), thickness=1)

            # 发送坐标
            send_circle_points(int_points)

    # 5. 显示与性能统计
    fps = clock.fps()
    img.draw_string_advanced(10, 10, 20, f"FPS: {fps:.1f}", color=(255, 255, 255))  # 显示FPS

    # 显示图像
    Display.show_image(img,
                      x=round((lcd_width-sensor.width())/2),
                      y=round((lcd_height-sensor.height())/2))

    print(f"FPS: {fps:.1f}")  # 打印FPS

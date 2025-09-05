# ============================================================
# MicroPython RGB888 彩色块检测测试代码（使用 cv_lite 扩展模块）
# RGB888 Color Blob Detection Test using cv_lite extension
# ============================================================

import time, os, sys, gc
from machine import Pin
from media.sensor import *  # 导入摄像头接口 / Camera interface
from media.display import * # 导入显示接口 / Display interface
from media.media import *   # 导入媒体资源管理器 / Media manager
import _thread
import cv_lite              # cv_lite 扩展模块
import ulab.numpy as np     # MicroPython NumPy 类库

# -------------------------------
# 图像尺寸设置 / Image resolution
# -------------------------------
image_shape = [240, 320]  # 高 x 宽 / Height x Width

# -------------------------------
# 初始化摄像头（RGB888格式） / Initialize camera (RGB888 format)
# -------------------------------
sensor = Sensor(id=2, width=image_shape[1], height=image_shape[0])
sensor.reset()
sensor.set_framesize(width=image_shape[1], height=image_shape[0])
sensor.set_pixformat(Sensor.RGB888)  # RGB888格式 / RGB888 format

# -------------------------------
# 初始化显示（IDE虚拟显示模式） / Initialize display (IDE virtual output)
# -------------------------------
Display.init(Display.ST7701, width=800, height=480, to_ide=True, quality=50)

# -------------------------------
# 初始化媒体资源管理器 / Initialize media manager
# -------------------------------
MediaManager.init()
sensor.run()

# -------------------------------
# 色块检测阈值 / Blob detection thresholds
# 格式：[Rmin, Rmax, Gmin, Gmax, Bmin, Bmax]
threshold = [60, 110, 90, 125, 200, 255]

min_area = 100    # 最小色块面积 / Minimum blob area
kernel_size = 1   # 腐蚀膨胀核大小（用于预处理）/ Kernel size for morphological ops

# -------------------------------
# 启动帧率计时器 / Start FPS timer
# -------------------------------
clock = time.clock()

# -------------------------------
# 主循环 / Main loop
# -------------------------------
while True:
    clock.tick()

    # 拍摄一帧图像 / Capture a frame
    img = sensor.snapshot()
    img_np = img.to_numpy_ref()  # 获取 RGB888 ndarray 引用

    # 调用 cv_lite 扩展进行色块检测，返回 [x, y, w, h, ...] 列表
    blobs = cv_lite.rgb888_find_blobs(image_shape, img_np, threshold, min_area, kernel_size)
    rect = []
#    print(blobs)
    # 遍历检测到的色块并绘制矩形框
    for i in range(len(blobs) // 4):   # 修正为整数除法
        x = blobs[4*i]
        y = blobs[4*i + 1]
        w = blobs[4*i + 2]
        h = blobs[4*i + 3]
        rect = [x,y,w,h]
        img.draw_rectangle(x, y, w, h, color=(255, 0, 0), thickness=2)  # 红色框
    if len(rect) > 3:
        xy = [(rect[0]+rect[2]//2,rect[1]+rect[3]//2,1)]
        print(f"终点坐标{xy}")
        img.draw_keypoints(xy,color=(255,0,0),size=10,thickness=1)
    # 显示结果图像 / Show image with blobs
    Display.show_image(img)

    # 打印帧率 / Print FPS
    print("findblobs:", clock.fps())

    # 垃圾回收 / Garbage collect
    gc.collect()

# -------------------------------
# 退出释放资源 / Cleanup on exit
# -------------------------------
sensor.stop()
Display.deinit()
os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
time.sleep_ms(100)
MediaManager.deinit()

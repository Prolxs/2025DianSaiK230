# ============================================================
# MicroPython RGB888 彩色块检测测试代码（使用 cv_lite 扩展模块）
# RGB888 Color Blob Detection Test using cv_lite extension
# ============================================================
import cv_lite              # cv_lite 扩展模块
import ulab.numpy as np     # MicroPython NumPy 类库
from media.display import *
def find_blobs(img_shape, img, threshold, min_area=100, kernel_size=1):
    """
    img_shape: [heitht, width]图像尺寸 / Image shape
    img: RGB888图像 / RGB888 Image 
    threshold: 色块检测阈值 / Blob detection thresholds
    min_area: 最小色块面积 / Minimum blob area
    kernel_size: 腐蚀膨胀核大小 / Kernel size for morphological ops
    """
    img_np = img.to_numpy_ref()
    # 调用 cv_lite 扩展进行色块检测，返回 [x, y, w, h, ...] 列表
    blobs = cv_lite.rgb888_find_blobs(img_shape, img_np, threshold, min_area, kernel_size)
    rect = ()
    xy = ()
    #    print(blobs)
    # 遍历检测到的色块并绘制矩形框
    for i in range(len(blobs) // 4):   # 修正为整数除法
        x = blobs[4*i]
        y = blobs[4*i + 1]
        w = blobs[4*i + 2]
        h = blobs[4*i + 3]
        rect = (x,y,w,h)
        # img.draw_rectangle(x, y, w, h, color=(255, 0, 0), thickness=2)  # 红色框
    if len(rect) > 3:
        # xy = [(rect[0]+rect[2]//2,rect[1]+rect[3]//2,1)]
        xy = (rect[0]+rect[2]//2,rect[1]+rect[3]//2)
        # print(f"终点坐标{xy}")
        # img.draw_keypoints(xy,color=(255,0,0),size=10,thickness=1)
        return [xy,rect]
    return None

# ============================================================
# MicroPython 基于 cv_lite 的 RGB888 矩形检测测试代码
# RGB888 Rectangle Detection Test using cv_lite extension
# ============================================================


# -------------------------------
# 可调参数（建议调试时调整）/ Adjustable parameters (recommended for tuning)
# -------------------------------
canny_thresh1       = 50        # Canny 边缘检测低阈值 / Canny edge low threshold
canny_thresh2       = 150       # Canny 边缘检测高阈值 / Canny edge high threshold
approx_epsilon      = 0.04      # 多边形拟合精度（比例） / Polygon approximation precision (ratio)
area_min_ratio      = 0.001     # 最小面积比例（0~1） / Minimum area ratio (0~1)
max_angle_cos       = 0.5       # 最大角余弦（值越小越接近矩形） / Max cosine of angle (smaller closer to rectangle)
gaussian_blur_size  = 5         # 高斯模糊核大小（奇数） / Gaussian blur kernel size (odd number)

# -------------------------------
# 主循环 / Main loop
# -------------------------------
def find_rectangles(img_shape, img):

    # 拍摄当前帧图像 / Capture current frame

    img_np = img.to_numpy_ref()  # 获取 RGB888 ndarray 引用 / Get RGB888 ndarray reference

    # 调用底层矩形检测函数，返回矩形列表 [x0, y0, w0, h0, x1, y1, w1, h1, ...]
    # Call underlying rectangle detection function, returns list of rectangles [x, y, w, h, ...]
    rects = cv_lite.rgb888_find_rectangles(
        img_shape, img_np,
        canny_thresh1, canny_thresh2,
        approx_epsilon,
        area_min_ratio,
        max_angle_cos,
        gaussian_blur_size
    )
    rect = ()
    # 遍历检测到的矩形，绘制矩形框 / Iterate detected rectangles and draw bounding boxes
    for i in range(0, len(rects), 4):
        x = rects[i]
        y = rects[i + 1]
        w = rects[i + 2]
        h = rects[i + 3]
        rect = (x,y,w,h)
        img.draw_rectangle(x, y, w, h, color=(255, 0, 0), thickness=2)

    # 释放临时变量内存 / Free temporary variables memory
    # del img_np
    # del img
    return rect

def find_rectangles_565(img,MIN_AREA = 2000,MAX_AREA = 16000):
    # 中值滤波
#        img = img.median(1)
    # 转换为灰度图像
    gray_img = img.to_grayscale()
    # 进行高斯模糊，减少图像噪声
    gray_img.gaussian(1)
#        gray_img.histeq(adaptive=True)
    gray_img.binary([(0,70)],invert=True)
#        gray_img.dilate(2)
    gray_img.erode(1)
#        gray_img.erode(2)
#        gray_img.dilate(1)
    
    # 在灰度图像中查找矩形，设置阈值
    rects = gray_img.find_rects(threshold=0)
    # Display.show_image(gray_img, x=0,y=0)
    # area = None
    for r in rects:
#            print(r)
        # 获取矩形的宽度和高度
        width = r.w()
        height = r.h()
        # 计算矩形的面积
        area = width * height
        
        if MIN_AREA <= area <= MAX_AREA:
            img.draw_rectangle(r.rect(), color=(1, 147, 230), thickness=1)
            # center_x = int(sum_x / len(list1))  # 765 ÷ 4 = 191.25
            # center_y = int(sum_y / len(list1))  # 476 ÷ 4 = 119.0
            # center = (center_x,center_y)
            # print(r.corners())
            list1 = [r.corners()[0],r.corners()[1],r.corners()[2],r.corners()[3]]
            
                # 计算所有x坐标的总和
            sum_x = sum(point[0] for point in list1)  # 127 + 253 + 259 + 126 = 765
            # 计算所有y坐标的总和
            sum_y = sum(point[1] for point in list1)  # 182 + 180 + 60 + 54 = 476
            # 计算中心点坐标
            center_x = int(sum_x / len(list1))  # 765 ÷ 4 = 191.25
            center_y = int(sum_y / len(list1))  # 476 ÷ 4 = 119.0
            center = (center_x,center_y)
            # print(f"中心点坐标：{center}")
            return center
    return None
    #     # 检查面积是否在合理范围内
    #     if MIN_AREA <= area <= MAX_AREA:
    #         valid_rects.append(r)
    #         # 打印有效矩形的面积
    #         print(f"有效矩形面积: {area}")
    # if len(valid_rects) >= 2:
    #     # 按面积对有效矩形进行排序
    #     valid_rects.sort(key=lambda rect: rect.w() * rect.h(), reverse=True)
    #     outer_rect = valid_rects[0]
    #     inner_rect = valid_rects[1]

    #     # 获取外框矩形的四个角点
    #     outer_corners = outer_rect.corners()
    #     outer_top_left = outer_corners[0]
    #     outer_top_right = outer_corners[1]
    #     outer_bottom_right = outer_corners[2]
    #     outer_bottom_left = outer_corners[3]

    #     # 获取内框矩形的四个角点
    #     inner_corners = inner_rect.corners()
    #     inner_top_left = inner_corners[0]
    #     inner_top_right = inner_corners[1]
    #     inner_bottom_right = inner_corners[2]
    #     inner_bottom_left = inner_corners[3]
    #     # 输出外框和内框矩形四角坐标
    #     print(f"外框矩形四角坐标：左上角: {outer_top_left}, 右上角: {outer_top_right}, 右下角: {outer_bottom_right}, 左下角: {outer_bottom_left}")
    #     print(f"内框矩形四角坐标：左上角: {inner_top_left}, 右上角: {inner_top_right}, 右下角: {inner_bottom_right}, 左下角: {inner_bottom_left}")



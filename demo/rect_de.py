from media.sensor import *
from media.display import *
from media.media import *
import time
from machine import UART,PWM
from machine import FPIOA
import math
import ulab

# 红色激光点颜色阈值，可根据实际情况调整
RED_LASER_THRESHOLD = [(0, 100, 22, 127, -128, 127)]
# 绿色激光点颜色阈值，可根据实际情况调整
GREEN_LASER_THRESHOLD = [(0, 100, -128, -29, -128, 127)]
def rect_detection(sensor,roi):
#    roi=(59,30,273,204)
    # 定义矩形面积的最小和最大阈值，可根据实际情况调整
    MIN_AREA = 2000
    MAX_AREA = 15000

    # 连续稳定检测次数
    stable_count = 0
    # 最大允许的点位差异
    MAX_POINT_DIFF = 10
    # 上一次检测到的外框和内框角点
    prev_outer_corners = None
    prev_inner_corners = None
    # 存储 20 次检测的外框和内框角点
    outer_corners_list = []
    inner_corners_list = []
    # 存储最终确定的外框和内框平均角点
    final_outer_corners = None
    final_inner_corners = None

    while True:
        # 拍摄一张图
        img = sensor.snapshot()

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
        rects = gray_img.find_rects(roi,threshold=0)
        img.draw_rectangle(roi, color=(255, 255, 0), thickness=1)
#        Display.show_image(gray_img, x=0,y=0)
        valid_rects = []
        for r in rects:
#            print(r)
            # 获取矩形的宽度和高度
            width = r.w()
            height = r.h()
            # 计算矩形的面积
            area = width * height
            img.draw_rectangle(r.rect(), color=(1, 147, 230), thickness=1)
            # 检查面积是否在合理范围内
            if MIN_AREA <= area <= MAX_AREA:
                valid_rects.append(r)
                # 打印有效矩形的面积
                print(f"有效矩形面积: {area}")

        if len(valid_rects) >= 2:
            # 按面积对有效矩形进行排序
            valid_rects.sort(key=lambda rect: rect.w() * rect.h(), reverse=True)
            outer_rect = valid_rects[0]
            inner_rect = valid_rects[1]

            # 获取外框矩形的四个角点
            outer_corners = outer_rect.corners()
            outer_top_left = outer_corners[0]
            outer_top_right = outer_corners[1]
            outer_bottom_right = outer_corners[2]
            outer_bottom_left = outer_corners[3]

            # 获取内框矩形的四个角点
            inner_corners = inner_rect.corners()
            inner_top_left = inner_corners[0]
            inner_top_right = inner_corners[1]
            inner_bottom_right = inner_corners[2]
            inner_bottom_left = inner_corners[3]

            # 输出外框和内框矩形四角坐标
            print(f"外框矩形四角坐标：左上角: {outer_top_left}, 右上角: {outer_top_right}, 右下角: {outer_bottom_right}, 左下角: {outer_bottom_left}")
            print(f"内框矩形四角坐标：左上角: {inner_top_left}, 右上角: {inner_top_right}, 右下角: {inner_bottom_right}, 左下角: {inner_bottom_left}")

            # 在原始 RGB 图像上绘制外框和内框矩形的角点连线，使用红色
            for corners in [outer_corners, inner_corners]:
                for i in range(4):
                    p1 = corners[i]
                    p2 = corners[(i + 1) % 4]
                    img.draw_line(p1[0], p1[1], p2[0], p2[1], color=(255, 0, 0), thickness=2)

            # 检查是否连续稳定
            if prev_outer_corners and prev_inner_corners:
                outer_stable = all(
                    abs(curr[0] - prev[0]) <= MAX_POINT_DIFF and abs(curr[1] - prev[1]) <= MAX_POINT_DIFF
                    for curr, prev in zip(outer_corners, prev_outer_corners)
                )
                inner_stable = all(
                    abs(curr[0] - prev[0]) <= MAX_POINT_DIFF and abs(curr[1] - prev[1]) <= MAX_POINT_DIFF
                    for curr, prev in zip(inner_corners, prev_inner_corners)
                )
                if outer_stable and inner_stable:
                    stable_count += 1
                    outer_corners_list.append(outer_corners)
                    inner_corners_list.append(inner_corners)
                else:
                    stable_count = 0
                    outer_corners_list = []
                    inner_corners_list = []
            else:
                stable_count = 0
                outer_corners_list = []
                inner_corners_list = []

            prev_outer_corners = outer_corners
            prev_inner_corners = inner_corners

            if stable_count >= 20:
                # 计算外框和内框角点的平均值
                outer_corners_sum = [[0, 0] for _ in range(4)]
                inner_corners_sum = [[0, 0] for _ in range(4)]
                for corners in outer_corners_list:
                    for i, point in enumerate(corners):
                        outer_corners_sum[i][0] += point[0]
                        outer_corners_sum[i][1] += point[1]
                for corners in inner_corners_list:
                    for i, point in enumerate(corners):
                        inner_corners_sum[i][0] += point[0]
                        inner_corners_sum[i][1] += point[1]
                final_outer_corners = [(x // 20, y // 20) for x, y in outer_corners_sum]
                final_inner_corners = [(x // 20, y // 20) for x, y in inner_corners_sum]
#                break

    #            # 输出平均角点坐标
    #            print(f"外框矩形平均四角坐标：左上角: {final_outer_corners[0]}, 右上角: {final_outer_corners[1]}, 右下角: {final_outer_corners[2]}, 左下角: {final_outer_corners[3]}")
    #            print(f"内框矩形平均四角坐标：左上角: {final_inner_corners[0]}, 右上角: {final_inner_corners[1]}, 右下角: {final_inner_corners[2]}, 左下角: {final_inner_corners[3]}")
#                while True:
                img = sensor.snapshot()
                # 绘制平均矩形，使用绿色
                for corners in [final_outer_corners, final_inner_corners]:
                    for i in range(4):
                        p1 = corners[i]
                        p2 = corners[(i + 1) % 4]
                        img.draw_line(p1[0], p1[1], p2[0], p2[1], color=(0, 255, 0), thickness=2)

                        if i==0:
                            img.draw_circle(p1[0], p1[1],5,color=(255,0,0),thickness=3)
                        elif i==1:
                            img.draw_circle(p1[0], p1[1],5,color=(0,255,0),thickness=3)
                        elif i==2:
                            img.draw_circle(p1[0], p1[1],5,color=(0,0,255),thickness=3)
                        else:
                            img.draw_circle(p1[0], p1[1],5,color=(0,255,255),thickness=3)

                # 显示图片

#                    print(f"外框矩形平均四角坐标：左上角: {final_outer_corners[0]}, 右上角: {final_outer_corners[1]}, 右下角: {final_outer_corners[2]}, 左下角: {final_outer_corners[3]}")
#                    print(f"内框矩形平均四角坐标：左上角: {final_inner_corners[0]}, 右上角: {final_inner_corners[1]}, 右下角: {final_inner_corners[2]}, 左下角: {final_inner_corners[3]}")
                outerDist = all_closest_to_origin(final_outer_corners)
                innerIndex,innerPoint = find_closest_point(outerDist[0]['point'],final_inner_corners)
#                innerDist = all_closest_to_origin(final_inner_corners)
                outerIndex = outerDist[0]['index']
#                innerIndex = innerDist[0]['index']
                print(outerIndex,innerIndex)
                xy = []
                for i in range(4):
                    xy.append((((final_outer_corners[outerIndex%4][0]+final_inner_corners[innerIndex%4][0]))//2,((final_outer_corners[outerIndex%4][1]+final_inner_corners[innerIndex%4][1]))//2))
                    outerIndex +=1
                    innerIndex +=1
#                print(xy)
                for i in range(4):
                    if i==0:
                        img.draw_circle(xy[i][0], xy[i][1],5,color=(255,0,0),thickness=3)
                    elif i==1:
                        img.draw_circle(xy[i][0], xy[i][1],5,color=(0,255,0),thickness=3)
                    elif i==2:
                        img.draw_circle(xy[i][0], xy[i][1],5,color=(0,0,255),thickness=3)
                    else:
                        img.draw_circle(xy[i][0], xy[i][1],5,color=(0,255,255),thickness=3)
                Display.show_image(img, x=0,y=0)
                return xy
        Display.show_image(img, x=0,y=0)


def laser_detection(sensor):
    # 拍摄一张图
#    roi=
    img = sensor.snapshot()

    # 中值滤波
    img = img.median(1)
    img.gamma_corr(1.3)
    Rxy = None
    Gxy = None
#    meanxy = None
    # 查找红色激光点
    red_blobs = img.find_blobs(RED_LASER_THRESHOLD, pixels_threshold=5, area_threshold=5, merge=True,roi=(31,0,313,204))
    if red_blobs:
        sumX = 0
        sumY = 0
        for blob in red_blobs:
            # 获取激光点的中心位置
            sumX += blob.cx()
            sumY += blob.cy()
        num = len(red_blobs)
        if num:
            Rxy = (int(sumX/num),int(sumY/num))
            img.draw_cross(Rxy[0], Rxy[1], color=(255, 0, 0), size=10, thickness=1)
        else:
            Rxy = None
#        sumX = 0
#        sumY = 0
#        for blob in red_blobs:
#            # 获取激光点的中心位置
#            x= blob.cx()
#            y= blob.cy()
#            Rxy = (x,y)
#            img.draw_cross(x, y, color=(255, 0, 255), size=10, thickness=1)


    # 查找绿色激光点
    green_blobs = img.find_blobs(GREEN_LASER_THRESHOLD, pixels_threshold=1, area_threshold=3, merge=True,roi=(31,19,313,204))
    if green_blobs:
        sumX = 0
        sumY = 0
        for blob in green_blobs:
            # 获取激光点的中心位置
            sumX += blob.cx()
            sumY += blob.cy()
        num = len(red_blobs)
        if num:
            Gxy = (int(sumX/num),int(sumY/num))
            # 在图像上绘制激光点的中心位置
            img.draw_cross(Gxy[0], Gxy[1], color=(0, 255, 0), size=10, thickness=1)
        else :
            Gxy = None
#                print(f"Green laser point detected at ({x}, {y})")

    # 显示图片
    Display.show_image(img, x=0,y=0)
    return Rxy,Gxy

def outterRect(sensor):
    roi=(59,30,273,204)
    MAX_POINT_DIFF = 3
    rect_list=[]
    counter = 0
    innerroi = None
    prev_rect = []
    stable = None
    while True:
        img = sensor.snapshot()
        img = img.to_grayscale()
        img.histeq(adaptive=True)
        img.binary([(0,50)],invert=True)
        img.erode(1)
        img.erode(1)
        img.dilate(1)
        img.dilate(1)   
        
        rects = img.find_rects(roi,threshold=20000)
        if counter<20:
            for rect in rects:
                S = rect.w()*rect.h()
#                print(S)
                if S>21000 and S<25000:
                    curr_rect = rect.corners()
                    print(f"有效面积：{S}")
                    if prev_rect:
                        stable = all(
                            abs(curr[0] - prev[0]) <= MAX_POINT_DIFF and abs(curr[1] - prev[1]) <= MAX_POINT_DIFF
                            for curr, prev in zip(curr_rect, prev_rect)
                        )
                    if stable:
                        counter=counter+1
                        innerroi = rect.rect()
                        rect_list.append(rect.corners())
                        print(f"有效矩形{rect.corners()}")
                    else :
                        counter=0
                        rect_list=[]
                        innerroi=None
                        print("不连续")
#                    img.draw_rectangle(rect.rect(), color=0, thickness=3)
                    
                    prev_rect = curr_rect
        else:
            # 初始化四个角点的累加器 [左上, 右上, 右下, 左下]
            sum_corners = [[0, 0], [0, 0], [0, 0], [0, 0]]

            # 遍历所有存储的矩形角点
            for corners in rect_list:
                
                # corners 是一个包含四个(x,y)元组的元组，顺序为(左上, 右上, 右下, 左下)
                for i in range(4):  # 处理每个角点
                    sum_corners[i][0] += corners[i][0]  # 累加x坐标
                    sum_corners[i][1] += corners[i][1]  # 累加y坐标

            # 计算平均坐标（四舍五入取整）
            avg_corners = []
            for point in sum_corners:
                avg_x = round(point[0] / 20)
                avg_y = round(point[1] / 20)
                avg_corners.append((int(avg_x), int(avg_y)))

            # 打印平均矩形坐标
            print("平均矩形坐标:")
            print(f"左上: {avg_corners[0]}")
            print(f"右上: {avg_corners[1]}")
            print(f"右下: {avg_corners[2]}")
            print(f"左下: {avg_corners[3]}")
            return (avg_corners,innerroi)
        Display.show_image(img , x=0,y=0)

def calculate_checksum(xy,str1):
    # 构建字符串：帧头$ + x坐标 + , + y坐标 + ,
    data_str = f"${str1},{xy[0]},{xy[1]}"
#    print(data_str)
    # 初始化校验和
    checksum = 0

    # 遍历字符串中的每个字符（不包括校验和本身）
    for char in data_str:
        # 将字符转换为ASCII值并累加
        checksum += ord(char)

    # 取校验和的低8位（模256）
    C = checksum % 256
#    print(C)
    return (C,data_str+f",{C}")

def waitCenter_Respond(uart,centermeg):
    data = None
    while data == None:
        uart.write(centermeg)
        time.sleep(0.3)
        data = uart.read()
        
        if data != b'' and data != None:
            print(f"waitCenter_Respond: {str(data)}")
            try:
                if data.decode() is "center":
                    return
            except UnicodeError as e:
                pass
            finally:
                data = None
        else :data = None

def SendRect_XY(uart, list1, index):
    counter = 0
    data = None
    while data == None:
        if counter >3:
            return
        (C,centermeg) = calculate_checksum(list1[counter],index[counter])
        uart.write(centermeg)
        
        data = uart.read()
        time.sleep(0.3)
        print(f"readRect_XY: {centermeg}")
        if data!=b'' and data !=None:
            if data.decode() is index[counter]:
                counter+=1
            data = None
        else:
            data = None

def all_closest_to_origin(coords):
    # 计算每个点的距离平方并同时记录索引
    indexed_distances = [(i, p, p[0]*p[0] + p[1]*p[1]) for i, p in enumerate(coords)]
    
    # 找到最小距离平方
    min_dist_sq = min(dist for _, _, dist in indexed_distances)
    
    # 返回所有距离平方等于最小值的点（包含坐标和索引）
    return [{"point": p, "index": i} for i, p, dist in indexed_distances if dist == min_dist_sq]

def find_closest_point(target_point, points_list):
    """
    找到距离目标点最近的坐标点并返回其索引
    
    参数:
        target_point (tuple): 目标坐标 (x, y)
        points_list (list): 候选坐标列表 [(x1, y1), (x2, y2), ...]
        
    返回:
        int: 最近点的索引
        tuple: 最近点的坐标
    """
    if not points_list:
        raise ValueError("坐标列表不能为空")
    
    min_distance = float('inf')
    closest_index = 0
    closest_point = None
    
    for index, point in enumerate(points_list):
        # 计算欧几里得距离平方（避免开方运算提升性能）
        distance_sq = (point[0] - target_point[0])**2 + (point[1] - target_point[1])**2
        
        if distance_sq < min_distance:
            min_distance = distance_sq
            closest_index = index
            closest_point = point
    
    return (closest_index, closest_point)

if __name__ == "__main__":
    
    fpioa = FPIOA()
    fpioa.set_function(43, FPIOA.PWM1)
    pwm = PWM(1, 340, duty=50, enable=False)
    fpioa.set_function(11, FPIOA.UART2_TXD)
    fpioa.set_function(12, FPIOA.UART2_RXD)
    uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
    sensor = Sensor(width=1280, height=960)
    sensor.reset()
    sensor.set_framesize(width=400, height=300)
    sensor.set_pixformat(sensor.RGB565)
    Display.init(Display.VIRT, to_ide=True,width=400,height=300)
    MediaManager.init()
    sensor.run()

    (list1,inner_roi) = outterRect(sensor)
    xy = rect_detection(sensor,inner_roi)
    index = 'QWET' #外框顶点
    Innerindex = 'YUIO' #内框
    # 计算所有x坐标的总和
    sum_x = sum(point[0] for point in list1)  # 127 + 253 + 259 + 126 = 765
    # 计算所有y坐标的总和
    sum_y = sum(point[1] for point in list1)  # 182 + 180 + 60 + 54 = 476
    # 计算中心点坐标
    center_x = int(sum_x / len(list1))  # 765 ÷ 4 = 191.25
    center_y = int(sum_y / len(list1))  # 476 ÷ 4 = 119.0
    center = (center_x,center_y)
    # 以中点为0
#    NewXYlist = []
#    for i in list1:
#        NewXYlist.append((i[0]-center_x,center_y-i[1]))
#    print(NewXYlist)
    (C,centermeg) = calculate_checksum(center,'C')
    print(f"{C},{centermeg}")
    print(f"中点坐标{center}")
    pwm.enable(1)
    time.sleep(0.5)
    pwm.enable(0)
    try:
        waitCenter_Respond(uart, centermeg) #等待中点请求
        SendRect_XY(uart, list1, index) #顶点坐标请求 0,0
        SendRect_XY(uart, xy, Innerindex)
        while True:
            img = sensor.snapshot()
#            img.rgb_to_hsv(img)
#            for i in range(4):
#                img.draw_line(list1[i][0],list1[i][1],list1[(i + 1) % 4][0],list1[(i + 1) % 4][1])
#            Display.show_image(img , x=0,y=0)
            RlaserXY,GlaserXY = laser_detection(sensor)
            if(RlaserXY != None):
#                RlaserXY = (laserXY[0],laserXY[1])
#                laserXY = (laserXY[0]-center[0],center[1]-laserXY[1])
                (C,lasermeg) = calculate_checksum(RlaserXY,'R')
                print("红点坐标："+lasermeg)
    #            uart.write(centermeg)
                time.sleep_ms(5)
                uart.write(lasermeg)
            if(GlaserXY != None):
#                RlaserXY = (laserXY[0],laserXY[1])
#                laserXY = (laserXY[0]-center[0],center[1]-laserXY[1])
                (C,lasermeg) = calculate_checksum(GlaserXY,'G')
                print("绿点坐标："+lasermeg)
    #            uart.write(centermeg)
                time.sleep_ms(5)
                uart.write(lasermeg)
#            endTime = time.time()
#            print(f"发送耗时:{(endTime - startTime):.6f}秒\n")
#            img.draw_circle(center_x,center_y, 4, color=(255,0,0), thickness=1)
#            Display.show_image(img , x=0,y=0)


    except KeyboardInterrupt as e:
            print("用户终止：", e)  # 捕获键盘中断异常
    except BaseException as e:
        print(f"异常：{e}")  # 捕获其他异常
    finally:
        # 清理资源
        Display.deinit()
        os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)  # 启用睡眠模式的退出点
        time.sleep_ms(100)  # 延迟100毫秒
        MediaManager.deinit()

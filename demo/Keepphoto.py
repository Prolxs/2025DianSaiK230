# 立创·庐山派-K230-CanMV开发板资料与相关扩展板软硬件资料官网全部开源
# 开发板官网：www.lckfb.com
# 技术支持常驻论坛，任何技术问题欢迎随时交流学习
# 立创论坛：www.jlc-bbs.com/lckfb
# 关注bilibili账号：【立创开发板】，掌握我们的最新动态！
# 不靠卖板赚钱，以培养中国工程师为己任

import time, os, sys
import ujson as json
from machine import TOUCH

#使用默认摄像头，可选参数:0,1,2.
sensor_id = 2

# ========== 多媒体/图像相关模块 ==========
from media.sensor import Sensor, CAM_CHN_ID_0
from media.display import Display
from media.media import MediaManager
import image
from ui.ui_core import TouchUI
# ========== GPIO/按键/LED相关模块 ==========
from machine import Pin
from machine import FPIOA

# ========== 创建FPIOA对象并为引脚功能分配 ==========
fpioa = FPIOA()
fpioa.set_function(62, FPIOA.GPIO62)   # 红灯
fpioa.set_function(20, FPIOA.GPIO20)   # 绿灯
fpioa.set_function(63, FPIOA.GPIO63)   # 蓝灯
fpioa.set_function(53, FPIOA.GPIO53)   # 按键

# ========== 初始化LED (共阳：高电平熄灭，低电平亮) ==========
LED_R = Pin(62, Pin.OUT, pull=Pin.PULL_NONE, drive=7)  # 红灯
LED_G = Pin(20, Pin.OUT, pull=Pin.PULL_NONE, drive=7)  # 绿灯
LED_B = Pin(63, Pin.OUT, pull=Pin.PULL_NONE, drive=7)  # 蓝灯

# 默认熄灭所有LED
LED_R.high()
LED_G.high()
LED_B.high()

# 选一个LED用来拍照提示
PHOTO_LED = LED_G

# ========== 初始化按键：按下时高电平 ==========
button = Pin(53, Pin.IN, Pin.PULL_DOWN)
debounce_delay = 200  # 按键消抖时长(ms)
last_press_time = 0
button_last_state = 0

# ========== 显示配置 ==========
DISPLAY_MODE = "LCD"   # 可选："VIRT","LCD","HDMI"
if DISPLAY_MODE == "VIRT":
    DISPLAY_WIDTH = 1920
    DISPLAY_HEIGHT = 1080
    FPS = 30
elif DISPLAY_MODE == "LCD":
    DISPLAY_WIDTH = 800
    DISPLAY_HEIGHT = 480
    FPS = 60
elif DISPLAY_MODE == "HDMI":
    DISPLAY_WIDTH = 1920
    DISPLAY_HEIGHT = 1080
    FPS = 30
else:
    raise ValueError("未知的 DISPLAY_MODE，请选择 'VIRT', 'LCD' 或 'HDMI'")

def lckfb_save_jpg(img, filename, quality=95):
    """
    将图像压缩成JPEG后写入文件 (不依赖第一段 save_jpg/MediaManager.convert_to_jpeg 的写法)
    :param img:    传入的图像对象 (Sensor.snapshot() 得到)
    :param filename: 保存的目标文件名 (含路径)
    :param quality:  压缩质量 (1-100)
    """
    compressed_data = img.compress(quality=quality)

    with open(filename, "wb") as f:
        f.write(compressed_data)

    print(f"[INFO] 使用 lckfb_save_jpg() 保存完毕: {filename}")


# ========== 新增变量 ==========
base_folder = "/data/images"
current_digit = 0
count = 0
max_digit = 9
max_count = 100
#import sensor

state_file = "/data/images/state.json"

def save_state(digit, count):
    try:
        with open(state_file, "w") as f:
            json.dump({"digit": digit, "count": count}, f)
    except Exception as e:
        print("[ERROR] 保存状态失败:", e)

def load_state():
    try:
        with open(state_file, "r") as f:
            data = json.load(f)
            return data.get("digit", 0), data.get("count", 0)
    except Exception:
        return 0, 0

# 初始化变量
current_digit, count = load_state()

# ========== 新建函数：确保目录存在 ==========
def ensure_dir(path):
    # 逐级创建目录
    parts = path.strip('/').split('/')
    current = ''
    for part in parts:
        current += '/' + part
        try:
            os.stat(current)
        except OSError:
            os.mkdir(current)

def keep_photo():
    if current_digit > max_digit:
        print("[INFO] 所有数字采集完成！")

    # LED闪烁提示
    PHOTO_LED.low()
    time.sleep_ms(20)
    PHOTO_LED.high()

    # 拍照并保存
    filename = f"{base_folder}/{current_digit}/{current_digit}_{count}.jpg"
    print(f"[INFO] 拍照保存 -> {filename}")
    lckfb_save_jpg(img, filename, quality=95)

    count += 1
    save_state(current_digit, count)
    if count >= max_count:
        current_digit += 1
        count = 0
        if current_digit <= max_digit:
            digit_folder = f"{base_folder}/{current_digit}"
            ensure_dir(digit_folder)
        else:
            print("[INFO] 所有数字采集完成！")

def on_button_click():
    keep_photo()

# ========== 初始化摄像头 ==========
try:
    print("[INFO] 初始化摄像头 ...")
    sensor = Sensor(id=sensor_id)
    sensor.reset()

    # 在本示例中使用 VGA (640x480) 做演示
    sensor.set_framesize(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, chn=CAM_CHN_ID_0)
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)
    
    # ========== 初始化显示 ==========
    if DISPLAY_MODE == "VIRT":
        Display.init(Display.VIRT, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, fps=FPS)
    elif DISPLAY_MODE == "LCD":
        Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    elif DISPLAY_MODE == "HDMI":
        Display.init(Display.LT9611, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)

    # ========== 初始化媒体管理器 ==========
    MediaManager.init()

    # ========== 启动摄像头 ==========
    sensor.run()
    print("[INFO] 摄像头已启动，进入主循环 ...")

    fps = time.clock()

    ui = TouchUI(DISPLAY_WIDTH, DISPLAY_HEIGHT)
    button = ui.add_button(350, 350, 100, 50, "拍照", on_button_click)
    button.bg_color = (180, 80, 80)
    button.text_color = (255, 255, 255)
    while True:
        fps.tick()
        os.exitpoint()

        #抓取通道0的图像
        img = sensor.snapshot(chn=CAM_CHN_ID_0)
        ui.update(img)
        #按键处理（检测上升沿）
        current_time = time.ticks_ms()
        button_state = button.value()
        if button_state == 1 and button_last_state == 0:  # 上升沿
            if current_time - last_press_time > debounce_delay:
                if current_digit > max_digit:
                    print("[INFO] 所有数字采集完成！")
                    break  # 或 continue，或其他处理

                # LED闪烁提示
                PHOTO_LED.low()
                time.sleep_ms(20)
                PHOTO_LED.high()

                # 拍照并保存
                filename = f"{base_folder}/{current_digit}/{current_digit}_{count}.jpg"
                print(f"[INFO] 拍照保存 -> {filename}")
                lckfb_save_jpg(img, filename, quality=95)

                count += 1
                save_state(current_digit, count)
                if count >= max_count:
                    current_digit += 1
                    count = 0
                    if current_digit <= max_digit:
                        digit_folder = f"{base_folder}/{current_digit}"
                        ensure_dir(digit_folder)
                    else:
                        print("[INFO] 所有数字采集完成！")
                        break  # 或 continue，或其他处理

                last_press_time = current_time

        button_last_state = button_state

        img.draw_string_advanced(5, 0, 32, f"{current_digit}:{count}", color=(255, 0, 0))
        img.draw_string_advanced(0, DISPLAY_HEIGHT-32, 32, str(fps.fps()), color=(255, 0, 0))

        Display.show_image(img)



except KeyboardInterrupt:
    print("[INFO] 用户停止")
except BaseException as e:
    print(f"[ERROR] 出现异常: {e}")
finally:
    if 'sensor' in locals() and isinstance(sensor, Sensor):
        sensor.stop()
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
    MediaManager.deinit()

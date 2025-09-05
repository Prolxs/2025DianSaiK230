from media.sensor import *
from media.display import *
from media.media import *

class qsK230:
    def __init__(self,sensor_id=2,sensor_width=800,sensor_height=480,sensor_chn=CAM_CHN_ID_0,sensor_pixformat=Sensor.RGB565,
                 disp_width=800,disp_height=480,to_ide=True,disp_mode='LCD'):
        self.sensor_id = sensor_id
        self.sensor_width = sensor_width
        self.sensor_height = sensor_height
        self.sensor_chn = sensor_chn
        self.sensor_pixformat = sensor_pixformat
        self.disp_width = disp_width
        self.disp_height = disp_height
        self.to_ide = to_ide
        self.disp_mode = disp_mode
        self.mediaManager = MediaManager()
        self.sensor = None
        self.display = Display()
        # 构造一个具有默认配置的摄像头对象
        self.sensor = Sensor(id=sensor_id)
        # 重置摄像头sensor
        self.sensor.reset()
        # 无需进行镜像翻转
        # 设置水平镜像
        # sensor.set_hmirror(False)
        # 设置垂直翻转
        # sensor.set_vflip(False)
        # 设置通道0的输出尺寸为1920x1080
        self.sensor.set_framesize(width=self.sensor_width, height=self.sensor_height, chn=self.sensor_chn)
        # 设置通道0的输出像素格式为RGB888
        self.sensor.set_pixformat(self.sensor_pixformat, chn=self.sensor_chn)
        # 根据模式初始化显示器
        if self.disp_mode == "VIRT":
            self.display.init(Display.VIRT, width=self.disp_width, height=self.disp_height, fps=60)
        elif self.disp_mode == "LCD":
            self.display.init(Display.ST7701, width=self.disp_width, height=self.disp_height, to_ide=True)
        elif self.disp_mode == "HDMI":
            self.display.init(Display.LT9611, width=self.disp_width, height=self.disp_height, to_ide=True)
        
        # 初始化媒体管理器
        self.mediaManager.init()
        self.sensor.run()
 
    
    def mediaManager_deinit(self):
        self.mediaManager.deinit()

    def display_deinit(self):
        self.display.deinit()

    def get_img(self):
        img = self.sensor.snapshot(chn=self.sensor_chn)
        return img

    def show_img(self, img, width, height):
        self.display.show_image(img, width, height)
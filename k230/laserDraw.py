import math

class LaserCanvas:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.shapes = []  # 存储图形列表
        self.active_shape_index = -1  # 当前激活的图形索引
        self.active_point_index = 0   # 当前图形中激活的点索引
        self.current_pos = (0, 0)     # 当前位置
        
    def set_origin(self, x, y):
        """设置绘图原点（相对坐标）"""
        self.origin = (x, y)
        
    def update_position(self, x, y):
        """更新当前位置"""
        self.current_pos = (x, y)
    
    def add_shape(self, points):
        """添加图形（绝对坐标列表）"""
        self.shapes.append(points)
    
    def add_rectangle(self, x, y, width, height, points_per_side=10):
        """添加矩形（左上角坐标和尺寸）"""
        points = []
        # 顶部边
        for i in range(points_per_side):
            points.append((x + i * width // points_per_side, y))
        # 右侧边
        for i in range(points_per_side):
            points.append((x + width, y + i * height // points_per_side))
        # 底部边
        for i in range(points_per_side):
            points.append((x + width - i * width // points_per_side, y + height))
        # 左侧边
        for i in range(points_per_side):
            points.append((x, y + height - i * height // points_per_side))
        
        self.shapes.append(points)
        
    def add_circle(self, center_x, center_y, radius, points=36):
        """添加圆形（圆心坐标和半径）"""
        points_list = []
        for i in range(points):
            angle = 2 * math.pi * i / points
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points_list.append((x, y))
        self.shapes.append(points_list)
        
    def add_ellipse(self, center_x, center_y, width, height, points=36):
        """添加椭圆（中心坐标，长轴和短轴）"""
        points_list = []
        a = width / 2  # 半长轴
        b = height / 2  # 半短轴
        for i in range(points):
            angle = 2 * math.pi * i / points
            x = center_x + a * math.cos(angle)
            y = center_y + b * math.sin(angle)
            points_list.append((x, y))
        self.shapes.append(points_list)
        
    def add_triangle(self, center_x, center_y, size, rotation=0, points_per_side=10):
        """添加正三角形（中心坐标，边长和旋转角度）"""
        # 计算三角形高度
        height = (math.sqrt(3) / 2) * size
        
        # 计算三个顶点（未旋转）
        top = (center_x, center_y - height * 2/3)
        right = (center_x + size/2, center_y + height/3)
        left = (center_x - size/2, center_y + height/3)
        
        # 应用旋转
        if rotation != 0:
            top = self._rotate_point(top, center_x, center_y, rotation)
            right = self._rotate_point(right, center_x, center_y, rotation)
            left = self._rotate_point(left, center_x, center_y, rotation)
        
        # 生成各边点集
        points_list = []
        
        # 顶边 (top -> right)
        for i in range(points_per_side):
            t = i / (points_per_side - 1)
            x = top[0] + t * (right[0] - top[0])
            y = top[1] + t * (right[1] - top[1])
            points_list.append((x, y))
            
        # 右边 (right -> left)
        for i in range(points_per_side):
            t = i / (points_per_side - 1)
            x = right[0] + t * (left[0] - right[0])
            y = right[1] + t * (left[1] - right[1])
            points_list.append((x, y))
            
        # 左边 (left -> top)
        for i in range(points_per_side):
            t = i / (points_per_side - 1)
            x = left[0] + t * (top[0] - left[0])
            y = left[1] + t * (top[1] - left[1])
            points_list.append((x, y))
            
        self.shapes.append(points_list)
        
    def _rotate_point(self, point, cx, cy, angle_deg):
        """旋转点（角度制）"""
        angle_rad = math.radians(angle_deg)
        x, y = point
        dx = x - cx
        dy = y - cy
        
        # 应用旋转
        new_x = cx + dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        new_y = cy + dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        
        return (new_x, new_y)
    
    def start_drawing(self, shape_index=0):
        """开始绘制指定图形"""
        if 0 <= shape_index < len(self.shapes):
            self.active_shape_index = shape_index
            self.active_point_index = 0
            return True
        return False
    
    def get_next_target(self, tolerance=5):
        """获取下一个目标点（相对坐标），使用当前位置进行容差判断"""
        if self.active_shape_index == -1:
            return None
            
        shape = self.shapes[self.active_shape_index]
        if self.active_point_index >= len(shape):
            return None
            
        # 获取当前目标点（绝对坐标）
        target_abs = shape[self.active_point_index]
        
        # 计算当前点到目标点的距离
        dx = self.current_pos[0] - target_abs[0]
        dy = self.current_pos[1] - target_abs[1]
        distance = (dx*dx + dy*dy)**0.5
        
        # 如果距离小于容差，则移动到下一个点
        if tolerance > 0 and distance < tolerance:
            self.active_point_index += 1
            # 递归获取下一个点
            return self.get_next_target(tolerance)
        
        # 绝对坐标 → 相对坐标
        rel_x = target_abs[0] - self.origin[0]
        rel_y = target_abs[1] - self.origin[1]
        
        return (rel_x, rel_y)
    
    def is_drawing_complete(self):
        """检查当前图形绘制是否完成"""
        if self.active_shape_index == -1:
            return True
        return self.active_point_index >= len(self.shapes[self.active_shape_index])
        
    def add_line(self, start_x, start_y, end_x, end_y, num_points=10):
        """添加直线（起点和终点坐标）"""
        points = []
        if num_points < 1:
            num_points = 1
            
        for i in range(num_points):
            t = i / max(1, num_points - 1)  # 避免除以0
            x = start_x + t * (end_x - start_x)
            y = start_y + t * (end_y - start_y)
            points.append((x, y))
        self.shapes.append(points)
        
    def add_waveform(self, rel_origin_x, rel_origin_y, wave_func, 
                     start_x, end_x, step=1, amplitude=10, degrees_per_unit=1):
        """
        在相对坐标系下绘制波形
        :param rel_origin_x: 相对坐标系原点X
        :param rel_origin_y: 相对坐标系原点Y
        :param wave_func: 波形函数 (如math.sin)
        :param start_x: 起始X坐标（相对）
        :param end_x: 结束X坐标（相对）
        :param step: 步长
        :param amplitude: 波形幅度
        :param degrees_per_unit: 每单位x对应的角度（默认1度）
        """
        points = []
        x = start_x
        while x <= end_x:
            # 将x值转换为角度（弧度）
            angle_rad = (x * degrees_per_unit) * (math.pi / 180)
            # 计算相对坐标下的波形值
            y_rel = amplitude * wave_func(angle_rad) 
            # 转换为绝对坐标
            abs_x = rel_origin_x + x
            abs_y = rel_origin_y + y_rel
            points.append((abs_x, abs_y))
            x += step
        self.shapes.append(points)
    
    def add_heart(self, center_x, center_y, size, points=None):
        """
        添加爱心图案（中心坐标和尺寸）
        :param center_x: 爱心中心X坐标
        :param center_y: 爱心中心Y坐标
        :param size: 爱心尺寸（直径，单位mm，范围10-100mm）
        :param points: 生成点的数量（默认根据尺寸自动计算）
        """
        # 参数校验
        if size < 10 or size > 100:
            raise ValueError("尺寸必须在10-100mm之间")
        
        # 自动计算点数（尺寸越大点数越多）
        if points is None:
            points = max(50, min(200, int(size * 1.5)))
        
        # 心形线参数方程
        t = [2 * math.pi * i / points for i in range(points)]
        points_list = []
        
        for i in range(points):
            # 标准心形线方程
            x = 16 * (math.sin(t[i]) ** 3)
            y = 13 * math.cos(t[i]) - 5 * math.cos(2*t[i]) - 2 * math.cos(3*t[i]) - math.cos(4*t[i])
            
            # 归一化并缩放
            scale = size / 32.0  # 32是方程中的基准尺寸
            x = x * scale
            y = y * scale
            
            # 平移至中心点并反转Y轴
            abs_x = center_x + x
            abs_y = center_y - y  # 反转Y轴
            
            # 边界检查
            if abs_x < 0: abs_x = 0
            if abs_x > self.width: abs_x = self.width
            if abs_y < 0: abs_y = 0
            if abs_y > self.height: abs_y = self.height
            
            points_list.append((abs_x, abs_y))
        
        self.shapes.append(points_list)

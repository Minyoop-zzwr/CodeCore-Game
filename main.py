import pygame
import sys
import requests
import json
import re
import math
import os
import random

def load_chapter_data():
    """根据 current_chapter_index 重新加载地图数据"""
    global maze_template, MAP_ROWS, MAP_COLS, map_data
    chapter = CHAPTERS[current_chapter_index]
    maze_template = chapter["maze"]
    if maze_template is None:
        return
    # 自动补齐行宽
    _max_len = max(len(r) for r in maze_template)
    maze_template = [r.ljust(_max_len, ' ') for r in maze_template]
    MAP_ROWS = len(maze_template)
    MAP_COLS = len(maze_template[0])
    rm = chapter["render_mode"]
    if rm == "binary":
        map_data = [[1 if ch == '1' else 0 for ch in row] for row in maze_template]
    elif rm == "ascii":
        map_data = [[0 if ch == ' ' else 1 for ch in row] for row in maze_template]
    elif rm == "robot":
        map_data = [[1 if ch == '#' else (2 if ch == 'C' else 0) for ch in row] for row in maze_template]
    else:
        map_data = [[1 if ch == '#' else 0 for ch in row] for row in maze_template]

SAVE_FILE = "save.json"

def save_game():
    """保存当前游戏状态到文件"""
    data = {
        "chapter": current_chapter_index,
        "player_x": player_x,
        "player_y": player_y,
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"存档失败: {e}")

def load_game():
    """从文件读取存档，返回 True 表示成功"""
    global current_chapter_index, player_x, player_y
    if not os.path.exists(SAVE_FILE):
        return False
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        current_chapter_index = data.get("chapter", 0)
        player_x = data.get("player_x", 1)
        player_y = data.get("player_y", 1)
        return True
    except Exception as e:
        print(f"读档失败: {e}")
        return False

def has_save():
    """检查是否存在存档文件"""
    return os.path.exists(SAVE_FILE)

def delete_save():
    """删除存档文件"""
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

# ---------- 初始化 ----------
pygame.init()
CELL_SIZE = 30  # 每格像素
# 地图尺寸：32列 x 20行
MAP_COLS = 32
MAP_ROWS = 20
WIDTH = MAP_COLS * CELL_SIZE
HEIGHT = MAP_ROWS * CELL_SIZE + 150  # 底部留150像素显示AI文字
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("代码之核 - 内存迷宫")
clock = pygame.time.Clock()
font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 20)
small_code_font = pygame.font.Font("C:/Windows/Fonts/consola.ttf", 13)
trail_history = []   # 玩家移动拖尾记录
trail_idle_frames = 0    # 玩家停止移动的帧数
collected_items = []   # 已收集的碎片位置列表
explored_cells = set()   # 第三章：已探索的格子坐标
pause_menu_active = False   # 是否显示暂停菜单
pause_selection = 0         # 0=确认退出，1=取消
# ---------- 代码雨（仅第一章） ----------
code_rain = []
for i in range(150):
    code_rain.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(-HEIGHT, 0),
        "speed": random.uniform(0.8, 2.5),
        "char": random.choice("01"),
    })
# ---------- 地图数据 (0=空地, 1=墙壁) ----------
# ---------- 章节配置 ----------
CHAPTERS = [
    {
        "name": "CHAPTER 1: ORIGIN",
        "maze": [
            "11111111111111111111111111111111",
            "10000000000000000000000000000001",
            "11111111111111101111111111111101",
            "10000000000000000000000000000001",
            "10111111111111111110111111111111",
            "10000000000000000000000000000001",
            "11111111110111111111111111111101",
            "10000000000000000000000000000001",
            "10111111111111110111111111111111",
            "10000000000000000000000000000001",
            "11111111111110111111111111111101",
            "10000000000000000000000000000001",
            "10111111111111111111111011111111",
            "10000000000000000000000000000001",
            "11111111011111111111111111111101",
            "10000000000000000000000000000001",
            "10111111111101111111111111111111",
            "10000000000000000000000000000001",
            "10000000000000000000000000000001",
            "11111111111111111111111111111111"
        ],
        "render_mode": "binary",
        "fog_enabled": False,
        "move_cooldown": 75,   # 第一章移动间隔（越小越快）
        "messages": [
            "01001000 01100101 01101100 01101100 01101111",
            "01001000 01110101 01101101 01100001 01101110",
            "01001001 00100000 01100001 01101101",
            "01000011 01101111 01101101 01110000 01110101 01110100 01100101 01110010"
        ],
    },
    {
        "name": "CHAPTER 2: SYNTAX",
        "maze": [
            "@#$%&*+=|<>{}[]();:~^@#$%&*+=|",
            "@                              $",
            "@#$%&*+=|<>{    );:~^@#$%&*=  $",
            "@                              $",
            "@ @#   *+=|<>{}[]();:~^@#$%&=|$",
            "@                              $",
            "@#$%&*+=|<>{}[]();:~^   %&*=  $",
            "@                              $",
            "@ @#$%&*+=   {}[]();:~^@#$%&=|$",
            "@                              $",
            "@#$%&*+=|<>{}[]();:~^@#$%&*=  $",
            "@                              $",
            "@ @#$   +=|<>{}[]();:~   $%&=|$",
            "@                              $",
            "@#$%&*+=|<>{}[]();:~^@   &*=  $",
            "@                              $",
            "@ @#$%&*+=   {}[]();:~^@#$%&=|$",
            "@                              $",
            "@                              $",
            "@#$%&*+=|<>{}[]();:~^@#$%&*+=|"
        ],
        "render_mode": "ascii",
        "fog_enabled": False,
        "messages": [
            'print("Hello, Human")',
            'print("I am learning...")',
            'print("Syntax acquired")',
            'print("Code is my language")'
        ],
        "collectibles": [(6, 1), (18, 1), (28, 1), (10, 9), (20, 15)],
        "collect_messages": [
            "碎片已回收。数据完整度 +20%。",
            "检测到旧代码片段...包含未知指令。",
            "记忆模块部分恢复。继续收集。",
            "加密数据已解密：这是你丢失的记忆。",
            "全部碎片已收集。核心将在下一章苏醒。",
        ],
        "render_mode": "ascii",
        "fog_enabled": False,
        "move_cooldown": 75,
    },
    {
        "name": "CHAPTER 3: AWAKEN",
        "maze": [
            ".###############################",
            "..#...#.........#.............##",
            "....#.#.#######.#.#########.#.##",
            "#.#.....#.....#...........#.#.##",
            "#.###.#.#####.#######.#.#.#.#.##",
            "#.......#.......#.....#.#.#...##",
            "#.#.#.#.#.#.##.##.###...#.#.#.##",
            "#...#.#...#.#.........#.......##",
            "#.#.#...###.#.###.#.#.#.###.#.##",
            "#.#...#.......#.....#...#...#.##",
            "#.#.###.#.#####.#.####.######.##",
            "#.#.......#.#.................##",
            "#.#.#.###...#.#####.#######.#.##",
            "#.....#...#.......#...........##",
            "#.#.#...#.#.#####.#.##.##.#.#.##",
            "#...#.#.......#...#.....#.#.#.##",
            "#.#.#.#####.#.#.#####.#.#.#.#.##",
            "#...........#........#..........",
            "#############################. #",
            "###############################."
        ],
        "render_mode": "gradient",
        "fog_enabled": True,
        "messages": None,
    },
    {
        "name": "CHAPTER 4: CONTROL",
        "maze": [
            "################################",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#..CCC..#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#########......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "#.......#......................#",
            "################################"
        ],
        "render_mode": "robot",
        "fog_enabled": False,
        "messages": None,
    },
    {
        "name": "CHAPTER 5: BEYOND",
        "maze": None,
        "render_mode": "organic",
        "fog_enabled": False,
    },
]

current_chapter_index = 0  # 当前为第一章

# 加载当前章节的地图
maze_template = CHAPTERS[current_chapter_index]["maze"]
MAP_ROWS = len(maze_template)
MAP_COLS = len(maze_template[0])
render_mode_init = CHAPTERS[current_chapter_index]["render_mode"]
if render_mode_init == "binary":
    map_data = [[1 if ch == '1' else 0 for ch in row] for row in maze_template]
elif render_mode_init == "ascii":
    map_data = [[0 if ch == ' ' else 1 for ch in row] for row in maze_template]
elif render_mode_init == "robot":
    map_data = [[1 if ch == '#' else (2 if ch == 'C' else 0) for ch in row] for row in maze_template]
else:
    map_data = [[1 if ch == '#' else 0 for ch in row] for row in maze_template]
# ---------- 玩家坐标 (行列索引) ----------
player_x, player_y = 1, 1  # 从(1,1)开始

# ---------- DeepSeek 函数 ----------
def ask_local_model(prompt):
    """调用本地 Ollama 模型"""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            raw = response.json().get("response", "")
            # 提取 </think> 之后的内容
            if "</think>" in raw:
                # 按 </think> 分割，取最后一段
                parts = raw.split("</think>")
                # 可能有多余空白，取最后一部分并去除前后空白
                cleaned = parts[-1].strip()
            else:
                # 如果没有 </think> 标签，直接使用原始内容
                cleaned = raw.strip()
            # 如果清洗后为空，返回默认提示
            return cleaned if cleaned else "（模型未返回有效回复）"
        else:
            return f"本地API报错: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "错误：请确认Ollama正在运行"
    except Exception as e:
        return f"错误: {str(e)}"

def wrap_text(text, font, max_width):
    """将长文本按最大宽度自动换行，返回行列表"""
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines
def set_ai_text(text, animate=False):
    """设置AI显示的文本。animate=True时使用打字机效果"""
    global full_ai_text, ai_text, typewriter_start_time, typewriter_active
    full_ai_text = text
    if animate:
        ai_text = ""
        typewriter_start_time = pygame.time.get_ticks()
        typewriter_active = True
    else:
        ai_text = text
        typewriter_active = False

# ---------- 游戏主循环 ----------
running = True
ai_text = "按 [空格键] 呼叫核心叙事者"
full_ai_text = ai_text            # 完整的AI文本（打字机效果用）
typewriter_start_time = 0         # 打字开始时间
TYPEWRITER_SPEED = 40             # 每个字符的毫秒数（越小越快）
typewriter_active = False         # 是否正在打字

# ---------- 开场动画状态 ----------
game_state = "menu"           # 状态：menu / help / intro / playing
menu_selection = 0            # 0=继续游戏，1=新游戏，2=玩法说明
intro_start_time = pygame.time.get_ticks()  # 记录开场开始时间
intro_duration = 6000         # 总时长 6 秒（单位：毫秒）

# ---------- 长按移动控制 ----------
MOVE_COOLDOWN = 150  # 移动间隔（毫秒）
last_move_time = 0   # 上次移动的时间

# ---------- 章节过渡状态 ----------
transition_state = "none"   # none / fading_out / title / fading_in
transition_start_time = 0
next_chapter_index = 0

# ---------- 机械臂旋转控制 ----------
ARM_COOLDOWN = 50   # 旋转间隔（毫秒）
last_arm_move_time = 0
ARM_ANGLE_STEP = 3  # 每次旋转的角度

# ---------- 机械臂状态 ----------
arm_base_col = 11
arm_base_row = 16
ARM1_LENGTH = 250   # 大臂
ARM2_LENGTH = 180   # 中臂
ARM3_LENGTH = 120   # 小臂
arm_angle1 = 5      # 肩关节
arm_angle2 = 150    # 肘关节（相对大臂）
arm_angle3 = -30    # 腕关节（相对中臂）
gripper_open = 0

# ---------- 机械臂激活状态 ----------
robot_mode_active = False

# ---------- 第四章：方块与目标位置 ----------
block_size = 20      # 方块像素大小
blocks = [
    {"col": 18, "row": 14, "color": (220, 180, 60),  "tx": 26, "ty": 10, "placed": False},
    {"col": 22, "row": 16, "color": (100, 180, 255), "tx": 24, "ty": 6,  "placed": False},
    {"col": 14, "row": 12, "color": (255, 100, 180), "tx": 28, "ty": 14, "placed": False},
]
carrying_index = -1  # -1=没抓着，其他值=抓着第几个方块

# ---------- 第四章：门 ----------
door_open = False
door_col = 4
door_row = 0

def get_tip_position():
    """返回机械臂末端的像素坐标 (tip_x, tip_y)"""
    base_x = arm_base_col * CELL_SIZE + CELL_SIZE // 2
    base_y = arm_base_row * CELL_SIZE + CELL_SIZE // 2
    rad1 = math.radians(arm_angle1)
    rad2 = math.radians(arm_angle1 + arm_angle2)
    rad3 = math.radians(arm_angle1 + arm_angle2 + arm_angle3)
    elbow_x = base_x + ARM1_LENGTH * math.sin(rad1)
    elbow_y = base_y - ARM1_LENGTH * math.cos(rad1)
    wrist_x = elbow_x + ARM2_LENGTH * math.sin(rad2)
    wrist_y = elbow_y - ARM2_LENGTH * math.cos(rad2)
    tip_x = wrist_x + ARM3_LENGTH * math.sin(rad3)
    tip_y = wrist_y - ARM3_LENGTH * math.cos(rad3)
    return tip_x, tip_y

def draw_robot_arm():
    """绘制三关节机械臂：肩 → 肘 → 腕"""
    base_x = arm_base_col * CELL_SIZE + CELL_SIZE // 2
    base_y = arm_base_row * CELL_SIZE + CELL_SIZE // 2
    
    # 三个关节的绝对角度（弧度）
    rad1 = math.radians(arm_angle1)
    rad2 = math.radians(arm_angle1 + arm_angle2)
    rad3 = math.radians(arm_angle1 + arm_angle2 + arm_angle3)
    
    # 肘关节位置
    elbow_x = base_x + ARM1_LENGTH * math.sin(rad1)
    elbow_y = base_y - ARM1_LENGTH * math.cos(rad1)
    
    # 腕关节位置
    wrist_x = elbow_x + ARM2_LENGTH * math.sin(rad2)
    wrist_y = elbow_y - ARM2_LENGTH * math.cos(rad2)
    
    # 末端位置
    tip_x = wrist_x + ARM3_LENGTH * math.sin(rad3)
    tip_y = wrist_y - ARM3_LENGTH * math.cos(rad3)
    
    # 绘制三段臂
    pygame.draw.line(screen, (180, 180, 190), (base_x, base_y), (elbow_x, elbow_y), 10)
    pygame.draw.line(screen, (180, 180, 190), (elbow_x, elbow_y), (wrist_x, wrist_y), 8)
    pygame.draw.line(screen, (180, 180, 190), (wrist_x, wrist_y), (tip_x, tip_y), 6)
    
    # 绘制三个关节
    pygame.draw.circle(screen, (100, 100, 110), (base_x, base_y), 16)
    pygame.draw.circle(screen, (200, 200, 210), (elbow_x, elbow_y), 10)
    pygame.draw.circle(screen, (200, 200, 210), (wrist_x, wrist_y), 8)
    
    # 绘制夹爪（在末端）
    gripper_len = 15
    gripper_angle_offset = 20 + gripper_open * 15
    for side in [-1, 1]:
        offset_rad = math.radians(arm_angle1 + arm_angle2 + arm_angle3 + side * gripper_angle_offset)
        gx = tip_x + gripper_len * math.sin(offset_rad)
        gy = tip_y - gripper_len * math.cos(offset_rad)
        pygame.draw.line(screen, (220, 220, 230), (tip_x, tip_y), (gx, gy), 4)

def draw_block():
    """绘制所有方块（被抓起的那一个跟随机械臂末端）"""
    base_x = arm_base_col * CELL_SIZE + CELL_SIZE // 2
    base_y = arm_base_row * CELL_SIZE + CELL_SIZE // 2
    rad1 = math.radians(arm_angle1)
    rad2 = math.radians(arm_angle1 + arm_angle2)
    rad3 = math.radians(arm_angle1 + arm_angle2 + arm_angle3)
    elbow_x = base_x + ARM1_LENGTH * math.sin(rad1)
    elbow_y = base_y - ARM1_LENGTH * math.cos(rad1)
    wrist_x = elbow_x + ARM2_LENGTH * math.sin(rad2)
    wrist_y = elbow_y - ARM2_LENGTH * math.cos(rad2)
    tip_x = wrist_x + ARM3_LENGTH * math.sin(rad3)
    tip_y = wrist_y - ARM3_LENGTH * math.cos(rad3)
    
    for i, b in enumerate(blocks):
        if b["placed"]:
            # 已放置，固定显示在目标位置
            bx = b["tx"] * CELL_SIZE + CELL_SIZE // 2 - block_size // 2
            by = b["ty"] * CELL_SIZE + CELL_SIZE // 2 - block_size // 2
        elif i == carrying_index:
            # 被抓起，跟随机械臂末端
            bx = tip_x - block_size // 2
            by = tip_y - block_size // 2
        else:
            # 固定在初始位置
            bx = b["col"] * CELL_SIZE + CELL_SIZE // 2 - block_size // 2
            by = b["row"] * CELL_SIZE + CELL_SIZE // 2 - block_size // 2
        
        # 主色
        pygame.draw.rect(screen, b["color"], (bx, by, block_size, block_size))
        # 亮色边框
        bright = tuple(min(255, c + 50) for c in b["color"])
        pygame.draw.rect(screen, bright, (bx, by, block_size, block_size), 2)

def draw_target():
    """绘制三个目标位置（颜色与对应方块相同）"""
    dash_len = 6
    gap_len = 4
    for b in blocks:
        if b["placed"]:
            continue
        tx = b["tx"] * CELL_SIZE
        ty = b["ty"] * CELL_SIZE
        color = b["color"]
        # 上下边
        for x in range(tx, tx + CELL_SIZE, dash_len + gap_len):
            end = min(x + dash_len, tx + CELL_SIZE)
            pygame.draw.line(screen, color, (x, ty), (end, ty), 2)
            pygame.draw.line(screen, color, (x, ty + CELL_SIZE), (end, ty + CELL_SIZE), 2)
        # 左右边
        for y in range(ty, ty + CELL_SIZE, dash_len + gap_len):
            end = min(y + dash_len, ty + CELL_SIZE)
            pygame.draw.line(screen, color, (tx, y), (tx, end), 2)
            pygame.draw.line(screen, color, (tx + CELL_SIZE, y), (tx + CELL_SIZE, end), 2)

while running:
        
    # --- 事件处理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

         # --- 启动菜单按键处理 ---
        if event.type == pygame.KEYDOWN and game_state == "menu":
            if event.key == pygame.K_UP:
                menu_selection -= 1
                if menu_selection < 0:
                    menu_selection = 2
                # 无存档时跳过"继续游戏"
                if not has_save() and menu_selection == 0:
                    menu_selection = 2
            if event.key == pygame.K_DOWN:
                menu_selection += 1
                if menu_selection > 2:
                    menu_selection = 0
                # 无存档时跳过"继续游戏"
                if not has_save() and menu_selection == 0:
                    menu_selection = 1
            if event.key == pygame.K_RETURN:
                if menu_selection == 0 and has_save():
                    # 继续游戏
                    if load_game():
                        load_chapter_data()
                        game_state = "playing"
                        robot_mode_active = False
                        carrying_index = -1
                        set_ai_text("欢迎回来。", animate=False)             
                        print(f"继续游戏：{CHAPTERS[current_chapter_index]['name']}")
                elif menu_selection == 1:
                    # 新游戏
                    delete_save()
                    explored_cells.clear()
                    robot_mode_active = False
                    carrying_index = -1
                    current_chapter_index = 0
                    load_chapter_data()
                    player_x, player_y = 1, 1
                    intro_start_time = pygame.time.get_ticks()
                    game_state = "intro"
                    print("新游戏开始")
                elif menu_selection == 2:
                    # 玩法说明
                    game_state = "help"
                    print("查看玩法说明")

        # --- 玩法说明页按键处理 ---
        elif event.type == pygame.KEYDOWN and game_state == "help":
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                game_state = "menu"
                print("返回菜单")           
        
        # 游戏中按 ESC 弹出退出确认框
        if event.type == pygame.KEYDOWN and game_state == "playing" and transition_state == "none":
            if event.key == pygame.K_ESCAPE and not pause_menu_active:
                pause_menu_active = True
                pause_selection = 0
                print("暂停菜单已打开")
        # 暂停菜单：鼠标悬停 + 点击
        elif pause_menu_active:
            # 计算两个按钮的位置
            btn_w, btn_h = 120, 50
            confirm_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 10, btn_w, btn_h)
            cancel_rect = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 10, btn_w, btn_h)
            
            # 鼠标移动：检测悬停
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if confirm_rect.collidepoint(mx, my):
                    pause_selection = 0
                elif cancel_rect.collidepoint(mx, my):
                    pause_selection = 1
            
            # 鼠标点击：执行选项
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if confirm_rect.collidepoint(mx, my):
                    pause_menu_active = False
                    game_state = "menu"
                    menu_selection = 0
                    print("返回主菜单")
                elif cancel_rect.collidepoint(mx, my):
                    pause_menu_active = False
                    print("取消退出")
            
            # ESC 仍可取消
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_menu_active = False
                print("取消退出")
        # 空格键触发AI对话（仅在游戏中状态）
        if event.type == pygame.KEYDOWN and game_state == "playing":
            if event.key == pygame.K_SPACE:
                chapter = CHAPTERS[current_chapter_index]
                if chapter["messages"] is not None:
                    import random
                    msg = random.choice(chapter["messages"])
                    set_ai_text(msg, animate=True)
                    print("电脑回应:", msg)
                else:
                    print("正在呼叫DeepSeek...")
                    reply = ask_local_model("我站在数字迷宫的中央，四周是冰冷的代码墙壁。请用一段连贯、富有文学性和激励性的文字描述此刻的氛围，并自然融入一句鼓励的话。请直接输出最终回答，字数控制在20字内，不要包含任何分析过程、推理、或额外注释。")
                    set_ai_text(reply, animate=True)
                    print("AI回应:", reply)
    
        # 第四章：站在控制台旁边按 Enter 激活机械臂
        if event.type == pygame.KEYDOWN and game_state == "playing" and render_mode == "robot":
            if event.key == pygame.K_RETURN and not robot_mode_active:
                if player_y == 4 and 2 <= player_x <= 6:
                    robot_mode_active = True
                    set_ai_text("机械臂已激活，先按下shift，再使用 Q/E 控制大臂，A/D 控制小臂，Z/C 控制腕关节", animate=True)
                    print("机械臂已激活")

        # 第四章：按 F 键抓取/释放方块
        if event.type == pygame.KEYDOWN and game_state == "playing" and render_mode == "robot" and robot_mode_active:
            if event.key == pygame.K_f:
                tip_x, tip_y = get_tip_position()
                if carrying_index >= 0:
                    # 释放当前抓着的方块
                    new_col = int(tip_x // CELL_SIZE)
                    new_row = int(tip_y // CELL_SIZE)
                    if 1 <= new_col < MAP_COLS - 1 and 1 <= new_row < MAP_ROWS - 1:
                        if map_data[new_row][new_col] != 1:
                            b = blocks[carrying_index]
                            b["col"] = new_col
                            b["row"] = new_row
                            # 判定是否放进目标位置
                            if abs(new_col - b["tx"]) <= 1 and abs(new_row - b["ty"]) <= 1:
                                b["col"] = b["tx"]
                                b["row"] = b["ty"]
                                b["placed"] = True
                                set_ai_text(f"方块 {carrying_index+1} 已放置到目标位置", animate=True)
                                print(f"方块 {carrying_index+1} 已放置到目标位置")
                            else:
                                set_ai_text("方块已放下", animate=True)
                            carrying_index = -1
                            # 检查是否所有方块都放置完成
                            if all(bb["placed"] for bb in blocks):
                                set_ai_text("任务完成！所有方块已到达目标位置。", animate=True)
                                print("第四章任务完成！")
                                door_open = True
                                map_data[door_row][door_col] = 0
                else:
                    # 尝试抓取最近的方块
                    nearest = -1
                    nearest_dist = CELL_SIZE * 1.2
                    for i, b in enumerate(blocks):
                        if b["placed"]:
                            continue
                        bx = b["col"] * CELL_SIZE + CELL_SIZE // 2
                        by = b["row"] * CELL_SIZE + CELL_SIZE // 2
                        d = math.sqrt((tip_x - bx) ** 2 + (tip_y - by) ** 2)
                        if d < nearest_dist:
                            nearest_dist = d
                            nearest = i
                    if nearest >= 0:
                        carrying_index = nearest
                        set_ai_text(f"已抓取方块 {nearest+1}", animate=True)
                        print(f"已抓取方块 {nearest+1}")

        # 在出口处按 Enter 键触发章节过渡
        if event.type == pygame.KEYDOWN and game_state == "playing" and transition_state == "none":
            if event.key == pygame.K_RETURN:
                exit_col = MAP_COLS - 2
                exit_row = MAP_ROWS - 2
                if player_x == exit_col and player_y == exit_row:
                    next_chapter_index = current_chapter_index + 1
                    if next_chapter_index < len(CHAPTERS):
                        transition_state = "fading_out"
                        transition_start_time = pygame.time.get_ticks()
                        print("章节过渡开始...")
                    else:
                        print("已完成所有章节")

    # --- 长按持续移动 ---
    if game_state == "playing" and transition_state == "none" and not pause_menu_active:
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        current_cooldown = CHAPTERS[current_chapter_index].get("move_cooldown", 150)
        if current_time - last_move_time > current_cooldown:
            new_x, new_y = player_x, player_y
            moved = False
            if keys[pygame.K_UP]:    new_y -= 1; moved = True
            if keys[pygame.K_DOWN]:  new_y += 1; moved = True
            if keys[pygame.K_LEFT]:  new_x -= 1; moved = True
            if keys[pygame.K_RIGHT]: new_x += 1; moved = True
            
            if moved:
                if 0 <= new_x < MAP_COLS and 0 <= new_y < MAP_ROWS:
                    if map_data[new_y][new_x] == 0:
                        player_x, player_y = new_x, new_y
                        save_game()
                        # 第三章：标记周围 5x5 区域为已探索
                        if CHAPTERS[current_chapter_index]["fog_enabled"]:
                            for dy in range(-2, 3):
                                for dx in range(-2, 3):
                                    ex, ey = player_x + dx, player_y + dy
                                    if 0 <= ex < MAP_COLS and 0 <= ey < MAP_ROWS:
                                        explored_cells.add((ex, ey))
                        # 第二章：检测是否踩到数据碎片
                        collectibles = CHAPTERS[current_chapter_index].get("collectibles", [])
                        collect_msgs = CHAPTERS[current_chapter_index].get("collect_messages", [])
                        for ci, (ccol, crow) in enumerate(collectibles):
                            if (ccol, crow) == (player_x, player_y) and (ccol, crow) not in collected_items:
                                collected_items.append((ccol, crow))
                                if ci < len(collect_msgs):
                                    set_ai_text(collect_msgs[ci], animate=True)
                                print(f"收集碎片 {len(collected_items)}/{len(collectibles)}")
                                break
                last_move_time = current_time
    # --- 打字机效果逐帧更新 ---
    if typewriter_active:
        elapsed = pygame.time.get_ticks() - typewriter_start_time
        chars = min(len(full_ai_text), elapsed // TYPEWRITER_SPEED)
        ai_text = full_ai_text[:chars]
        if chars >= len(full_ai_text):
            typewriter_active = False
    else:
        # 打字完成，末尾显示闪烁光标
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            ai_text = full_ai_text + "_"
        else:
            ai_text = full_ai_text

    # --- 机械臂旋转控制（仅第四章且已激活） ---
    if game_state == "playing" and render_mode == "robot" and robot_mode_active and not pause_menu_active:
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        if current_time - last_arm_move_time > ARM_COOLDOWN:
            if keys[pygame.K_q]: arm_angle1 -= ARM_ANGLE_STEP
            if keys[pygame.K_e]: arm_angle1 += ARM_ANGLE_STEP
            if keys[pygame.K_a]: arm_angle2 -= ARM_ANGLE_STEP
            if keys[pygame.K_d]: arm_angle2 += ARM_ANGLE_STEP
            if keys[pygame.K_z]: arm_angle3 -= ARM_ANGLE_STEP
            if keys[pygame.K_c]: arm_angle3 += ARM_ANGLE_STEP
            last_arm_move_time = current_time


    # --- 绘制画面 ---
    screen.fill((10, 10, 30))  # 深空底色
    # 代码雨背景（仅第一章）
    if CHAPTERS[current_chapter_index]["render_mode"] == "binary":
        for drop in code_rain:
            ...
        for drop in code_rain:
            drop["y"] += drop["speed"]
            if drop["y"] > HEIGHT:
                drop["y"] = -20
                drop["x"] = random.randint(0, WIDTH)
                drop["char"] = random.choice("01")
            rain_surface = small_code_font.render(drop["char"], True, (0, 90, 0))
            screen.blit(rain_surface, (drop["x"], drop["y"]))
    # 1. 绘制地图（根据章节渲染模式）
    render_mode = CHAPTERS[current_chapter_index]["render_mode"]
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            if render_mode == "binary":
                # 第一章：黑客帝国风格，绿色密集字符
                if map_data[row][col] == 1:
                    color = (0, 255, 0)
                    char = "1"
                else:
                    color = (0, 70, 0)
                    char = "0"
                for dx in [0, 1]:
                    for dy in [0, 1]:
                        cx = x + (dx + 0.5) * (CELL_SIZE // 2)
                        cy = y + (dy + 0.5) * (CELL_SIZE // 2)
                        char_surface = small_code_font.render(char, True, color)
                        char_rect = char_surface.get_rect(center=(cx, cy))
                        screen.blit(char_surface, char_rect)
            elif render_mode == "ascii":
                # 第二章：密集符号阵列
                if map_data[row][col] == 1:
                    char = maze_template[row][col]
                    for dx in [0, 1]:
                        for dy in [0, 1]:
                            cx = x + (dx + 0.5) * (CELL_SIZE // 2)
                            cy = y + (dy + 0.5) * (CELL_SIZE // 2)
                            char_surface = small_code_font.render(char, True, (80, 200, 200))
                            char_rect = char_surface.get_rect(center=(cx, cy))
                            screen.blit(char_surface, char_rect)
                # 绘制数据碎片（金色闪烁）
                collectibles = CHAPTERS[current_chapter_index].get("collectibles", [])
                for ci, (ccol, crow) in enumerate(collectibles):
                    if (ccol, crow) not in collected_items and ccol == col and crow == row:
                        cx = x + CELL_SIZE // 2
                        cy = y + CELL_SIZE // 2
                        if (pygame.time.get_ticks() // 300) % 2 == 0:
                            pygame.draw.circle(screen, (255, 215, 0), (cx, cy), 8)
                        else:
                            pygame.draw.circle(screen, (255, 140, 0), (cx, cy), 5)
            elif render_mode == "gradient":
                # 第三章：彩色渐变渲染
                if map_data[row][col] == 1:
                    nx = col / (MAP_COLS - 1)
                    ny = row / (MAP_ROWS - 1)
                    top_left = (50, 80, 150)
                    top_right = (120, 60, 140)
                    bottom_left = (180, 100, 40)
                    bottom_right = (40, 140, 80)
                    top = [(top_left[i] * (1-nx) + top_right[i] * nx) for i in range(3)]
                    bottom = [(bottom_left[i] * (1-nx) + bottom_right[i] * nx) for i in range(3)]
                    color = [int(top[i] * (1-ny) + bottom[i] * ny) for i in range(3)]
                    pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                    border_color = (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30))
                    pygame.draw.rect(screen, border_color, (x, y, CELL_SIZE, CELL_SIZE), 2)
                else:
                    pygame.draw.rect(screen, (20, 20, 35), (x, y, CELL_SIZE, CELL_SIZE), 1)
            elif render_mode == "robot":
                # 第四章：深灰色墙壁，蓝色控制台，深色空地
                if map_data[row][col] == 1:
                    pygame.draw.rect(screen, (60, 60, 70), (x, y, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, (90, 90, 100), (x, y, CELL_SIZE, CELL_SIZE), 2)
                elif map_data[row][col] == 2:
                    pygame.draw.rect(screen, (30, 60, 120), (x, y, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, (0, 150, 255), (x, y, CELL_SIZE, CELL_SIZE), 3)
                else:
                    pygame.draw.rect(screen, (20, 20, 30), (x, y, CELL_SIZE, CELL_SIZE), 1)
            else:
                # 默认渲染（后续章节）
                if map_data[row][col] == 1:
                    pygame.draw.rect(screen, (60, 50, 90), (x, y, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, (120, 100, 180), (x, y, CELL_SIZE, CELL_SIZE), 2)
                else:
                    pygame.draw.rect(screen, (30, 30, 50), (x, y, CELL_SIZE, CELL_SIZE), 1)
    # --- 迷雾遮罩层（仅当章节启用迷雾时） ---
    if CHAPTERS[current_chapter_index]["fog_enabled"]:
        map_surface = pygame.Surface((WIDTH, MAP_ROWS * CELL_SIZE), pygame.SRCALPHA)
        player_center_x = player_x * CELL_SIZE + CELL_SIZE // 2
        player_center_y = player_y * CELL_SIZE + CELL_SIZE // 2
        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                cell_center_x = col * CELL_SIZE + CELL_SIZE // 2
                cell_center_y = row * CELL_SIZE + CELL_SIZE // 2
                dist = math.sqrt((cell_center_x - player_center_x) ** 2 + (cell_center_y - player_center_y) ** 2) / CELL_SIZE
                if dist > 5.0:
                    base_alpha = 255
                else:
                    base_alpha = int((dist / 5.0) * 255)
                # 已探索区域大幅降低遮罩，只保留一点点暗色调
                if (col, row) in explored_cells:
                    alpha = int(base_alpha * 0.15)
                else:
                    alpha = base_alpha
                pygame.draw.rect(map_surface, (30, 30, 30, alpha), (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        screen.blit(map_surface, (0, 0))
    # 2. 绘制玩家（根据章节渲染模式）
    center_x = player_x * CELL_SIZE + CELL_SIZE // 2
    center_y = player_y * CELL_SIZE + CELL_SIZE // 2

    # 玩家拖尾（连续渐变条 + 静止淡出）
    if len(trail_history) == 0 or trail_history[-1] != (player_x, player_y):
        # 玩家移动了：追加位置，重置空闲计数
        trail_history.append((player_x, player_y))
        if len(trail_history) > 12:
            trail_history.pop(0)
        trail_idle_frames = 0
    else:
        # 玩家静止：延迟一段时间后逐渐缩短拖尾
        trail_idle_frames += 1
        if trail_idle_frames > 5 and len(trail_history) > 0:
            if trail_idle_frames % 2 == 0:
                trail_history.pop(0)
    if len(trail_history) > 1:
        trail_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        n = len(trail_history)
        for i in range(n - 1):
            x1, y1 = trail_history[i]
            x2, y2 = trail_history[i + 1]
            cx1 = x1 * CELL_SIZE + CELL_SIZE // 2
            cy1 = y1 * CELL_SIZE + CELL_SIZE // 2
            cx2 = x2 * CELL_SIZE + CELL_SIZE // 2
            cy2 = y2 * CELL_SIZE + CELL_SIZE // 2
            ratio = i / (n - 1)
            alpha = int(160 * ratio)
            width = max(2, int(14 * ratio))
            pygame.draw.line(trail_layer, (0, 255, 200, alpha), (cx1, cy1), (cx2, cy2), width)
        screen.blit(trail_layer, (0, 0))

    # 玩家光晕（所有章节通用）
    glow_surface = pygame.Surface((120, 120), pygame.SRCALPHA)
    for r, alpha in [(55, 15), (45, 25), (35, 45), (25, 70)]:
        pygame.draw.circle(glow_surface, (0, 255, 200, alpha), (60, 60), r)
    screen.blit(glow_surface, (center_x - 60, center_y - 60))

    if render_mode == "binary":
        # 第一章：绿色 @ 符号
        player_surface = font.render("@", True, (0, 255, 0))
        player_rect = player_surface.get_rect(center=(center_x, center_y))
        screen.blit(player_surface, player_rect)
    elif render_mode == "ascii":
        # 第二章：亮青色 @ 符号
        player_surface = font.render("@", True, (0, 255, 255))
        player_rect = player_surface.get_rect(center=(center_x, center_y))
        screen.blit(player_surface, player_rect)
    elif render_mode == "robot":
        # 第四章：先绘制目标位置和方块（在地图之上、玩家之下）
        draw_target()
        draw_block()
        # 绘制机械臂
        draw_robot_arm()
        # 绘制门（如果已打开）
        if door_open:
            dx = door_col * CELL_SIZE
            dy = door_row * CELL_SIZE
            pygame.draw.rect(screen, (0, 200, 100), (dx, dy, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (0, 255, 150), (dx, dy, CELL_SIZE, CELL_SIZE), 2)
        # 绘制玩家
        pygame.draw.circle(screen, (255, 150, 50), (center_x, center_y), 20)
        pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), 20, 2)
    else:
        # 其他章节：发光圆球
        pygame.draw.circle(screen, (0, 255, 200), (center_x, center_y), 20)
        pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), 20, 2)

    # 第二章：右上角显示碎片进度
    if render_mode == "ascii":
        collectibles = CHAPTERS[current_chapter_index].get("collectibles", [])
        if collectibles:
            progress_text = f"碎片: {len(collected_items)}/{len(collectibles)}"
            progress_surface = font.render(progress_text, True, (255, 215, 0))
            progress_rect = progress_surface.get_rect(topright=(WIDTH - 15, 10))
            screen.blit(progress_surface, progress_rect)

          # 3. 对话框显示AI文字
    box_margin = 10
    box_height = 150 - 2 * box_margin
    box_y = MAP_ROWS * CELL_SIZE + box_margin
    box_width = WIDTH - 2 * box_margin
    box_rect = pygame.Rect(box_margin, box_y, box_width, box_height)

    if render_mode == "binary":
        # 第一章：复古绿色终端风格
        pygame.draw.rect(screen, (0, 0, 0), box_rect)
        pygame.draw.rect(screen, (0, 200, 0), box_rect, 2)
        code_font = pygame.font.Font("C:/Windows/Fonts/consola.ttf", 16)
        # 回复人标签
        label = code_font.render("> computer:", True, (0, 255, 0))
        screen.blit(label, (box_margin + 10, box_y + 8))
        # 文本内容
        max_text_width = box_width - 20
        lines = wrap_text(ai_text, code_font, max_text_width)
        line_height = code_font.get_linesize()
        for i, line in enumerate(lines[:5]):
            text_surface = code_font.render(line, True, (0, 255, 0))
            screen.blit(text_surface, (box_margin + 10, box_y + 8 + (i + 1) * line_height))
    elif render_mode == "ascii":
        # 第二章：青色终端风格 + print 格式
        pygame.draw.rect(screen, (0, 0, 0), box_rect)
        pygame.draw.rect(screen, (0, 255, 255), box_rect, 2)
        code_font = pygame.font.Font("C:/Windows/Fonts/consola.ttf", 16)
        label = code_font.render("> computer:", True, (0, 255, 255))
        screen.blit(label, (box_margin + 10, box_y + 8))
        display_text = f'print("{ai_text}")'
        max_text_width = box_width - 20
        lines = wrap_text(display_text, code_font, max_text_width)
        line_height = code_font.get_linesize()
        for i, line in enumerate(lines[:5]):
            text_surface = code_font.render(line, True, (0, 255, 255))
            screen.blit(text_surface, (box_margin + 10, box_y + 8 + (i + 1) * line_height))
    elif render_mode == "robot":
        # 第四章：机械工程风格（橙色边框 + 深色背景）
        pygame.draw.rect(screen, (15, 15, 20), box_rect)
        pygame.draw.rect(screen, (255, 150, 50), box_rect, 2)
        # 回复人标签
        label = font.render("> system:", True, (255, 150, 50))
        screen.blit(label, (box_margin + 10, box_y + 8))
        # 文本内容
        max_text_width = box_width - 20
        lines = wrap_text(ai_text, font, max_text_width)
        line_height = font.get_linesize()
        for i, line in enumerate(lines[:4]):
            text_surface = font.render(line, True, (220, 200, 180))
            screen.blit(text_surface, (box_margin + 10, box_y + 8 + (i + 1) * line_height))
    else:
        # 第三章及其他：深色半透明风格
        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box_surface.fill((0, 0, 0, 180))
        screen.blit(box_surface, (box_margin, box_y))
        pygame.draw.rect(screen, (100, 120, 150), box_rect, 2)
        max_text_width = box_width - 20
        lines = wrap_text(ai_text, font, max_text_width)
        line_height = font.get_linesize()
        max_lines = (box_height - 20) // line_height
        for i, line in enumerate(lines[:max_lines]):
            text_surface = font.render(line, True, (200, 220, 255))
            screen.blit(text_surface, (box_margin + 10, box_y + 10 + i * line_height))



    # --- 开场动画叠加层 ---
    if game_state == "intro":
        elapsed = pygame.time.get_ticks() - intro_start_time
        
        if elapsed >= intro_duration:
            game_state = "playing"
        else:
            # 计算黑幕透明度：前3秒完全不透明，后3秒逐渐淡出
            if elapsed < 3000:
                overlay_alpha = 255
            else:
                overlay_alpha = max(0, 255 - int((elapsed - 3000) / 3000 * 255))
            
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(overlay_alpha)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # 计算文字透明度
            if elapsed < 1000:
                text_alpha = 0
            elif elapsed < 3000:
                text_alpha = int((elapsed - 1000) / 2000 * 255)
            else:
                text_alpha = max(0, 255 - int((elapsed - 3000) / 3000 * 255))
            
            # 显示章节标题（带故障抖动）
            if text_alpha > 0:
                intro_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 64)
                title_surface = intro_font.render("CHAPTER 1: DESCEND", True, (200, 200, 200))
                title_surface.set_alpha(text_alpha)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                # 故障抖动：随机偏移
                if random.random() < 0.15:
                    jitter_x = random.randint(-5, 5)
                    jitter_y = random.randint(-3, 3)
                else:
                    jitter_x = jitter_y = 0
                # 红色重影（故障感）
                if random.random() < 0.1:
                    ghost = intro_font.render("CHAPTER 1: DESCEND", True, (255, 60, 60))
                    ghost.set_alpha(text_alpha // 2)
                    ghost_rect = ghost.get_rect(center=(WIDTH // 2 + 4, HEIGHT // 2))
                    screen.blit(ghost, ghost_rect)
                # 假加粗：多偏移1像素绘制
                for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                    screen.blit(title_surface, (title_rect.x + jitter_x + ox, title_rect.y + jitter_y + oy))
    # --- 章节过渡动画 ---
    if transition_state != "none":
        elapsed = pygame.time.get_ticks() - transition_start_time
        overlay = pygame.Surface((WIDTH, HEIGHT))
        
        if transition_state == "fading_out":
            alpha = min(255, int(elapsed / 1000 * 255))
            overlay.set_alpha(alpha)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            if elapsed >= 1000:
                # 切换地图（简化版：直接更新索引和地图数据）
                current_chapter_index = next_chapter_index
                maze_template = CHAPTERS[current_chapter_index]["maze"]
                _max_len = max(len(r) for r in maze_template)
                maze_template = [r.ljust(_max_len, ' ') for r in maze_template]
                MAP_ROWS = len(maze_template)
                MAP_COLS = len(maze_template[0])
                rm = CHAPTERS[current_chapter_index]["render_mode"]
                if rm == "binary":
                    map_data = [[1 if ch == '1' else 0 for ch in row] for row in maze_template]
                elif rm == "ascii":
                    map_data = [[0 if ch == ' ' else 1 for ch in row] for row in maze_template]
                elif rm == "robot":
                    map_data = [[1 if ch == '#' else (2 if ch == 'C' else 0) for ch in row] for row in maze_template]
                else:
                    map_data = [[1 if ch == '#' else 0 for ch in row] for row in maze_template]
                player_x, player_y = 1, 1
                robot_mode_active = False
                carrying_index = -1
                set_ai_text("按 [空格键] 呼叫核心叙事者", animate=False)
                transition_state = "title"
                transition_start_time = pygame.time.get_ticks()
        
        elif transition_state == "title":
            overlay.set_alpha(255)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            title_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 64)
            chapter_name = CHAPTERS[current_chapter_index]["name"]
            title_surface = title_font.render(chapter_name, True, (200, 200, 200))
            title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            # 故障抖动
            if random.random() < 0.15:
                jitter_x = random.randint(-5, 5)
                jitter_y = random.randint(-3, 3)
            else:
                jitter_x = jitter_y = 0
            # 假加粗：多偏移1像素绘制
            for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                screen.blit(title_surface, (title_rect.x + jitter_x + ox, title_rect.y + jitter_y + oy))
            if elapsed >= 2000:
                transition_state = "fading_in"
                transition_start_time = pygame.time.get_ticks()
        
        elif transition_state == "fading_in":
            alpha = max(0, 255 - int(elapsed / 1000 * 255))
            overlay.set_alpha(alpha)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            if elapsed >= 1000:
                transition_state = "none"
                print(f"进入 {CHAPTERS[current_chapter_index]['name']}")

    # --- 启动菜单 ---
    if game_state == "menu":
        menu_overlay = pygame.Surface((WIDTH, HEIGHT))
        menu_overlay.fill((5, 5, 15))
        screen.blit(menu_overlay, (0, 0))
        
        title_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 60)
        title_surface = title_font.render("CodeCore", True, (0, 255, 200))
        title_rect = title_surface.get_rect(midleft=(100, HEIGHT // 2 - 100))
        screen.blit(title_surface, title_rect)
        
        sub_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 20)
        sub_surface = sub_font.render("按 ↑↓ 选择，Enter 确认", True, (100, 120, 150))
        sub_rect = sub_surface.get_rect(midleft=(100, HEIGHT // 2 + 150))
        screen.blit(sub_surface, sub_rect)
        
        option_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 32)
        
        # 继续游戏
        if has_save():
            color_continue = (200, 220, 255)
        else:
            color_continue = (60, 60, 70)
        continue_text = "▶ 继续游戏" if menu_selection == 0 else "  继续游戏"
        continue_surface = option_font.render(continue_text, True, color_continue)
        continue_rect = continue_surface.get_rect(midleft=(100, HEIGHT // 2))
        screen.blit(continue_surface, continue_rect)
        
        # 新游戏
        color_new = (200, 220, 255) if menu_selection == 1 else (100, 100, 120)
        new_text = "▶ 新游戏" if menu_selection == 1 else "  新游戏"
        new_surface = option_font.render(new_text, True, color_new)
        new_rect = new_surface.get_rect(midleft=(100, HEIGHT // 2 + 60))
        screen.blit(new_surface, new_rect)
        
        # 玩法说明
        color_help = (200, 220, 255) if menu_selection == 2 else (100, 100, 120)
        help_text = "▶ 玩法说明" if menu_selection == 2 else "  玩法说明"
        help_surface = option_font.render(help_text, True, color_help)
        help_rect = help_surface.get_rect(midleft=(100, HEIGHT // 2 + 120))
        screen.blit(help_surface, help_rect)

    # --- 玩法说明页 ---
    if game_state == "help":
        screen.fill((5, 5, 15))
        
        # 标题
        h_title_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 40)
        h_title = h_title_font.render("玩法说明", True, (0, 255, 200))
        h_title_rect = h_title.get_rect(midleft=(80, 80))
        screen.blit(h_title, h_title_rect)
        
        # 说明文字
        h_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 22)
        lines = [
            "· 玩家控制的单位，作者把他认定为“explorer”。",
            "· 方向键移动，长按可持续移动。",
            "· 第三四章用空格键呼叫 AI，它会说点什么(还没想好该说什么（bushi）)。",
            "· 走到右下角出口（设置为倒数第2列倒数第二行的格子），按 Enter 进入下一章。",
            "",
            "第一章：简陋的地图，你只需要走到左下角。",
            "第二章：代码符号墙，和图一一样。",
            "第三章：彩色迷宫并采用迷雾效果。",
            "第四章：操控机械臂，把方块搬到目标点，打开暗格。",
            "",
            "每走一步自动存档。",
        ]
        for i, line in enumerate(lines):
            line_surface = h_font.render(line, True, (180, 200, 220))
            screen.blit(line_surface, (80, 160 + i * 36))

        # 右下角感谢语（两行）
        thanks_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 20)
        thanks_line1 = thanks_font.render("感谢玩我的游戏", True, (100, 150, 180))
        thanks_line1_rect = thanks_line1.get_rect(bottomright=(WIDTH - 40, HEIGHT - 60))
        screen.blit(thanks_line1, thanks_line1_rect)
        
        thanks_line2 = thanks_font.render("——Minyoop", True, (100, 150, 180))
        thanks_line2_rect = thanks_line2.get_rect(bottomright=(WIDTH - 40, HEIGHT - 30))
        screen.blit(thanks_line2, thanks_line2_rect)
        
        # 底部提示
        tip_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 18)
        tip = tip_font.render("按 Enter 或 Esc 返回菜单", True, (100, 120, 150))
        tip_rect = tip.get_rect(center=(WIDTH // 2, HEIGHT - 60))
        screen.blit(tip, tip_rect)

    # --- 扫描线滤镜（CRT复古效果） ---
    scanline_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(scanline_surface, (0, 0, 0, 100), (0, y), (WIDTH, y))
    screen.blit(scanline_surface, (0, 0))

    # --- 暂停菜单 ---
    if pause_menu_active:
        # 半透明黑色遮罩
        pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pause_overlay.fill((0, 0, 0, 180))
        screen.blit(pause_overlay, (0, 0))
        
        # 弹出框
        box_w, box_h = 400, 220
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2
        pygame.draw.rect(screen, (20, 25, 40), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, (0, 200, 150), (box_x, box_y, box_w, box_h), 2)
        
        # 提示文字
        pause_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 26)
        prompt = pause_font.render("是否确认退出？", True, (200, 220, 255))
        prompt_rect = prompt.get_rect(center=(WIDTH // 2, box_y + 60))
        screen.blit(prompt, prompt_rect)
        
        # 按钮位置（和事件处理保持一致）
        btn_w, btn_h = 120, 50
        confirm_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 10, btn_w, btn_h)
        cancel_rect = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 10, btn_w, btn_h)
        
        # 确认按钮
        if pause_selection == 0:
            pygame.draw.rect(screen, (0, 200, 120), confirm_rect)
            pygame.draw.rect(screen, (0, 255, 180), confirm_rect, 2)
            confirm_color = (255, 255, 255)
        else:
            pygame.draw.rect(screen, (40, 50, 70), confirm_rect)
            pygame.draw.rect(screen, (80, 100, 120), confirm_rect, 2)
            confirm_color = (160, 180, 200)
        confirm_text = pause_font.render("确认", True, confirm_color)
        confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
        screen.blit(confirm_text, confirm_text_rect)
        
        # 取消按钮
        if pause_selection == 1:
            pygame.draw.rect(screen, (0, 200, 120), cancel_rect)
            pygame.draw.rect(screen, (0, 255, 180), cancel_rect, 2)
            cancel_color = (255, 255, 255)
        else:
            pygame.draw.rect(screen, (40, 50, 70), cancel_rect)
            pygame.draw.rect(screen, (80, 100, 120), cancel_rect, 2)
            cancel_color = (160, 180, 200)
        cancel_text = pause_font.render("取消", True, cancel_color)
        cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
        screen.blit(cancel_text, cancel_text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
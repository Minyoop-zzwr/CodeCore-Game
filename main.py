import pygame
import sys
import requests
import json
import re
import math
import os

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
            "@ @#$   +=|<>{}[]();:~^@#$%&=|$",
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
# ---------- 游戏主循环 ----------
running = True
ai_text = "按 [空格键] 呼叫核心叙事者"

# ---------- 开场动画状态 ----------
game_state = "menu"           # 状态：menu / intro / playing
menu_selection = 0            # 菜单当前选中的选项（0=继续游戏，1=新游戏）
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
block_col = 18       # 方块初始列
block_row = 14       # 方块初始行
block_size = 20      # 方块像素大小
target_col = 26      # 目标位置列
target_row = 10      # 目标位置行
is_carrying = False  # 是否正在抓取方块
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
    """绘制方块（如果被抓取，跟随机械臂末端）"""
    if is_carrying:
        # 跟随机械臂末端
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
        bx = tip_x - block_size // 2
        by = tip_y - block_size // 2
    else:
        # 固定在初始位置
        bx = block_col * CELL_SIZE + CELL_SIZE // 2 - block_size // 2
        by = block_row * CELL_SIZE + CELL_SIZE // 2 - block_size // 2
    
    pygame.draw.rect(screen, (220, 180, 60), (bx, by, block_size, block_size))
    pygame.draw.rect(screen, (255, 220, 120), (bx, by, block_size, block_size), 2)


def draw_target():
    """绘制目标位置（虚线框）"""
    tx = target_col * CELL_SIZE
    ty = target_row * CELL_SIZE
    # 用四条短线段画虚线框
    dash_len = 6
    gap_len = 4
    color = (80, 255, 120)
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
            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                # 如果有存档，两个选项之间切换；没有存档，只能选"新游戏"
                if has_save():
                    menu_selection = 1 - menu_selection
                else:
                    menu_selection = 0
            if event.key == pygame.K_RETURN:
                if menu_selection == 0 and has_save():
                    # 继续游戏
                    if load_game():
                        load_chapter_data()
                        game_state = "playing"
                        ai_text = "欢迎回来。"
                        print(f"继续游戏：{CHAPTERS[current_chapter_index]['name']}")
                else:
                    # 新游戏
                    delete_save()
                    current_chapter_index = 0
                    load_chapter_data()
                    player_x, player_y = 1, 1
                    intro_start_time = pygame.time.get_ticks()
                    game_state = "intro"
                    print("新游戏开始")
            
        
        # 空格键触发AI对话（仅在游戏中状态）
        if event.type == pygame.KEYDOWN and game_state == "playing":
            if event.key == pygame.K_SPACE:
                chapter = CHAPTERS[current_chapter_index]
                if chapter["messages"] is not None:
                    import random
                    ai_text = random.choice(chapter["messages"])
                    print("电脑回应:", ai_text)
                else:
                    print("正在呼叫DeepSeek...")
                    reply = ask_local_model("我站在数字迷宫的中央，四周是冰冷的代码墙壁。请用一段连贯、富有文学性和激励性的文字描述此刻的氛围，并自然融入一句鼓励的话。请直接输出最终回答，字数控制在20字内，不要包含任何分析过程、推理、或额外注释。")
                    ai_text = reply
                    print("AI回应:", reply)
    
        # 第四章：站在控制台旁边按 Enter 激活机械臂
        if event.type == pygame.KEYDOWN and game_state == "playing" and render_mode == "robot":
            if event.key == pygame.K_RETURN and not robot_mode_active:
                if player_y == 4 and 2 <= player_x <= 6:
                    robot_mode_active = True
                    ai_text = "机械臂已激活，使用 Q/E 控制大臂，A/D 控制小臂，Z/C 控制腕关节"
                    print("机械臂已激活")

        # 第四章：按 F 键抓取/释放方块
        if event.type == pygame.KEYDOWN and game_state == "playing" and render_mode == "robot" and robot_mode_active:
            if event.key == pygame.K_f:
                tip_x, tip_y = get_tip_position()
                if is_carrying:
                    # 释放方块
                    new_col = int(tip_x // CELL_SIZE)
                    new_row = int(tip_y // CELL_SIZE)
                    if 1 <= new_col < MAP_COLS - 1 and 1 <= new_row < MAP_ROWS - 1:
                        if map_data[new_row][new_col] != 1:
                            is_carrying = False
                            block_col = new_col
                            block_row = new_row
                            ai_text = "方块已放置"
                            print("方块已放置")
                            if block_col == target_col and block_row == target_row:
                                ai_text = "任务完成！方块已到达目标位置。"
                                print("第四章任务完成！")
                                door_open = True
                                map_data[door_row][door_col] = 0
                else:
                    # 尝试抓取
                    block_center_x = block_col * CELL_SIZE + CELL_SIZE // 2
                    block_center_y = block_row * CELL_SIZE + CELL_SIZE // 2
                    dist = math.sqrt((tip_x - block_center_x) ** 2 + (tip_y - block_center_y) ** 2)
                    if dist < CELL_SIZE:
                        is_carrying = True
                        ai_text = "方块已抓取"
                        print("方块已抓取")

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
    if game_state == "playing" and transition_state == "none":
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
                last_move_time = current_time

    # --- 机械臂旋转控制（仅第四章且已激活） ---
    if game_state == "playing" and render_mode == "robot" and robot_mode_active:
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
    # 1. 绘制地图（根据章节渲染模式）
    render_mode = CHAPTERS[current_chapter_index]["render_mode"]
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            if render_mode == "binary":
                # 第一章：二进制字符渲染
                if map_data[row][col] == 1:
                    char_surface = font.render("1", True, (220, 220, 220))
                else:
                    char_surface = font.render("0", True, (50, 50, 70))
                char_rect = char_surface.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(char_surface, char_rect)
            elif render_mode == "ascii":
                # 第二章：直接渲染地图字符
                if map_data[row][col] == 1:
                    char = maze_template[row][col]
                    char_surface = font.render(char, True, (80, 200, 200))
                    char_rect = char_surface.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    screen.blit(char_surface, char_rect)
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
                    alpha = 255
                else:
                    alpha = int((dist / 5.0) * 255)
                pygame.draw.rect(map_surface, (30, 30, 30, alpha), (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        screen.blit(map_surface, (0, 0))    
    # 2. 绘制玩家（根据章节渲染模式）
    center_x = player_x * CELL_SIZE + CELL_SIZE // 2
    center_y = player_y * CELL_SIZE + CELL_SIZE // 2
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
            
            # 显示章节标题
            if text_alpha > 0:
                intro_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 36)
                title_surface = intro_font.render("CHAPTER 1: DESCEND", True, (150, 150, 150))
                title_surface.set_alpha(text_alpha)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(title_surface, title_rect)

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
                ai_text = "按 [空格键] 呼叫核心叙事者"
                transition_state = "title"
                transition_start_time = pygame.time.get_ticks()
        
        elif transition_state == "title":
            overlay.set_alpha(255)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            title_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 36)
            chapter_name = CHAPTERS[current_chapter_index]["name"]
            title_surface = title_font.render(chapter_name, True, (150, 150, 150))
            title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(title_surface, title_rect)
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
        # 用纯黑覆盖整个屏幕
        menu_overlay = pygame.Surface((WIDTH, HEIGHT))
        menu_overlay.fill((5, 5, 15))
        screen.blit(menu_overlay, (0, 0))
        
        # 标题
        title_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 60)
        title_surface = title_font.render("CodeCore", True, (0, 255, 200))
        title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        screen.blit(title_surface, title_rect)
        
        # 副标题
        sub_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 20)
        sub_surface = sub_font.render("按 ↑↓ 选择，Enter 确认", True, (100, 120, 150))
        sub_rect = sub_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
        screen.blit(sub_surface, sub_rect)
        
        # 选项
        option_font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 32)
        
        # 继续游戏
        if has_save():
            color_continue = (200, 220, 255)
        else:
            color_continue = (60, 60, 70)
        if menu_selection == 0:
            continue_text = "▶ 继续游戏"
        else:
            continue_text = "  继续游戏"
        continue_surface = option_font.render(continue_text, True, color_continue)
        continue_rect = continue_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10))
        screen.blit(continue_surface, continue_rect)
        
        # 新游戏
        color_new = (200, 220, 255)
        if menu_selection == 1:
            new_text = "▶ 新游戏"
        else:
            new_text = "  新游戏"
        new_surface = option_font.render(new_text, True, color_new)
        new_rect = new_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(new_surface, new_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
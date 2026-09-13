import pygame
import sys
import requests
import json
import re
import math

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
        "messages": [
            "01001000 01100101 01101100 01101100 01101111",
            "01001000 01110101 01101101 01100001 01101110",
            "01001001 00100000 01100001 01101101",
            "01000011 01101111 01101101 01110000 01110101 01110100 01100101 01110010"
        ],
    },
    {
        "name": "CHAPTER 2: SYNTAX",
        "maze": None,
        "render_mode": "ascii",
        "fog_enabled": False,
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
            "###############################.",
            "###############################."
        ],
        "render_mode": "gradient",
        "fog_enabled": True,
        "messages": None,
    },
    {
        "name": "CHAPTER 4: CONTROL",
        "maze": None,
        "render_mode": "robot",
        "fog_enabled": False,
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
map_data = [[1 if ch == '1' else 0 for ch in row] for row in maze_template]
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
game_state = "intro"          # 状态：intro 或 playing
intro_start_time = pygame.time.get_ticks()  # 记录开场开始时间
intro_duration = 6000         # 总时长 6 秒（单位：毫秒）

# ---------- 长按移动控制 ----------
MOVE_COOLDOWN = 150  # 移动间隔（毫秒）
last_move_time = 0   # 上次移动的时间

while running:
        
    # --- 事件处理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
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
    
    # --- 长按持续移动 ---
    if game_state == "playing":
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        if current_time - last_move_time > MOVE_COOLDOWN:
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
                last_move_time = current_time


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

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
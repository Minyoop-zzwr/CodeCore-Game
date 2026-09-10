import pygame
import sys
import requests
import json
import re

# ---------- 初始化 ----------
pygame.init()
CELL_SIZE = 45  # 每格像素
# 地图尺寸：16列 x 10行
MAP_COLS = 16
MAP_ROWS = 10
WIDTH = MAP_COLS * CELL_SIZE
HEIGHT = MAP_ROWS * CELL_SIZE + 80  # 底部留80像素显示AI文字
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("代码之核 - 内存迷宫")
clock = pygame.time.Clock()
font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 20)
# ---------- 地图数据 (0=空地, 1=墙壁) ----------
maze_template = [
    "################",
    "#..#....#......#",
    "#..#.##.#.####.#",
    "#....#..#....#.#",
    "#.##.####.#..#.#",
    "#..#......#..#.#",
    "#.#.####.##..#.#",
    "#.#....#....#..#",
    "#..####.#.####.#",
    "################"
]
MAP_ROWS = len(maze_template)
MAP_COLS = len(maze_template[0])
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
# ---------- 游戏主循环 ----------
running = True
ai_text = "按 [空格键] 呼叫核心叙事者"
scroll_index = 0
ai_lines = []

while running:
    # --- 事件处理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            # 计算移动后的新坐标
            new_x, new_y = player_x, player_y
            if event.key == pygame.K_UP:    new_y -= 1
            if event.key == pygame.K_DOWN:  new_y += 1
            if event.key == pygame.K_LEFT:  new_x -= 1
            if event.key == pygame.K_RIGHT: new_x += 1
            
            # 碰撞检测：只有目标格子是空地(0)才允许移动
            if 0 <= new_x < MAP_COLS and 0 <= new_y < MAP_ROWS:
                if map_data[new_y][new_x] == 0:
                    player_x, player_y = new_x, new_y
            
            # 按空格键呼叫AI
            if event.key == pygame.K_SPACE:
                print("正在呼叫DeepSeek...")
                reply =ask_local_model ("我站在数字迷宫的中央，四周是冰冷的代码墙壁。请用一段连贯、富有文学性和激励性的文字描述此刻的氛围，并自然融入一句鼓励的话。请直接输出最终回答，字数控制在20字内，不要包含任何分析过程、推理、或额外注释。")
                ai_text = reply
                scroll_index = 0
                # 按每行30个字符切分（可根据字体大小调整）
                chars_per_line = 30
                lines = []
                for i in range(0, len(reply), chars_per_line):
                    lines.append(reply[i:i+chars_per_line])
                ai_lines = lines
                print("AI回应:", reply)

             # 上下键滚动显示
            if event.key == pygame.K_UP:
                if ai_lines and scroll_index > 0:
                    scroll_index -= 1
                    ai_text = ai_lines[scroll_index] if ai_lines else "（空）"
            if event.key == pygame.K_DOWN:
                if ai_lines and scroll_index < len(ai_lines) - 1:
                    scroll_index += 1
                    ai_text = ai_lines[scroll_index] if ai_lines else "（空）"

    # --- 绘制画面 ---
    screen.fill((10, 10, 30))  # 深空底色
          # 1. 绘制地图（带区域渐变颜色）
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            if map_data[row][col] == 1:
                # 根据坐标计算颜色（四个区域混合）
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
                # 空地（深色网格）
                pygame.draw.rect(screen, (20, 20, 35), (x, y, CELL_SIZE, CELL_SIZE), 1)
    
    # 2. 绘制玩家（发光圆球）
    center_x = player_x * CELL_SIZE + CELL_SIZE // 2
    center_y = player_y * CELL_SIZE + CELL_SIZE // 2
    pygame.draw.circle(screen, (0, 255, 200), (center_x, center_y), 20)  # 青色
    pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), 20, 2)  # 外发光

    # 3. 底部显示AI文字（黑色背景条）
    pygame.draw.rect(screen, (0, 0, 0, 128), (0, HEIGHT - 80, WIDTH, 80))
    # 显示当前行内容
    text_surface = font.render(ai_text, True, (200, 220, 255))
    screen.blit(text_surface, (20, HEIGHT - 50))
    # 显示行号提示
    if ai_lines:
        page_info = f"{scroll_index + 1}/{len(ai_lines)}"
        info_surface = font.render(page_info, True, (150, 150, 180))
        screen.blit(info_surface, (WIDTH - 80, HEIGHT - 50))
    # 操作提示
    # 左上角：移动和呼叫AI
    tip_move = font.render("方向键移动 | SPACE呼叫AI", True, (100, 120, 150))
    screen.blit(tip_move, (20, 15))

    # 右上角：翻页提示
    tip_page = font.render("↑↓ 翻页", True, (100, 120, 150))
    screen.blit(tip_page, (WIDTH - 120, 15))
    screen.blit(text_surface, (20, HEIGHT - 50))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
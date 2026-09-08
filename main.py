import pygame
import sys
import requests
import json

# ---------- 初始化 ----------
pygame.init()
CELL_SIZE = 70  # 每格像素
# 地图尺寸：8列 x 5行
MAP_COLS = 8
MAP_ROWS = 5
WIDTH = MAP_COLS * CELL_SIZE
HEIGHT = MAP_ROWS * CELL_SIZE + 80  # 底部留80像素显示AI文字
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("代码之核 - 内存迷宫")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 30)

# ---------- 地图数据 (0=空地, 1=墙壁) ----------
map_data = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1]
]

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
            return response.json().get("response", "模型未返回内容")
        else:
            return f"本地API报错: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "错误：请确认Ollama正在运行"
    except Exception as e:
        return f"错误: {str(e)}"

# ---------- 游戏主循环 ----------
running = True
ai_text = "按 [空格键] 呼叫核心叙事者"

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
                reply =ask_local_model ("我站在数字迷宫的中央，四周是冰冷的代码墙壁。请用一句话描述此刻的氛围，并给我一句鼓励。")
                ai_text = reply
                print("AI回应:", reply)

    # --- 绘制画面 ---
    screen.fill((10, 10, 30))  # 深空底色

    # 1. 绘制地图
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            if map_data[row][col] == 1:
                # 墙壁（暗紫色）
                pygame.draw.rect(screen, (60, 50, 90), (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, (120, 100, 180), (x, y, CELL_SIZE, CELL_SIZE), 2)
            else:
                # 空地（隐约的网格线）
                pygame.draw.rect(screen, (30, 30, 50), (x, y, CELL_SIZE, CELL_SIZE), 1)

    # 2. 绘制玩家（发光圆球）
    center_x = player_x * CELL_SIZE + CELL_SIZE // 2
    center_y = player_y * CELL_SIZE + CELL_SIZE // 2
    pygame.draw.circle(screen, (0, 255, 200), (center_x, center_y), 20)  # 青色
    pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), 20, 2)  # 外发光

    # 3. 底部显示AI文字（黑色背景条）
    pygame.draw.rect(screen, (0, 0, 0, 128), (0, HEIGHT - 80, WIDTH, 80))
    text_surface = font.render(ai_text, True, (200, 220, 255))
    screen.blit(text_surface, (20, HEIGHT - 50))

    # 4. 操作提示
    tip = font.render("方向键移动 | SPACE 呼叫AI", True, (100, 120, 150))
    screen.blit(tip, (20, 15))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
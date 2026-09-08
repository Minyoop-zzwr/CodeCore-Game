# 🧩 CodeCore-Game

一个基于 Pygame 的迷宫探索游戏，通过本地部署的 DeepSeek-R1 模型驱动实时叙事对话。

---

## 🎮 当前功能 (v0.1)

- 🎯 键盘方向键控制角色在迷宫中移动
- 🧱 墙壁碰撞检测
- 💬 按 空格键 触发 AI 生成当前场景的描述与鼓励
- 🤖 完全本地运行，无需联网，无需 API Key（基于 Ollama + DeepSeek-R1 1.5B）

---

## 🛠️ 技术栈

- 游戏引擎：Pygame 2.6.1
- AI 推理：Ollama + DeepSeek-R1 1.5B (GGUF)
- 语言：Python 3.13
- 通信：HTTP API (本地)

---

## 🚀 如何运行

**前提条件**：安装 Python 3.13+ 和 Ollama（https://ollama.com）

**步骤1：克隆仓库**  
git clone https://github.com/Minyoop-zzwr/CodeCore-Game.git  
cd CodeCore-Game

**步骤2：安装 Python 依赖**  
pip install pygame requests

**步骤3：下载并运行 AI 模型（首次运行，约1.1GB，只需一次）**  
ollama run deepseek-r1:1.5b

**步骤4：启动游戏**  
python main.py

**游戏操作**：方向键移动，空格键触发 AI 对话

---

## 📌 为何采用本地 AI 部署？

最初版本依赖云端 API，但为了完全免费、隐私保护、离线可用，以及展示工程化落地能力，我切换到了本地 Ollama + DeepSeek-R1 1.5B 方案，并持续在 GitHub 上迭代。

---

## 🔜 下一步计划

- 增加决策日志面板，显示 AI 的每次建议与置信度
- 设计多层级地图（三个不同关卡）
- 添加音效和简单背景音乐
- 打包成 Windows 可执行文件（exe）

---

## 📄 许可

本项目仅供学习和展示用途。

---

## 🙏 致谢

Pygame 社区、Ollama 团队、DeepSeek 开源模型

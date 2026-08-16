from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
FRAMES_DIR = ASSETS_DIR / "frames"
SOUNDS_DIR = ASSETS_DIR / "sounds"
PET_SRC = ASSETS_DIR / "pet.png"

DESKTOP_PATH = Path.home() / "Desktop"

PET_HEIGHT = 200              # 角色缩放高度（px）
SNAPSHOT_INTERVAL_MS = 1000   # 图标快照周期
ANIMATION_FPS = 60            # 动画帧率

MOVE_DURATION_MS = 800        # 移动到图标时长
THROW_DURATION_MS = 500       # 扔垃圾桶时长
KICK_DURATION_MS = 500        # 踢飞时长

ICON_SIZE = 32                # 提取图标像素尺寸

import math
import os
from PIL import Image


def _load_and_prepare(src_path: str, height: int) -> Image.Image:
    img = Image.open(src_path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    new_w = max(1, int(w * height / h))
    return img.resize((new_w, height), Image.LANCZOS)


def _shear(img: Image.Image, shear: float) -> Image.Image:
    """水平错切：顶部(y=0)不动，底部偏移 shear*h，模拟钟摆摆动。"""
    w, h = img.size
    return img.transform((w, h), Image.AFFINE, (1, shear, 0, 0, 1, 0),
                         resample=Image.BICUBIC)


def generate_frames(src_path: str, out_dir: str, height: int = 100,
                    leg_ratio: float = 0.65, swing: int = 3,
                    idle_frames: int = 8) -> list[str]:
    base = _load_and_prepare(src_path, height)
    w, h = base.size
    leg_top = int(h * leg_ratio)
    body = base.crop((0, 0, w, leg_top))
    legs = base.crop((0, leg_top, w, h))
    leg_h = h - leg_top

    CW = w + 4
    CH = h + 8
    os.makedirs(out_dir, exist_ok=True)
    paths = []

    # idle：身体静止 + 腿部钟摆式错切摆动（正弦波采样，平滑循环）
    for i in range(idle_frames):
        phase = 2 * math.pi * i / idle_frames
        s = swing * math.sin(phase)
        shear = s / leg_h
        sheared = _shear(legs, shear)
        frame = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        frame.paste(body, (2, 4), body)
        frame.paste(sheared, (2, 4 + leg_top), sheared)
        p = os.path.join(out_dir, f"idle_{i+1:02d}.png")
        frame.save(p)
        paths.append(p)

    # move：整体漂浮（平移 + 上下浮动）
    for i, (dx, dy) in enumerate([(0, 4), (1, 1), (0, 0), (-1, 1)]):
        frame = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        frame.paste(base, (2 + dx, dy), base)
        p = os.path.join(out_dir, f"move_{i+1:02d}.png")
        frame.save(p)
        paths.append(p)

    # act：下压 + 上挑（配合图标飞行动画）
    for i, dy in enumerate([6, 0]):
        frame = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        frame.paste(base, (2, dy), base)
        p = os.path.join(out_dir, f"act_{i+1:02d}.png")
        frame.save(p)
        paths.append(p)

    return paths

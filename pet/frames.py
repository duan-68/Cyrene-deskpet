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


def generate_frames(src_path: str, out_dir: str, height: int = 100,
                    leg_ratio: float = 0.65) -> list[str]:
    base = _load_and_prepare(src_path, height)
    w, h = base.size
    leg_top = int(h * leg_ratio)
    body = base.crop((0, 0, w, leg_top))
    legs = base.crop((0, leg_top, w, h))

    CW = w + 4
    CH = h + 8
    os.makedirs(out_dir, exist_ok=True)
    paths = []

    # idle：身体静止 + 腿部左右摆动（模拟晃脚）
    for i, dx in enumerate([0, 2, 0, -2]):
        frame = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        frame.paste(body, (2, 4), body)
        frame.paste(legs, (2 + dx, 4 + leg_top), legs)
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

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


def _place(base: Image.Image, dx: int, dy: int) -> Image.Image:
    canvas = Image.new("RGBA", base.size, (0, 0, 0, 0))
    canvas.paste(base, (dx, dy), base)
    return canvas


def generate_frames(src_path: str, out_dir: str, height: int = 200) -> list[str]:
    base = _load_and_prepare(src_path, height)
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    # idle：轻微上下浮动 + 左右摇摆（模拟晃脚）
    for i, (dx, dy) in enumerate([(0, 0), (1, -2), (0, -3), (-1, -2)]):
        p = os.path.join(out_dir, f"idle_{i+1:02d}.png")
        _place(base, dx, dy).save(p)
        paths.append(p)
    # move：漂浮移动，浮动幅度更大
    for i, (dx, dy) in enumerate([(0, 0), (2, -4), (0, -6), (-2, -4)]):
        p = os.path.join(out_dir, f"move_{i+1:02d}.png")
        _place(base, dx, dy).save(p)
        paths.append(p)
    # act：下压 + 上挑（配合图标飞行动画）
    p1 = os.path.join(out_dir, "act_01.png")
    _place(base, 0, 3).save(p1)
    p2 = os.path.join(out_dir, "act_02.png")
    _place(base, 0, -4).save(p2)
    paths += [p1, p2]
    return paths

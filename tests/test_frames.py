import os
from PIL import Image
from pet.config import PET_SRC
from pet.frames import generate_frames


def test_generate_frames_produces_expected_set(tmp_path):
    out = tmp_path / "frames"
    paths = generate_frames(str(PET_SRC), str(out))
    names = sorted(os.path.basename(p) for p in paths)
    assert names == sorted(
        ["idle_01.png", "idle_02.png", "idle_03.png", "idle_04.png",
         "move_01.png", "move_02.png", "move_03.png", "move_04.png",
         "act_01.png", "act_02.png"])


def test_generated_frame_is_sized(tmp_path):
    out = tmp_path / "frames"
    paths = generate_frames(str(PET_SRC), str(out))
    img = Image.open(paths[0])
    assert img.mode == "RGBA"
    w, h = img.size
    assert h == 200 and w > 0


def test_generated_frame_has_transparency(tmp_path):
    out = tmp_path / "frames"
    paths = generate_frames(str(PET_SRC), str(out))
    img = Image.open(paths[0])
    alpha = list(img.getdata(3))
    assert any(a == 0 for a in alpha)

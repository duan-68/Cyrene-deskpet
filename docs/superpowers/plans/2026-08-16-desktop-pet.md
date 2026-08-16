# 桌宠小插件实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Windows 桌宠应用：监控桌面 `.lnk` 删除，桌宠（Q版昔涟坐弓）漂浮到图标位置，先扔垃圾桶再踢飞，图标随动作自然消失，含音效与托盘，打包成 exe。

**Architecture:** 单进程 PySide6 应用，五个核心模块（图标快照 / 文件监控 / 动作调度 / 桌宠窗口 / 音效+托盘）通过主入口组装。图标外观用「快照缓存 + 删除瞬间顶替」实现自然消失。

**Tech Stack:** Python 3.12、PySide6-Essentials 6.11.1、watchdog 6.0.0、Pillow 12.1.1、ctypes（标准库）、winsound（标准库）、pytest、PyInstaller。

**Spec:** `docs/superpowers/specs/2026-08-16-desktop-pet-design.md`

## Global Constraints

- Python 3.12，仅 Windows。
- GUI 依赖只用 PySide6-Essentials（不含 Addons）；音效用 winsound 播 `.wav`。
- 桌面图标位置用 ctypes 调 Win32（`LVM_GETITEMPOSITION`），不依赖 pywin32/comtypes。
- 图标外观用 PySide6 `QFileIconProvider` 提取，不依赖 pywin32。
- 角色素材用已抠好的 `pet.png`（1200×675，透明背景）。
- 音效文件缺失时静默跳过，不报错、不阻塞。
- 所有文件写入仅在工作区 `E:\code\dsh\desktop-pet\` 内；pip/PyInstaller 等需要写 Python site-packages 的操作须通过 `sandbox_permissions=danger-full-access` 升级执行。

## 文件结构

```
E:\code\dsh\desktop-pet\
├── pet\
│   ├── __init__.py
│   ├── config.py          # 常量：路径、尺寸、动画时长
│   ├── frames.py          # 帧生成（Pillow 缩放/裁剪/抖动/摇摆）
│   ├── file_watcher.py    # 桌面删除监控（watchdog）
│   ├── icon_snapshot.py   # 图标坐标+外观快照（ctypes + QFileIconProvider）
│   ├── dispatcher.py      # 删除事件 → 动画序列调度 + 队列
│   ├── audio.py           # 音效（winsound）
│   ├── pet_window.py      # 透明置顶窗口 + 动画状态机
│   ├── tray.py            # 系统托盘
│   └── main.py            # 入口：组装 + 事件循环
├── assets\
│   ├── pet.png            # 抠好的角色图（从 E:\code\dsh\pet.png 复制）
│   ├── frames\            # 生成的帧（idle_01.., move_01.., act_01..）
│   └── sounds\            # move.wav / throw.wav / kick.wav（可后补）
├── tests\
│   ├── test_frames.py
│   ├── test_file_watcher.py
│   ├── test_dispatcher.py
│   └── test_icon_snapshot.py
└── requirements.txt
```

---

### Task 1: 项目脚手架 + 帧生成器

**Files:**
- Create: `desktop-pet/requirements.txt`
- Create: `desktop-pet/pet/__init__.py`
- Create: `desktop-pet/pet/config.py`
- Create: `desktop-pet/pet/frames.py`
- Create: `desktop-pet/tests/test_frames.py`
- Create: `desktop-pet/assets/`（放 `pet.png`）

**Interfaces:**
- Produces: `frames.generate_frames(src_path: str, out_dir: str, height: int = 200) -> list[str]`，返回生成帧的路径列表；`config` 模块常量（见下）。

- [ ] **Step 1: 初始化 git 仓库并建目录**

```bash
cd E:\code\dsh && git init
New-Item -ItemType Directory -Force desktop-pet\pet, desktop-pet\tests, desktop-pet\assets\frames, desktop-pet\assets\sounds
Copy-Item E:\code\dsh\pet.png desktop-pet\assets\pet.png
```

- [ ] **Step 2: 写 requirements.txt**

```
PySide6-Essentials==6.11.1
watchdog==6.0.0
Pillow==12.1.1
pytest
```

- [ ] **Step 3: 写 config.py**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
FRAMES_DIR = ASSETS_DIR / "frames"
SOUNDS_DIR = ASSETS_DIR / "sounds"
PET_SRC = ASSETS_DIR / "pet.png"

DESKTOP_PATH = Path.home() / "Desktop"

PET_HEIGHT = 200          # 角色缩放高度（px）
SNAPSHOT_INTERVAL_MS = 1000   # 图标快照周期
ANIMATION_FPS = 60        # 动画帧率

MOVE_DURATION_MS = 800    # 移动到图标时长
THROW_DURATION_MS = 500   # 扔垃圾桶时长
KICK_DURATION_MS = 500    # 踢飞时长

ICON_SIZE = 32            # 提取图标像素尺寸
```

- [ ] **Step 4: 写失败测试 test_frames.py**

```python
import os
from PIL import Image
from pet.frames import generate_frames

def test_generate_frames_produces_expected_set(tmp_path):
    out = tmp_path / "frames"
    paths = generate_frames("pet.png", str(out))  # 用仓库根目录 pet.png
    names = sorted(os.path.basename(p) for p in paths)
    assert names == sorted(
        ["idle_01.png", "idle_02.png", "idle_03.png", "idle_04.png",
         "move_01.png", "move_02.png", "move_03.png", "move_04.png",
         "act_01.png", "act_02.png"]
    )

def test_generated_frame_is_transparent_and_sized(tmp_path):
    out = tmp_path / "frames"
    paths = generate_frames("pet.png", str(out))
    img = Image.open(paths[0])
    assert img.mode == "RGBA"
    w, h = img.size
    assert h == 200 and w > 0
    # 四角应为透明
    assert img.getpixel((0, 0))[3] == 0
```

- [ ] **Step 5: 运行测试确认失败**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_frames.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'pet.frames'`）

- [ ] **Step 6: 写 frames.py 最小实现**

```python
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
```

- [ ] **Step 7: 运行测试确认通过**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_frames.py -v`
Expected: PASS（2 passed）。注意测试从 `desktop-pet` 目录运行，`pet.png` 路径为仓库根 `E:\code\dsh\pet.png`，测试里用绝对路径或 `sys.path` 调整；若 `pet.png` 不在 cwd，改为 `os.path.join(os.path.dirname(__file__), "..", "..", "pet.png")`。

- [ ] **Step 8: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/requirements.txt desktop-pet/pet/__init__.py desktop-pet/pet/config.py desktop-pet/pet/frames.py desktop-pet/tests/test_frames.py
git commit -m "feat: 脚手架与角色帧生成器"
```

---

### Task 2: 文件监控模块

**Files:**
- Create: `desktop-pet/pet/file_watcher.py`
- Create: `desktop-pet/tests/test_file_watcher.py`

**Interfaces:**
- Produces: `file_watcher.is_recycle_bin(path: str) -> bool`；`file_watcher.DesktopDeleteHandler(on_delete: Callable[[str, str], None])`；`file_watcher.FileWatcher(directory: Path, on_delete).start()/.stop()`

- [ ] **Step 1: 写失败测试 test_file_watcher.py**

```python
import os
from pathlib import Path
from pet.file_watcher import DesktopDeleteHandler, is_recycle_bin

class _Event:
    def __init__(self, src, dest=None, is_dir=False):
        self.src_path = src
        self.dest_path = dest or ""
        self.is_directory = is_dir

def test_is_recycle_bin():
    assert is_recycle_bin("C:\\$Recycle.Bin\\S-1-5-18\\x.lnk")
    assert not is_recycle_bin("C:\\Users\\a\\Desktop\\x.lnk")

def test_handler_fires_on_deleted_lnk():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_deleted(_Event("C:\\Users\\a\\Desktop\\foo.lnk"))
    assert seen == [("foo.lnk", "deleted")]

def test_handler_ignores_non_lnk_and_directory():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_deleted(_Event("C:\\Users\\a\\Desktop\\a.txt"))
    h.on_deleted(_Event("C:\\Users\\a\\Desktop\\x.lnk", is_dir=True))
    assert seen == []

def test_handler_fires_on_moved_to_recycle_bin():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_moved(_Event("C:\\Users\\a\\Desktop\\foo.lnk",
                      "C:\\$Recycle.Bin\\S-1-5-18\\foo.lnk"))
    assert seen == [("foo.lnk", "moved")]

def test_handler_ignores_moved_not_to_recycle():
    seen = []
    h = DesktopDeleteHandler(lambda f, m: seen.append((f, m)))
    h.on_moved(_Event("C:\\Users\\a\\Desktop\\foo.lnk",
                      "C:\\Users\\a\\Desktop\\foo2.lnk"))
    assert seen == []
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_file_watcher.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 写 file_watcher.py 最小实现**

```python
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def is_recycle_bin(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return "$Recycle.Bin" in parts


class DesktopDeleteHandler(FileSystemEventHandler):
    def __init__(self, on_delete):
        self._on_delete = on_delete

    def _handle(self, src_path, mode):
        if src_path.lower().endswith(".lnk"):
            self._on_delete(os.path.basename(src_path), mode)

    def on_deleted(self, event):
        if not event.is_directory:
            self._handle(event.src_path, "deleted")

    def on_moved(self, event):
        if not event.is_directory and is_recycle_bin(event.dest_path):
            self._handle(event.src_path, "moved")


class FileWatcher:
    def __init__(self, directory: Path, on_delete):
        self._observer = Observer()
        self._observer.schedule(
            DesktopDeleteHandler(on_delete), str(directory), recursive=False)

    def start(self):
        self._observer.start()

    def stop(self):
        self._observer.stop()
        self._observer.join(timeout=5)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_file_watcher.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/pet/file_watcher.py desktop-pet/tests/test_file_watcher.py
git commit -m "feat: 桌面删除事件监控"
```

---

### Task 3: 动作调度模块

**Files:**
- Create: `desktop-pet/pet/dispatcher.py`
- Create: `desktop-pet/tests/test_dispatcher.py`

**Interfaces:**
- Consumes: `IconInfo`（含 `filename`/`x`/`y`/`icon` 字段）；`snapshot.get(filename) -> IconInfo | None`；`window.play_sequence(icon_info, on_done)`。
- Produces: `dispatcher.Dispatcher(snapshot, window, audio, max_queue=10)`，方法 `.on_delete(filename, mode)`、`.stop()`。

- [ ] **Step 1: 写失败测试 test_dispatcher.py**

```python
from pet.dispatcher import Dispatcher

class _Snapshot:
    def __init__(self, data):
        self.data = data
    def get(self, name):
        return self.data.get(name)

class _Window:
    def __init__(self):
        self.calls = []
    def play_sequence(self, info, on_done):
        self.calls.append(info.filename)
        self.on_done = on_done

class _Audio:
    def play(self, name):
        pass

class _Info:
    def __init__(self, name):
        self.filename = name
        self.x = 10
        self.y = 20
        self.icon = "ICON"

def test_on_delete_dispatches_sequence():
    info = _Info("foo.lnk")
    snap = _Snapshot({"foo.lnk": info})
    win = _Window()
    d = Dispatcher(snap, win, _Audio())
    d.on_delete("foo.lnk", "deleted")
    assert win.calls == ["foo.lnk"]

def test_on_delete_unknown_icon_skips():
    snap = _Snapshot({})
    win = _Window()
    d = Dispatcher(snap, win, _Audio())
    d.on_delete("missing.lnk", "deleted")
    assert win.calls == []

def test_queue_serializes_and_advances():
    i1, i2 = _Info("a.lnk"), _Info("b.lnk")
    snap = _Snapshot({"a.lnk": i1, "b.lnk": i2})
    win = _Window()
    d = Dispatcher(snap, win, _Audio())
    d.on_delete("a.lnk", "deleted")
    d.on_delete("b.lnk", "deleted")
    # 第一个立即播放，第二个排队
    assert win.calls == ["a.lnk"]
    win.on_done()  # 第一个完成
    assert win.calls == ["a.lnk", "b.lnk"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_dispatcher.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 写 dispatcher.py 最小实现**

```python
from collections import deque
from dataclasses import dataclass


@dataclass
class ActionRequest:
    filename: str
    icon_info: object


class Dispatcher:
    def __init__(self, snapshot, window, audio, max_queue=10):
        self._snapshot = snapshot
        self._window = window
        self._audio = audio
        self._queue = deque(maxlen=max_queue)
        self._current = None
        self._running = True

    def on_delete(self, filename, mode):
        if not self._running:
            return
        info = self._snapshot.get(filename)
        if info is None:
            return
        self._queue.append(ActionRequest(filename, info))
        self._maybe_start_next()

    def _maybe_start_next(self):
        if self._current is not None or not self._queue:
            return
        self._current = self._queue.popleft()
        self._window.play_sequence(self._current.icon_info, self._on_done)

    def _on_done(self):
        self._current = None
        self._maybe_start_next()

    def stop(self):
        self._running = False
        self._queue.clear()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_dispatcher.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/pet/dispatcher.py desktop-pet/tests/test_dispatcher.py
git commit -m "feat: 删除事件动作调度与队列"
```

---

### Task 4: 音效 + 托盘模块

**Files:**
- Create: `desktop-pet/pet/audio.py`
- Create: `desktop-pet/pet/tray.py`

**Interfaces:**
- Produces: `audio.Audio(sounds_dir, enabled=True)`，方法 `.play(name)`、属性 `.enabled`（可读写）。
- Produces: `tray.Tray(app, on_quit, on_toggle_pause, on_toggle_audio)`，方法 `.set_paused(paused)`、`.set_audio(enabled)`、`.notify(msg)`。

- [ ] **Step 1: 写 audio.py**

```python
import winsound
from pathlib import Path


class Audio:
    def __init__(self, sounds_dir, enabled=True):
        self._dir = Path(sounds_dir)
        self._enabled = enabled

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    def play(self, name):
        if not self._enabled:
            return
        path = self._dir / f"{name}.wav"
        if path.exists():
            winsound.PlaySound(
                str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
```

- [ ] **Step 2: 写 tray.py**

```python
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction


class Tray:
    def __init__(self, app, icon_path, on_quit, on_toggle_pause, on_toggle_audio):
        self._tray = QSystemTrayIcon(QIcon(str(icon_path)), app)
        menu = QMenu()

        self._pause_action = QAction("暂停监控", menu)
        self._pause_action.setCheckable(True)
        self._pause_action.triggered.connect(
            lambda checked: on_toggle_pause(checked))
        menu.addAction(self._pause_action)

        self._audio_action = QAction("音效", menu)
        self._audio_action.setCheckable(True)
        self._audio_action.setChecked(True)
        self._audio_action.triggered.connect(
            lambda checked: on_toggle_audio(checked))
        menu.addAction(self._audio_action)

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(on_quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.setToolTip("桌宠")
        self._tray.show()

    def set_paused(self, paused):
        self._pause_action.setChecked(paused)

    def set_audio(self, enabled):
        self._audio_action.setChecked(enabled)

    def notify(self, msg):
        self._tray.showMessage("桌宠", msg)
```

- [ ] **Step 3: 手动验证（无 GUI 环境可跳过自动化）**

Run: `cd E:\code\dsh\desktop-pet && python -c "from pet.audio import Audio; a=Audio('assets/sounds', enabled=False); print('audio ok')"`
Expected: 输出 `audio ok`（winsound 不发声因 enabled=False）。tray.py 需 GUI 环境，在 Task 7 端到端时一并验证。

- [ ] **Step 4: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/pet/audio.py desktop-pet/pet/tray.py
git commit -m "feat: 音效与系统托盘"
```

---

### Task 5: 图标快照模块（ctypes + QFileIconProvider）

**Files:**
- Create: `desktop-pet/pet/icon_snapshot.py`
- Create: `desktop-pet/tests/test_icon_snapshot.py`

**Interfaces:**
- Produces: `icon_snapshot.IconInfo`（dataclass：`filename`/`x`/`y`/`icon`）；`icon_snapshot.find_desktop_listview() -> int`；`icon_snapshot.enum_icon_positions(hwnd) -> list[tuple[str,int,int]]`；`icon_snapshot.IconSnapshot(desktop_path)`，方法 `.refresh()`、`.get(filename) -> IconInfo | None`。

- [ ] **Step 1: 写可测试部分的失败测试 test_icon_snapshot.py**

```python
from pet.icon_snapshot import IconSnapshot

def test_snapshot_returns_none_when_missing():
    s = IconSnapshot.__new__(IconSnapshot)  # 不跑构造，直接测 get
    s._snapshot = {}
    assert s.get("x.lnk") is None

def test_snapshot_returns_cached_info():
    s = IconSnapshot.__new__(IconSnapshot)
    class I:
        filename = "x.lnk"; x = 1; y = 2; icon = "I"
    s._snapshot = {"x.lnk": I()}
    got = s.get("x.lnk")
    assert got.x == 1 and got.y == 2
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_icon_snapshot.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 写 icon_snapshot.py**

```python
import ctypes
import ctypes.wintypes as wt
from dataclasses import dataclass
from pathlib import Path

LVM_FIRST = 0x1000
LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_GETITEMPOSITION = LVM_FIRST + 16
LVM_GETITEMTEXTW = LVM_FIRST + 115
LVIF_TEXT = 0x0001

user32 = ctypes.windll.user32


@dataclass
class IconInfo:
    filename: str
    x: int
    y: int
    icon: object


class _LVITEMW(ctypes.Structure):
    _fields_ = [
        ("mask", wt.UINT), ("iItem", ctypes.c_int), ("iSubItem", ctypes.c_int),
        ("state", wt.UINT), ("stateMask", wt.UINT), ("pszText", wt.LPWSTR),
        ("cchTextMax", ctypes.c_int), ("iImage", ctypes.c_int),
        ("lParam", wt.LPARAM), ("iIndent", ctypes.c_int),
        ("iGroupId", ctypes.c_int), ("cColumns", wt.UINT),
        ("puColumns", wt.PUINT), ("piColFmt", ctypes.POINTER(ctypes.c_int)),
        ("iGroup", ctypes.c_int),
    ]


def find_desktop_listview() -> int:
    progman = user32.FindWindowW("Progman", None)
    defview = user32.FindWindowExW(progman, 0, "SHELLDLL_DefView", None)
    if defview:
        lv = user32.FindWindowExW(defview, 0, "SysListView32", None)
        if lv:
            return lv
    workerw = None
    while True:
        workerw = user32.FindWindowExW(None, workerw, "WorkerW", None)
        if not workerw:
            break
        lv = user32.FindWindowExW(workerw, 0, "SysListView32", None)
        if lv:
            return lv
    return 0


def enum_icon_positions(hwnd: int) -> list[tuple[str, int, int]]:
    count = user32.SendMessageW(hwnd, LVM_GETITEMCOUNT, 0, 0)
    out = []
    for i in range(count):
        pt = wt.POINT()
        user32.SendMessageW(hwnd, LVM_GETITEMPOSITION, i, ctypes.byref(pt))
        buf = ctypes.create_unicode_buffer(260)
        lvi = _LVITEMW()
        lvi.mask = LVIF_TEXT
        lvi.iSubItem = 0
        lvi.pszText = ctypes.cast(buf, wt.LPWSTR)
        lvi.cchTextMax = 260
        user32.SendMessageW(hwnd, LVM_GETITEMTEXTW, i, ctypes.byref(lvi))
        out.append((buf.value, pt.x, pt.y))
    return out


class IconSnapshot:
    def __init__(self, desktop_path: Path):
        self._desktop = Path(desktop_path)
        self._snapshot: dict[str, IconInfo] = {}
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            from PySide6.QtWidgets import QFileIconProvider
            self._provider = QFileIconProvider()
        return self._provider

    def refresh(self):
        hwnd = find_desktop_listview()
        if not hwnd:
            return
        for name, x, y in enum_icon_positions(hwnd):
            if not name.lower().endswith(".lnk"):
                continue
            lnk = self._desktop / name
            if not lnk.exists():
                continue
            icon = self._get_provider().icon(
                __import__("PySide6.QtCore", fromlist=["QFileInfo"])
                .QFileInfo(str(lnk)))
            self._snapshot[name] = IconInfo(name, x, y, icon)

    def get(self, filename: str) -> IconInfo | None:
        return self._snapshot.get(filename)
```

> 注意：`IconInfo.x/y` 为 ListView 客户区坐标，后续在 `pet_window` 中用 `ClientToScreen` 换算为屏幕坐标。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd E:\code\dsh\desktop-pet && python -m pytest tests/test_icon_snapshot.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 手动验证真实枚举**

Run: `cd E:\code\dsh\desktop-pet && python -c "from pet.icon_snapshot import find_desktop_listview, enum_icon_positions; h=find_desktop_listview(); print('hwnd', h); print(enum_icon_positions(h) if h else 'none')"`
Expected: 打印 `hwnd <非0>` 与桌面图标列表（含文件名与坐标）。若 hwnd=0，按 Step 3 中 `find_desktop_listview` 的 Progman→WorkerW 逻辑排查，或改用 `EnumWindows` 遍历顶层窗口收集所有 `SysListView32` 子窗口。

- [ ] **Step 6: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/pet/icon_snapshot.py desktop-pet/tests/test_icon_snapshot.py
git commit -m "feat: 桌面图标坐标与外观快照"
```

---

### Task 6: 桌宠窗口（透明置顶 + 动画状态机）

**Files:**
- Create: `desktop-pet/pet/pet_window.py`

**Interfaces:**
- Consumes: `config` 常量、`frames` 生成的帧文件、`audio.Audio.play`。
- Produces: `pet_window.PetWindow(frames_dir, audio)`，方法 `.play_sequence(icon_info, on_done)`、`.set_paused(paused)`、`.show_pet()`。

- [ ] **Step 1: 写 pet_window.py（含动画状态机）**

```python
import time
import math
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QTimer, QRect
from PySide6.QtGui import QPainter, QPixmap, QTransform
from PySide6.QtWidgets import QWidget, QApplication

from . import config


def _load_frames(d, prefix, count):
    out = []
    for i in range(1, count + 1):
        p = Path(d) / f"{prefix}_{i:02d}.png"
        if p.exists():
            out.append(QPixmap(str(p)))
    return out


class PetWindow(QWidget):
    def __init__(self, frames_dir, audio):
        super().__init__()
        self._audio = audio
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        screen = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screen)

        self._idle = _load_frames(frames_dir, "idle", 4) or [QPixmap()]
        self._move = _load_frames(frames_dir, "move", 4) or self._idle
        self._act = _load_frames(frames_dir, "act", 2) or self._idle

        self._paused = False
        self._pet_pos = QPoint(screen.width() // 2, screen.height() - 250)
        self._frames = self._idle
        self._frame_idx = 0

        # 序列状态
        self._stage = "idle"          # idle/moving/throwing/kicking
        self._stage_start = 0.0
        self._seq_icon = None
        self._icon_pm = None
        self._icon_pos = None
        self._on_done = None
        self._start_pos = None
        self._target_pos = None
        self._trash_pos = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // config.ANIMATION_FPS)
        self._t0 = time.monotonic()

    def show_pet(self):
        self.show()

    def set_paused(self, paused):
        self._paused = paused

    def play_sequence(self, icon_info, on_done):
        self._seq_icon = icon_info
        self._on_done = on_done
        # 图标顶替在原坐标（先换算为窗口坐标）
        self._icon_pm = icon_info.icon.pixmap(config.ICON_SIZE, config.ICON_SIZE)
        self._icon_pos = self._to_window(icon_info.x, icon_info.y)
        # 角色目标：图标左侧
        self._start_pos = QPoint(self._pet_pos)
        self._target_pos = QPoint(
            self._icon_pos.x() - 80, self._icon_pos.y() - 60)
        self._trash_pos = self._find_trash_pos()
        self._stage = "moving"
        self._stage_start = time.monotonic()
        self._frames = self._move

    def _to_window(self, x, y):
        # ListView 客户区坐标 → 屏幕 → 窗口（虚拟屏幕）坐标
        return QPoint(x + self.geometry().x(), y + self.geometry().y())

    def _find_trash_pos(self):
        # 简化：回收站默认在桌面左上角，用屏幕左上角附近；找不到则用右下角
        return QPoint(60, 60)

    def _tick(self):
        self._frame_idx += 1
        now = time.monotonic()
        if self._stage == "moving":
            self._advance_moving(now)
        elif self._stage == "throwing":
            self._advance_throwing(now)
        elif self._stage == "kicking":
            self._advance_kicking(now)
        self.update()

    def _progress(self, now, duration):
        return min(1.0, (now - self._stage_start) * 1000 / duration)

    def _advance_moving(self, now):
        t = self._progress(now, config.MOVE_DURATION_MS)
        e = t * t * (3 - 2 * t)  # smoothstep
        self._pet_pos = QPoint(
            round(self._start_pos.x() + (self._target_pos.x() - self._start_pos.x()) * e),
            round(self._start_pos.y() + (self._target_pos.y() - self._start_pos.y()) * e))
        if t >= 1.0:
            self._audio.play("move")
            self._stage = "throwing"
            self._stage_start = now
            self._frames = self._act

    def _advance_throwing(self, now):
        t = self._progress(now, config.THROW_DURATION_MS)
        # 图标沿抛物线飞向回收站，缩小 + 淡出
        sx, sy = self._icon_pos.x(), self._icon_pos.y()
        tx, ty = self._trash_pos.x(), self._trash_pos.y()
        cx = sx + (tx - sx) * t
        cy = sy + (ty - sy) * t - math.sin(t * math.pi) * 120
        self._icon_pos = QPoint(round(cx), round(cy))
        self._icon_scale = 1.0 - 0.6 * t
        self._icon_opacity = 1.0 - t
        if t >= 1.0:
            self._audio.play("throw")
            self._stage = "kicking"
            self._stage_start = now

    def _advance_kicking(self, now):
        t = self._progress(now, config.KICK_DURATION_MS)
        # 垃圾桶（用图标残留表示）沿弧线飞出屏幕
        vx = self.geometry().width() + 200
        vy = self._trash_pos.y() - 400 * t
        self._icon_pos = QPoint(round(self._trash_pos.x() + vx * t), round(vy))
        self._icon_opacity = 1.0 - t
        if t >= 1.0:
            self._audio.play("kick")
            self._finish()

    def _finish(self):
        self._stage = "idle"
        self._frames = self._idle
        self._seq_icon = None
        self._icon_pm = None
        cb = self._on_done
        self._on_done = None
        if cb:
            cb()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # 角色
        pm = self._frames[self._frame_idx % len(self._frames)]
        painter.drawPixmap(self._pet_pos, pm)
        # 图标（顶替/飞行）
        if self._icon_pm and self._icon_pos:
            painter.setOpacity(getattr(self, "_icon_opacity", 1.0))
            scale = getattr(self, "_icon_scale", 1.0)
            w = round(self._icon_pm.width() * scale)
            h = round(self._icon_pm.height() * scale)
            painter.drawPixmap(
                QRect(self._icon_pos.x(), self._icon_pos.y(), w, h),
                self._icon_pm)
            painter.setOpacity(1.0)
```

- [ ] **Step 2: 手动验证窗口显示**

Run: 临时脚本（见 Step 3）先只显示窗口 + 待机帧动画，确认透明置顶、角色可见、可被 Esc 关闭。

- [ ] **Step 3: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/pet/pet_window.py
git commit -m "feat: 透明置顶桌宠窗口与动画状态机"
```

---

### Task 7: 入口组装 + 端到端联调

**Files:**
- Create: `desktop-pet/pet/main.py`

**Interfaces:**
- Consumes: 所有模块。
- Produces: 可运行入口 `python -m pet.main`。

- [ ] **Step 1: 写 main.py**

```python
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from . import config
from .audio import Audio
from .dispatcher import Dispatcher
from .file_watcher import FileWatcher
from .icon_snapshot import IconSnapshot
from .pet_window import PetWindow
from .tray import Tray


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    audio = Audio(config.SOUNDS_DIR, enabled=True)
    window = PetWindow(config.FRAMES_DIR, audio)
    snapshot = IconSnapshot(config.DESKTOP_PATH)
    dispatcher = Dispatcher(snapshot, window, audio)

    watcher = FileWatcher(config.DESKTOP_PATH, dispatcher.on_delete)

    # 快照定时刷新
    from PySide6.QtCore import QTimer
    snap_timer = QTimer()
    snap_timer.timeout.connect(snapshot.refresh)
    snap_timer.start(config.SNAPSHOT_INTERVAL_MS)
    snapshot.refresh()

    window.show_pet()

    paused = {"v": False}

    def toggle_pause(checked):
        paused["v"] = checked
        window.set_paused(checked)
        if checked:
            watcher.stop()
        else:
            watcher.start()

    def toggle_audio(checked):
        audio.enabled = checked

    tray = Tray(app, config.PET_SRC,
                on_quit=app.quit,
                on_toggle_pause=toggle_pause,
                on_toggle_audio=toggle_audio)

    watcher.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 端到端手动验证**

Run: `cd E:\code\dsh\desktop-pet && python -m pet.main`
然后：
1. 确认桌宠出现在屏幕，播放待机动画。
2. 在桌面新建一个快捷方式（或复制现有 .lnk），确认快照捕捉到。
3. 删除该 .lnk（Delete 或拖回收站），确认：图标顶替 → 角色漂浮到图标旁 → 图标飞向回收站 → 飞出屏幕 → 角色归位。
4. 托盘「暂停监控」「音效」「退出」均生效。
5. 修正动画位置/时长/音效触发时机等观感问题后重跑。

- [ ] **Step 3: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/pet/main.py
git commit -m "feat: 入口组装与端到端联调"
```

---

### Task 8: PyInstaller 打包 exe

**Files:**
- Create: `desktop-pet/pet.spec`（或命令行参数）
- Create: `desktop-pet/build.ps1`（打包脚本）

- [ ] **Step 1: 升级权限安装 PyInstaller**

Run: `pip install pyinstaller --no-input --disable-pip-version-check -i https://pypi.tuna.tsinghua.edu.cn/simple`
（通过 `sandbox_permissions=danger-full-access` 执行）

- [ ] **Step 2: 写打包脚本 build.ps1**

```powershell
cd E:\code\dsh\desktop-pet
pyinstaller --noconfirm --onefile --windowed `
  --name DesktopPet `
  --add-data "assets;assets" `
  pet\main.py
```

- [ ] **Step 3: 运行打包**

Run: `powershell -File build.ps1`（通过 `sandbox_permissions=danger-full-access` 执行，因 PyInstaller 需写临时目录）
Expected: 生成 `desktop-pet/dist/DesktopPet.exe`

- [ ] **Step 4: 验证 exe**

Run: 双击 `dist/DesktopPet.exe`，确认与 `python -m pet.main` 行为一致；注意 assets 打包路径（`sys._MEIPASS`）需在 config.py 兼容：若 `getattr(sys, 'frozen', False)` 则 `BASE_DIR = Path(sys._MEIPASS)`。

- [ ] **Step 5: 提交**

```bash
cd E:\code\dsh
git add desktop-pet/build.ps1
git commit -m "build: PyInstaller 打包脚本"
```

---

## Self-Review

- **Spec coverage**：设计文档第 10 节 MVP 六项已全部映射到任务（窗口动画=Task6、监控=Task2、快照=Task5、动画序列+音效=Task6/7、托盘=Task4、打包=Task8）。
- **Placeholder scan**：无 TBD/TODO；所有步骤含可执行代码或命令。
- **Type consistency**：`IconInfo`（filename/x/y/icon）在 Task3（测试 `_Info`）、Task5（dataclass）、Task6（`icon_info.icon.pixmap`）中字段一致；`snapshot.get(name)`、`window.play_sequence(info, on_done)`、`audio.play(name)` 签名贯穿 Task3/5/6/7 一致。
- **遗留风险**：`find_desktop_listview` 的 Progman/WorkerW 结构在个别 Windows 版本可能需调序（Task5 Step5 已给排查指引）；回收站位置暂用固定点（Task6 `_find_trash_pos` 返回 (60,60)），观感优化在 Task7 联调时调整。

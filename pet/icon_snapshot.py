import ctypes
import ctypes.wintypes as wt
from dataclasses import dataclass
from pathlib import Path

LVM_FIRST = 0x1000
LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_GETITEMPOSITION = LVM_FIRST + 16
LVM_GETITEMTEXTW = LVM_FIRST + 115
LVIF_TEXT = 0x0001

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

# 64 位安全：显式声明 Win32 函数签名
user32.FindWindowW.restype = wt.HWND
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.FindWindowExW.restype = wt.HWND
user32.FindWindowExW.argtypes = [wt.HWND, wt.HWND, wt.LPCWSTR, wt.LPCWSTR]
user32.SendMessageW.restype = wt.LPARAM
user32.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, ctypes.c_void_p]
user32.GetWindowThreadProcessId.restype = wt.DWORD
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.ClientToScreen.restype = wt.BOOL
user32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]

kernel32.OpenProcess.restype = wt.HANDLE
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.VirtualAllocEx.restype = wt.LPVOID
kernel32.VirtualAllocEx.argtypes = [wt.HANDLE, wt.LPVOID, ctypes.c_size_t, wt.DWORD, wt.DWORD]
kernel32.VirtualFreeEx.restype = wt.BOOL
kernel32.VirtualFreeEx.argtypes = [wt.HANDLE, wt.LPVOID, ctypes.c_size_t, wt.DWORD]
kernel32.WriteProcessMemory.restype = wt.BOOL
kernel32.WriteProcessMemory.argtypes = [wt.HANDLE, wt.LPVOID, wt.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.ReadProcessMemory.restype = wt.BOOL
kernel32.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.CloseHandle.restype = wt.BOOL
kernel32.CloseHandle.argtypes = [wt.HANDLE]


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


def _open_process(hwnd: int) -> int:
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return kernel32.OpenProcess(
        PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE,
        False, pid.value)


def enum_icon_positions(hwnd: int) -> list[tuple[str, int, int]]:
    """跨进程枚举桌面图标，返回 [(显示名, 屏幕x, 屏幕y)]。"""
    hproc = _open_process(hwnd)
    if not hproc:
        return []
    try:
        count = user32.SendMessageW(hwnd, LVM_GETITEMCOUNT, 0, None)
        out = []
        lvi_size = ctypes.sizeof(_LVITEMW)
        buf_size = 260 * 2
        pt_size = ctypes.sizeof(wt.POINT)
        for i in range(count):
            remote_lvi = kernel32.VirtualAllocEx(
                hproc, None, lvi_size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
            remote_buf = kernel32.VirtualAllocEx(
                hproc, None, buf_size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
            remote_pt = kernel32.VirtualAllocEx(
                hproc, None, pt_size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
            if not (remote_lvi and remote_buf and remote_pt):
                break
            written = ctypes.c_size_t()
            lvi = _LVITEMW()
            lvi.mask = LVIF_TEXT
            lvi.iSubItem = 0
            lvi.pszText = ctypes.cast(remote_buf, wt.LPWSTR)
            lvi.cchTextMax = 260
            kernel32.WriteProcessMemory(
                hproc, remote_lvi, ctypes.byref(lvi), lvi_size,
                ctypes.byref(written))
            user32.SendMessageW(hwnd, LVM_GETITEMTEXTW, i, remote_lvi)
            local_buf = ctypes.create_unicode_buffer(260)
            kernel32.ReadProcessMemory(
                hproc, remote_buf, local_buf, buf_size, ctypes.byref(written))
            user32.SendMessageW(hwnd, LVM_GETITEMPOSITION, i, remote_pt)
            pt = wt.POINT()
            kernel32.ReadProcessMemory(
                hproc, remote_pt, ctypes.byref(pt), pt_size,
                ctypes.byref(written))
            user32.ClientToScreen(hwnd, ctypes.byref(pt))
            out.append((local_buf.value, pt.x, pt.y))
            kernel32.VirtualFreeEx(hproc, remote_lvi, 0, MEM_RELEASE)
            kernel32.VirtualFreeEx(hproc, remote_buf, 0, MEM_RELEASE)
            kernel32.VirtualFreeEx(hproc, remote_pt, 0, MEM_RELEASE)
        return out
    finally:
        kernel32.CloseHandle(hproc)


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
        from PySide6.QtCore import QFileInfo
        for display_name, x, y in enum_icon_positions(hwnd):
            filename = display_name + ".lnk"
            lnk = self._desktop / filename
            if not lnk.exists():
                continue
            icon = self._get_provider().icon(QFileInfo(str(lnk)))
            self._snapshot[filename] = IconInfo(filename, x, y, icon)

    def get(self, filename: str) -> IconInfo | None:
        return self._snapshot.get(filename)

import asyncio
import json
import sys
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pet.icon_snapshot import (find_desktop_listview, enum_icon_positions,
                               extract_icon_png_b64)
from pet.file_watcher import FileWatcher

DESKTOP = Path.home() / "Desktop"
PORT = 8765


class Backend:
    def __init__(self):
        self.clients = set()
        self.snapshot = {}      # {filename: (x, y, icon_b64)}
        self._icon_cache = {}   # {filename: icon_b64}
        self.loop = None

    def _resolve_name(self, display_name, entries, stem_map):
        # 桌面图标显示名 -> 真实文件名（支持文件夹/普通文件/.lnk）
        if display_name in entries:
            return display_name
        if (display_name + ".lnk") in entries:
            return display_name + ".lnk"
        # 隐藏扩展名：foo.txt 显示为 foo
        return stem_map.get(display_name)

    def refresh_snapshot(self):
        hwnd = find_desktop_listview()
        if not hwnd:
            return
        items = enum_icon_positions(hwnd)
        entries = {p.name for p in DESKTOP.iterdir()}
        stem_map = {}
        for p in DESKTOP.iterdir():
            stem_map.setdefault(p.stem, p.name)
        snap = {}
        for name, x, y in items:
            real = self._resolve_name(name, entries, stem_map)
            if real is None:
                continue
            icon = self._icon_cache.get(real)
            if icon is None:
                icon = extract_icon_png_b64(str(DESKTOP / real))
                self._icon_cache[real] = icon
            snap[real] = (x, y, icon)
        self.snapshot = snap

    def on_delete(self, filename, mode):
        print(f"delete event: {filename} mode={mode}", flush=True)
        info = self.snapshot.get(filename)
        if info is None:
            print(f"  '{filename}' not in snapshot", flush=True)
            return
        x, y, icon = info
        msg = json.dumps({
            "type": "delete", "filename": filename,
            "x": x, "y": y, "icon": icon})
        print(f"  broadcasting: x={x} y={y} icon={'yes' if icon else 'no'}",
              flush=True)
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.broadcast(msg), self.loop)

    async def broadcast(self, msg):
        for client in list(self.clients):
            try:
                await client.send(msg)
            except Exception:
                self.clients.discard(client)

    async def handler(self, ws):
        self.clients.add(ws)
        try:
            async for _ in ws:
                pass
        finally:
            self.clients.discard(ws)

    async def snapshot_loop(self):
        while True:
            await asyncio.to_thread(self.refresh_snapshot)
            await asyncio.sleep(1.0)


async def main():
    backend = Backend()
    backend.loop = asyncio.get_running_loop()
    asyncio.create_task(backend.snapshot_loop())
    watcher = FileWatcher(DESKTOP, backend.on_delete)
    watcher.start()
    await asyncio.to_thread(backend.refresh_snapshot)
    print(f"backend listening on ws://127.0.0.1:{PORT}", flush=True)
    async with websockets.serve(backend.handler, "127.0.0.1", PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import json
import sys
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pet.icon_snapshot import find_desktop_listview, enum_icon_positions
from pet.file_watcher import FileWatcher

DESKTOP = Path.home() / "Desktop"
PORT = 8765


class Backend:
    def __init__(self):
        self.clients = set()
        self.snapshot = {}  # {filename: (x, y)}
        self.loop = None

    def refresh_snapshot(self):
        hwnd = find_desktop_listview()
        if not hwnd:
            return
        items = enum_icon_positions(hwnd)
        snap = {}
        for name, x, y in items:
            filename = name + ".lnk"
            if (DESKTOP / filename).exists():
                snap[filename] = (x, y)
        self.snapshot = snap

    def on_delete(self, filename, mode):
        print(f"delete event: {filename} mode={mode}", flush=True)
        info = self.snapshot.get(filename)
        if info is None:
            print(f"  '{filename}' not in snapshot", flush=True)
            return
        x, y = info
        msg = json.dumps({
            "type": "delete", "filename": filename, "x": x, "y": y})
        print(f"  broadcasting: {msg}", flush=True)
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

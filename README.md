# Cyrene Deskpet · 昔涟桌宠
## v0.2.0(开发中)

一个 Windows 桌面宠物：Q 版「昔涟」（《崩坏：星穹铁道》角色，坐在弓上）常驻在桌面上，可以与你互动，陪伴你的冲浪时光。
当你**删除桌面图标**时，她会飞过去把图标装进垃圾桶、再一脚踹飞，让「删除」这件事变得生动有趣。

## ✨ 功能特性

- **删除动画**：删除桌面任意文件/文件夹/快捷方式时触发 —— 桌宠移动到图标旁，垃圾桶身体从下方冲上、盖子从上方落下合住图标，晃动两下后桌宠飞过去踹飞，垃圾桶旋转飞向回收站
- **图标顶替**：删除瞬间用缓存图标外观顶替原位置，实现「图标不先消失，随动画自然消失」
- **拖拽互动**：鼠标可拖动桌宠；快速拖动会触发**眩晕**
- **投喂**：右键桌宠，零食从天而降 + 粉色音符
- **视线跟随**：眼睛跟随鼠标；鼠标闲置 2.5 秒后随机打量四周
- **待机动作**：轻微摇摆、周期性飘出粉色音符
- **桌面友好**：透明窗口、鼠标穿透（可正常操作桌面图标）、始终置顶、系统托盘菜单

## 🏗️ 技术架构

| 层 | 技术 | 说明 |
|----|------|------|
| 前端渲染 | Electron + WebGL | 透明无边框置顶窗口，`Anime2.5DRig` 自动绑骨渲染分层 PSD |
| 后端 | Python 3.12 + WebSocket | 监控桌面、枚举图标坐标、截取图标外观，经 `ws://127.0.0.1:8765` 推送 |
| 文件监控 | watchdog | 监听桌面删除事件（`deleted` / 拖入回收站 `moved`） |
| 图标快照 | ctypes（Win32 消息） | 跨进程枚举桌面图标坐标（`LVM_GETITEMPOSITION`）+ 提取图标 PNG |
| 打包 | electron-builder + PyInstaller | 前端打包 portable exe，后端打包为独立 exe |

```
Electron 主进程 (electron/main.js)
   ├─ 透明置顶窗口 ← 加载 web/index.html（WebGL 渲染 + 动画逻辑）
   └─ 启动 Python 后端 (pet/backend_server.exe)
          ├─ file_watcher.py    监控桌面删除
          ├─ icon_snapshot.py   枚举图标坐标 + 截取图标
          └─ WebSocket ──删除事件/坐标/图标──▶ 前端触发动画
```

## 📁 目录结构

```
desktop-pet/
├── electron/              # Electron 主进程 + 打包配置
│   ├── main.js            # 主进程：透明置顶窗口、托盘、启动后端
│   ├── preload.js         # 渲染进程 IPC 桥接
│   ├── package.json       # electron-builder 打包配置
│   ├── icon.ico           # exe 图标
│   └── tray.png           # 托盘图标
├── pet/                   # Python 后端
│   ├── backend_server.py  # WebSocket 服务 + 图标快照维护
│   ├── file_watcher.py    # watchdog 桌面删除监听
│   └── icon_snapshot.py   # ctypes 枚举图标 + 提取图标 PNG
├── web/                   # 前端渲染与动画
│   ├── index.html         # 桌宠渲染 + 全部动画/交互逻辑
│   ├── pet.psd            # 昔涟分层素材（Anime2.5DRig 渲染）
│   ├── bin_body.png       # 垃圾桶桶身
│   ├── bin_lid.png        # 垃圾桶盖子
│   ├── lib/               # Anime2.5DRig 渲染库
│   └── music/             # 音符素材
├── assets/                # 素材（角色图、帧、图标）
├── tests/                 # 单元测试
├── requirements.txt       # Python 依赖
└── backend_server.spec    # PyInstaller 打包配置
```

## 🚀 运行（开发模式）

环境要求：Node.js、Python 3.12

```bash
# 1. 安装 Python 依赖
pip install websockets watchdog Pillow pywin32

# 2. 安装 Electron 依赖
cd electron
npm install

# 3. 启动（开发模式用系统 Python 跑后端）
npm start
```

## 📦 打包 exe

1. 打包后端（生成 `pet/backend_server.exe`）：

```bash
pyinstaller backend_server.spec --distpath electron/backend_dist --workpath electron/backend_build --clean --noconfirm
copy electron\backend_dist\backend_server.exe pet\backend_server.exe
```

2. 打包前端（生成 `electron/dist/Cyrene deskpet v0.1.exe`）：

```bash
cd electron
npx electron-builder
```

> 国内网络环境建议先设置镜像，避免 electron-builder 下载 winCodeSign 超时：
> ```powershell
> $env:ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
> $env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
> ```

## ⚙️ 托盘菜单

- **投喂**：手动触发投喂动画
- **暂停监控**：暂停监听桌面删除事件
- **音效**：开关音效
- **退出**：退出程序

## 📄 版权说明

昔涟为《崩坏：星穹铁道》游戏角色，项目所用桌宠图片来自B站视频截图，视频链接[https://www.bilibili.com/video/BV1FPydBPEfC/?spm_id_from=333.337.search-card.all.click]()。本项目素材仅供个人自用学习，不涉及商业分发。

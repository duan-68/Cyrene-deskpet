const { app, BrowserWindow, screen, ipcMain, Tray, Menu } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const RES_DIR = app.isPackaged ? process.resourcesPath : path.join(__dirname, '..');
const WEB_DIR = path.join(RES_DIR, 'web');

ipcMain.handle('get-sample-psd', () => {
  return fs.readFileSync(path.join(WEB_DIR, 'pet.psd'));
});
ipcMain.handle('read-psd', (e, absPath) => {
  return fs.readFileSync(absPath);
});
ipcMain.handle('set-ignore-mouse', (e, ignore) => {
  if (win) win.setIgnoreMouseEvents(ignore, { forward: true });
});

let pythonProc = null;
let tray = null;

function createTray() {
  tray = new Tray(path.join(__dirname, 'tray.png'));
  const menu = Menu.buildFromTemplate([
    { label: '投喂', click: () => {
        if (win) win.webContents.send('feed');
    }},
    { label: '暂停监控', type: 'checkbox', click: (item) => {
        if (win) win.webContents.send('set-paused', item.checked);
    }},
    { label: '音效', type: 'checkbox', checked: true, click: (item) => {
        if (win) win.webContents.send('set-audio', item.checked);
    }},
    { type: 'separator' },
    { label: '退出', click: () => app.quit() },
  ]);
  tray.setToolTip('桌宠');
  tray.setContextMenu(menu);
}

let win = null;

function startBackend() {
  let cmd, args;
  if (app.isPackaged) {
    // 打包后：调用 PyInstaller 打包的独立后端 exe（不依赖 Python 环境）
    cmd = path.join(RES_DIR, 'pet', 'backend_server.exe');
    args = [];
  } else {
    // 开发：用系统 Python 运行
    cmd = 'python';
    args = [path.join(RES_DIR, 'pet', 'backend_server.py')];
  }
  pythonProc = spawn(cmd, args, { stdio: 'ignore' });
  pythonProc.on('exit', (code) => {
    if (!app.isQuitting) {
      // 后端异常退出时重启
      setTimeout(startBackend, 1000);
    }
  });
}

function createWindow() {
  const area = screen.getPrimaryDisplay().workArea;
  win = new BrowserWindow({
    x: area.x,
    y: area.y,
    width: area.width,
    height: area.height,
    transparent: true,
    backgroundColor: '#00000000',
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: true,
    hasShadow: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  // 鼠标穿透（用户仍可操作桌面图标）；托盘为独立窗口不受影响
  win.setIgnoreMouseEvents(true, { forward: true });
  win.setAlwaysOnTop(true, 'screen-saver');
  // 始终置顶：定期重新置顶 + 失焦时重新置顶
  const keepTop = setInterval(() => {
    if (win && !win.isDestroyed()) {
      win.setAlwaysOnTop(true, 'screen-saver');
      win.moveTop();
    }
  }, 2000);
  win.on('blur', () => {
    if (win && !win.isDestroyed()) {
      win.setAlwaysOnTop(true, 'screen-saver');
      win.moveTop();
    }
  });
  win.on('closed', () => clearInterval(keepTop));
  win.webContents.on('console-message', (event) => {
    console.log('[renderer]', event.message);
  });
  win.webContents.on('did-finish-load', () => {
    console.log('[main] did-finish-load visible=' + win.isVisible() +
      ' bounds=' + JSON.stringify(win.getBounds()));
  });
  win.loadFile(path.join(__dirname, '..', 'web', 'index.html'), { query: { pet: '1' } });
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
  createTray();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  app.isQuitting = true;
  if (pythonProc) pythonProc.kill();
});

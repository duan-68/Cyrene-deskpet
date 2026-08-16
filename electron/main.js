const { app, BrowserWindow, screen } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let pythonProc = null;

function startBackend() {
  const script = path.join(__dirname, '..', 'pet', 'backend_server.py');
  pythonProc = spawn('python', [script], { stdio: 'ignore' });
  pythonProc.on('exit', (code) => {
    if (!app.isQuitting) {
      // 后端异常退出时重启
      setTimeout(startBackend, 1000);
    }
  });
}

function createWindow() {
  const area = screen.getPrimaryDisplay().workArea;
  const win = new BrowserWindow({
    x: area.x,
    y: area.y,
    width: area.width,
    height: area.height,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: true,
    hasShadow: false,
    webPreferences: {
      contextIsolation: false,
      nodeIntegration: true,
    },
  });
  // 鼠标穿透（用户仍可操作桌面图标）；托盘为独立窗口不受影响
  win.setIgnoreMouseEvents(true, { forward: true });
  win.setAlwaysOnTop(true, 'screen-saver');
  win.loadFile(path.join(__dirname, '..', 'web', 'index.html'), { query: { pet: '1' } });
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
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

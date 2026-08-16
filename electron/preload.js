const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('petAPI', {
  getSamplePsd: () => ipcRenderer.invoke('get-sample-psd'),
  readPsd: (absPath) => ipcRenderer.invoke('read-psd', absPath),
  setIgnoreMouse: (ignore) => ipcRenderer.invoke('set-ignore-mouse', ignore),
  onFeed: (cb) => ipcRenderer.on('feed', () => cb()),
  onPaused: (cb) => ipcRenderer.on('set-paused', (e, v) => cb(v)),
  onAudio: (cb) => ipcRenderer.on('set-audio', (e, v) => cb(v)),
});

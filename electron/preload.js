const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('petAPI', {
  getSamplePsd: () => ipcRenderer.invoke('get-sample-psd'),
  readPsd: (absPath) => ipcRenderer.invoke('read-psd', absPath),
});

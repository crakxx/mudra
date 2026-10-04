'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('mudraDashboard', Object.freeze({
  getState: () => ipcRenderer.invoke('dashboard:get-state'),
  setSetting: (key, value) => ipcRenderer.invoke(
    'dashboard:set-setting', key, value
  ),
  resetSettings: () => ipcRenderer.invoke('dashboard:reset-settings'),
  onPreviewFrame: (callback) => {
    if (typeof callback !== 'function') {
      throw new TypeError('preview callback must be a function');
    }
    const listener = (_event, base64) => {
      if (typeof base64 === 'string') callback(base64);
    };
    ipcRenderer.on('dashboard:preview-frame', listener);
    return () => ipcRenderer.removeListener(
      'dashboard:preview-frame', listener
    );
  }
}));

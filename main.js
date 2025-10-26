const { app, BrowserWindow } = require('electron');

function createWindow() {
  const win = new BrowserWindow({
    width: 700,
    height: 520,
    webPreferences: { nodeIntegration: true, contextIsolation: false }
  });
  win.loadFile('index.html');
}

app.whenReady().then(() => createWindow());

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

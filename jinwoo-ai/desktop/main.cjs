// Electron shell foundation. Install Electron only after the web/API source is
// settled: `npm install --save-dev electron`, then set JINWOO_DEV_SERVER_URL.
const { app, BrowserWindow, shell } = require('electron')
const path = require('path')
const { pathToFileURL } = require('url')

const createWindow = () => {
  const window = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 960,
    minHeight: 660,
    backgroundColor: '#07080e',
    autoHideMenuBar: true,
    webPreferences: {
      // Keep renderer/browser code isolated from Node and desktop privileges.
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  const developmentUrl = process.env.JINWOO_DEV_SERVER_URL
  const productionUrl = pathToFileURL(path.join(__dirname, '..', 'dist', 'index.html')).toString()
  window.loadURL(developmentUrl || productionUrl)

  window.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://')) shell.openExternal(url)
    return { action: 'deny' }
  })
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })

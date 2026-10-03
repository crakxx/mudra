'use strict';

const path = require('node:path');
const { spawn } = require('node:child_process');
const { app, globalShortcut } = require('electron');

const DESKTOP_ID = 'io.github.crakxx.mudra.desktop';
const PAUSE_SHORTCUT = 'Control+Alt+P';
const QUIT_SHORTCUT = 'Control+Alt+Q';

app.setName('Mudra');
app.setDesktopName(DESKTOP_ID);

let child = null;
let shuttingDown = false;

function pythonArgs() {
  const raw = process.env.MUDRA_PYTHON_ARGS_JSON || '[]';
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    throw new Error(`Invalid MUDRA_PYTHON_ARGS_JSON: ${error.message}`);
  }
  if (!Array.isArray(parsed) || !parsed.every((value) => typeof value === 'string')) {
    throw new Error('MUDRA_PYTHON_ARGS_JSON must be a JSON array of strings');
  }
  return parsed;
}

function sendControl(command) {
  if (!child || !child.stdin || !child.stdin.writable) return false;
  child.stdin.write(`${command}\n`);
  return true;
}

function registerShortcut(accelerator, command) {
  const submitted = globalShortcut.register(accelerator, () => {
    sendControl(command);
  });
  if (!submitted) {
    console.error(`Failed to submit global shortcut: ${accelerator}`);
  }
  return submitted;
}

function requestShutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  sendControl('quit');

  const timer = setTimeout(() => {
    if (child && !child.killed) child.kill('SIGTERM');
    app.quit();
  }, 1500);
  timer.unref();
}

app.whenReady().then(() => {
  const root = path.resolve(__dirname, '..');

  child = spawn(
    'python3',
    [path.join(root, 'mudra.py'), '--control-stdin', ...pythonArgs()],
    {
      cwd: root,
      stdio: ['pipe', 'inherit', 'inherit'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      shell: false
    }
  );

  child.on('error', (error) => {
    console.error(`Failed to start mudra.py: ${error.message}`);
    process.exitCode = 1;
    app.quit();
  });

  child.on('exit', (code, signal) => {
    child = null;
    if (code && code !== 0) {
      console.error(`mudra.py exited with code ${code}${signal ? ` (signal ${signal})` : ''}`);
      process.exitCode = code;
    }
    app.quit();
  });

  registerShortcut(PAUSE_SHORTCUT, 'pause');
  registerShortcut(QUIT_SHORTCUT, 'quit');

  if (process.env.XDG_SESSION_TYPE === 'wayland') {
    console.log(
      'Global shortcuts requested through the XDG GlobalShortcuts portal. ' +
      'GNOME may ask for consent on first use.'
    );
  }

  // Future Electron versions expose the portal's asynchronous result.  Keep
  // this hook feature-detected so the code becomes more informative without
  // breaking the pinned Electron 45 alpha, where it is not yet available.
  if (typeof globalShortcut.on === 'function') {
    globalShortcut.on('registration-resolved', (accelerator, bound) => {
      console.log(`Global shortcut ${accelerator}: ${bound ? 'bound' : 'not bound'}`);
    });
  }
}).catch((error) => {
  console.error(error);
  process.exitCode = 1;
  app.quit();
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (child && !child.killed) {
    child.kill('SIGTERM');
  }
});

process.on('SIGINT', requestShutdown);
process.on('SIGTERM', requestShutdown);

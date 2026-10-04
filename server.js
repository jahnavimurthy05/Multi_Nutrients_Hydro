// server.js (full) - Node + Serial + Python optimize integration
const express = require('express');
const { SerialPort } = require('serialport');
const { ReadlineParser } = require('@serialport/parser-readline');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const app = express();
const PORT = 3000;

// allow JSON body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// serve public
app.use(express.static(path.join(__dirname, 'public')));

// ---------- Serial port (same as before) ----------
const SERIAL_PORT_PATH = 'COM5'; // adjust if needed
const BAUD_RATE = 9600;

let sensorData = { ph:'--', temperature:'--', humidity:'--' };

try {
  const serialPort = new SerialPort({ path: SERIAL_PORT_PATH, baudRate: BAUD_RATE, autoOpen: true });
  const parser = serialPort.pipe(new ReadlineParser({ delimiter: '\n' }));

  parser.on('data', (line) => {
    line = line.trim();
    console.log("Arduino:", line);

    if (line.includes("Humidity =")) {
      const match = line.match(/Humidity\s*=\s*([\d.]+)/);
      if (match) sensorData.humidity = match[1];
    }
    if (line.includes("pH Val")) {
      const match = line.match(/pH Val:\s*([\d.]+)/);
      if (match) sensorData.ph = match[1];
    }
    if (line.includes("Temperature =")) {
      const match = line.match(/Temperature\s*=\s*([\d.]+)/);
      if (match) sensorData.temperature = match[1];
    }
  });

  serialPort.on('open', () => console.log('Serial port opened:', SERIAL_PORT_PATH, 'baudRate', BAUD_RATE));
  serialPort.on('error', (err) => console.error('Serial port error:', err.message));
} catch (e) {
  console.error('Failed to open serial port:', e.message || e);
}

// ---------- /data endpoint for dashboard ----------
app.get('/data', (req, res) => {
  res.json(sensorData);
});

// ---------- /optimize endpoint: runs Python script ----------
app.post('/optimize', (req, res) => {
  // expects JSON body: { "crops": ["Tomato","Lettuce"] }
  const crops = Array.isArray(req.body.crops) ? req.body.crops : [];
  const cropsArg = crops.join(',');

  // ensure python script exists
  const pyPath = path.join(__dirname, 'optimize.py');
  if (!fs.existsSync(pyPath)) {
    return res.status(500).json({ error: 'optimize.py not found on server' });
  }

  // Try 'python' then 'py' on Windows if needed
  const tryCommands = ['python', 'py'];
  let spawned = null;
  let usedCmd = null;

  function runWith(cmdIndex) {
    if (cmdIndex >= tryCommands.length) {
      return res.status(500).json({ error: 'Python not found. Install Python and ensure "python" command works.' });
    }
    const cmd = tryCommands[cmdIndex];
    usedCmd = cmd;
    const args = [pyPath, cropsArg];
    spawned = spawn(cmd, args, { cwd: __dirname });

    let stdout = '';
    let stderr = '';

    spawned.stdout.on('data', (data) => { stdout += data.toString(); });
    spawned.stderr.on('data', (data) => { stderr += data.toString(); });

    spawned.on('close', (code) => {
      if (code === 0 && stdout) {
        try {
          const parsed = JSON.parse(stdout);
          // If plot path exists, include accessible URL
          const plotPath = path.join(__dirname, 'public', 'optimize_plot.png');
          if (fs.existsSync(plotPath)) {
            parsed.plot = '/optimize_plot.png';
          }
          return res.json(parsed);
        } catch (err) {
          // parse error -> return raw output + stderr for debugging
          return res.status(500).json({ error: 'Invalid JSON from python', stdout, stderr });
        }
      } else {
        // try next command if python missing
        if (/not found|is not recognized/i.test(stderr + stdout)) {
          return runWith(cmdIndex + 1);
        }
        return res.status(500).json({ error: 'Python script failed', code, stdout, stderr });
      }
    });

    spawned.on('error', (err) => {
      // maybe command not found -> try next
      return runWith(cmdIndex + 1);
    });
  }

  runWith(0);
});

// start server
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
  console.log('Make sure Arduino is connected and Serial Monitor is closed.');
});

#!/bin/bash

export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
export QT_QUICK_BACKEND=software
export QSG_RENDER_LOOP=basic
export QSG_RENDERER_BATCH_NODE_SIZE=64
export DOCSUMMARIZER_DATA_DIR=/tmp/docsummarizer
mkdir -p /tmp/docsummarizer/logs
mkdir -p "$HOME/Desktop" "$HOME/Downloads" "$HOME/Documents" "$HOME/Music" "$HOME/Pictures" "$HOME/Videos" 2>/dev/null || true
mkdir -p /root/Desktop /root/Downloads /root/Documents /root/Music /root/Pictures /root/Videos 2>/dev/null || true

# 1. Start Ollama service in the background if installed
if command -v ollama >/dev/null 2>&1; then
    echo "Starting background Ollama service..."
    ollama serve >/tmp/ollama.log 2>&1 &
    sleep 2
fi

# 2. Ensure noVNC root defaults to vnc.html and inject Computer File Upload bar + Dynamic Display Controls
python3 - <<'PYEOF'
from pathlib import Path
for name in ["vnc.html", "vnc_lite.html", "index.html"]:
    p = Path("/usr/share/novnc") / name
    if p.exists():
        html = p.read_text(encoding="utf-8", errors="ignore")
        snippet = """
<!-- Cloud Direct PC Upload & Display Controls Overlay -->
<style>
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    overflow: hidden !important;
    background: #0b0d13 !important;
  }
  #noVNC_container {
    width: 100vw !important;
    height: 100vh !important;
    overflow: hidden !important;
  }
  canvas {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
  }
  #quick-ctrl-bar {
    position: fixed;
    top: 8px;
    left: 200px;
    z-index: 999999;
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(11, 13, 19, 0.94);
    backdrop-filter: blur(10px);
    border: 1px solid #6fc3d8;
    border-radius: 6px;
    padding: 4px 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.7);
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  }
  .ctrl-btn {
    background: #172430;
    color: #6fc3d8;
    border: 1px solid #2a4d5e;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 700;
    font-size: 11px;
    display: flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s ease;
  }
  .ctrl-btn:hover {
    background: #6fc3d8;
    color: #0b0d13;
  }
  .ctrl-btn-primary {
    background: #6fc3d8;
    color: #0b0d13;
    border: none;
  }
</style>

<div id="quick-ctrl-bar">
  <button class="ctrl-btn ctrl-btn-primary" onclick="document.getElementById('pc-file-input').click()">📁 UPLOAD FROM PC</button>
  <button class="ctrl-btn" onclick="fitScreen()" title="Fit desktop perfectly to browser window">🔍 FIT SCREEN</button>
  <button class="ctrl-btn" onclick="zoomIn()" title="Zoom in">➕ ZOOM IN</button>
  <button class="ctrl-btn" onclick="zoomOut()" title="Zoom out">➖ ZOOM OUT</button>
  <button class="ctrl-btn" onclick="toggleFullscreen()" title="Toggle Fullscreen">🖥️ FULLSCREEN</button>
  <input type="file" id="pc-file-input" style="display:none" accept=".pdf,.docx,.rtf,.txt,.md,.png,.jpg,.jpeg,.webp" onchange="uploadLocalDocument(this)">
  <span id="upload-feedback" style="color:#6fc3d8;font-size:11px;font-weight:500;margin-left:4px;"></span>
</div>

<script>
// Auto-force noVNC scaling mode to 'scale' (Fit to screen) so mouse and screen always align perfectly
function ensureScaling() {
  try {
    localStorage.setItem('noVNC_resize', 'scale');
    localStorage.setItem('noVNC_autoconnect', 'true');
    if (window.UI) {
      if (typeof UI.setSetting === 'function') {
        UI.setSetting('resize', 'scale');
      }
      if (UI.rfb) {
        UI.rfb.scaleViewport = true;
        UI.rfb.resizeSession = false;
      }
    }
  } catch(e) {}
}

window.addEventListener('load', function() {
  ensureScaling();
  setTimeout(ensureScaling, 500);
  setTimeout(ensureScaling, 2000);
});

var currentZoom = 1.0;
function fitScreen() {
  currentZoom = 1.0;
  ensureScaling();
  var canvas = document.querySelector('#noVNC_container canvas') || document.querySelector('#noVNC_screen canvas');
  if (canvas) {
    canvas.style.transform = 'none';
  }
}

function zoomIn() {
  currentZoom = Math.min(2.5, currentZoom + 0.15);
  applyZoom();
}

function zoomOut() {
  currentZoom = Math.max(0.5, currentZoom - 0.15);
  applyZoom();
}

function applyZoom() {
  var canvas = document.querySelector('#noVNC_container canvas') || document.querySelector('#noVNC_screen canvas');
  if (canvas) {
    canvas.style.transform = 'scale(' + currentZoom + ')';
    canvas.style.transformOrigin = 'center center';
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(function(){});
  } else {
    document.exitFullscreen().catch(function(){});
  }
}

function uploadLocalDocument(input) {
  if (!input.files || !input.files[0]) return;
  var file = input.files[0];
  var feedback = document.getElementById('upload-feedback');
  feedback.textContent = 'Uploading ' + file.name + '...';
  var formData = new FormData();
  formData.append('file', file);
  fetch('/api/upload', { method: 'POST', body: formData })
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.success) {
        feedback.textContent = '✅ ' + file.name + ' Loaded into App!';
      } else {
        feedback.textContent = '❌ ' + (data.error || 'Upload failed');
      }
      setTimeout(function() { feedback.textContent = ''; }, 6000);
    })
    .catch(function(err) {
      feedback.textContent = '❌ Error: ' + err;
    });
}
// Global drag-and-drop listener
window.addEventListener('dragover', function(e) { e.preventDefault(); }, false);
window.addEventListener('drop', function(e) {
  e.preventDefault();
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    document.getElementById('pc-file-input').files = e.dataTransfer.files;
    uploadLocalDocument(document.getElementById('pc-file-input'));
  }
}, false);
</script>
"""
        if "quick-ctrl-bar" not in html:
            html = html.replace("</body>", snippet + "\n</body>")
            p.write_text(html, encoding="utf-8")
PYEOF
if [ -f "/usr/share/novnc/vnc.html" ]; then
    cp /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true
fi

# 3. Start virtual Xvfb display in Full HD 1920x1080
echo "Starting virtual display Xvfb on :99 (1920x1080 native)..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
sleep 2

# 4. Start Openbox & High-Definition Lossless VNC Server
echo "Starting Openbox window manager on :99..."
mkdir -p ~/.config/openbox
cat <<'EOF' > ~/.config/openbox/rc.xml
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <desktops>
    <number>1</number>
    <firstdefault>1</firstdefault>
  </desktops>
</openbox_config>
EOF
openbox --sm-disable >/dev/null 2>&1 &
sleep 1

echo "Starting high-fidelity lossless VNC server on port 5900..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 -noxdamage -nowf -ncache 10 -ncache_cr >/tmp/x11vnc.log 2>&1 &
# 5. Start internal websockify bridge on port 5901
echo "Starting internal websockify on port 5901..."
websockify 5901 localhost:5900 >/tmp/websockify.log 2>&1 &
sleep 1

# 6. Bind unified Web Server (REST API, direct upload & noVNC proxy) to primary deployment PORT
APP_PORT="${PORT:-${WEBSITES_PORT:-8080}}"
echo "Starting DocSummarizer Unified Web Server on port ${APP_PORT}..."
python -m docsummarizer.web_app --port "${APP_PORT}" >/tmp/web_app.log 2>&1 &
sleep 1

echo "Launching DocSummarizer QML Desktop Application..."
while true; do
    python run.py
    EXIT_CODE=$?
    echo "DocSummarizer process exited with code ${EXIT_CODE}. Restarting in 2s..."
    sleep 2
done

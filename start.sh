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

# 2. Configure noVNC for full-window responsive auto-scaling and global drag-and-drop
python3 - <<'PYEOF'
from pathlib import Path
for name in ["vnc.html", "vnc_lite.html", "index.html"]:
    p = Path("/usr/share/novnc") / name
    if p.exists():
        html = p.read_text(encoding="utf-8", errors="ignore")
        snippet = """
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
  #upload-feedback-toast {
    position: fixed;
    top: 12px;
    right: 20px;
    z-index: 999999;
    background: rgba(11, 13, 19, 0.92);
    border: 1px solid #6fc3d8;
    border-radius: 6px;
    padding: 6px 14px;
    color: #6fc3d8;
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    font-size: 12px;
    font-weight: 600;
    display: none;
    box-shadow: 0 4px 16px rgba(0,0,0,0.8);
  }
</style>
<div id="upload-feedback-toast"></div>
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

function showUploadToast(msg, isError) {
  var t = document.getElementById('upload-feedback-toast');
  if (!t) return;
  t.textContent = msg;
  t.style.borderColor = isError ? '#ff4d4f' : '#6fc3d8';
  t.style.color = isError ? '#ff4d4f' : '#6fc3d8';
  t.style.display = 'block';
  setTimeout(function() { t.style.display = 'none'; }, 5000);
}

function uploadLocalDocument(file) {
  if (!file) return;
  showUploadToast('Uploading ' + file.name + '...', false);
  var formData = new FormData();
  formData.append('file', file);
  fetch('/api/upload', { method: 'POST', body: formData })
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.success) {
        showUploadToast('✅ ' + file.name + ' Loaded into App!', false);
      } else {
        showUploadToast('❌ ' + (data.error || 'Upload failed'), true);
      }
    })
    .catch(function(err) {
      showUploadToast('❌ Error: ' + err, true);
    });
}

// Global drag-and-drop listener anywhere on the browser window
window.addEventListener('dragover', function(e) { e.preventDefault(); }, false);
window.addEventListener('drop', function(e) {
  e.preventDefault();
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    uploadLocalDocument(e.dataTransfer.files[0]);
  }
}, false);
</script>
"""
        if "upload-feedback-toast" not in html:
            html = html.replace("</body>", snippet + "\n</body>")
            p.write_text(html, encoding="utf-8")
PYEOF
if [ -f "/usr/share/novnc/vnc.html" ]; then
    cp /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true
fi

# 3. Start virtual Xvfb display in 1366x768 (Native 16:9 Laptop/Desktop Resolution)
echo "Starting virtual display Xvfb on :99 (1366x768 native)..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 1366x768x24 -ac +extension GLX +render -noreset &
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

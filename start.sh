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

# 2. Ensure noVNC root defaults to vnc.html and inject Computer File Upload bar + Drag-and-Drop
python3 - <<'PYEOF'
from pathlib import Path
for name in ["vnc.html", "vnc_lite.html", "index.html"]:
    p = Path("/usr/share/novnc") / name
    if p.exists():
        html = p.read_text(encoding="utf-8", errors="ignore")
        snippet = """
<!-- Cloud Direct PC Upload Overlay -->
<div id="quick-upload-bar" style="position:fixed;top:10px;right:70px;z-index:999999;display:flex;align-items:center;gap:10px;background:#0d1820;border:2px solid #10b981;border-radius:8px;padding:8px 16px;box-shadow:0 6px 20px rgba(0,0,0,0.8);font-family:system-ui,sans-serif;">
  <button id="upload-from-pc-btn" style="background:#10b981;color:#0d1820;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-weight:800;font-size:13px;letter-spacing:0.5px;" onclick="document.getElementById('pc-file-input').click()">📁 UPLOAD FILE FROM YOUR PC</button>
  <input type="file" id="pc-file-input" style="display:none" accept=".pdf,.docx,.rtf,.txt,.md,.png,.jpg,.jpeg,.webp" onchange="uploadLocalDocument(this)">
  <span id="upload-feedback" style="color:#6ee7b7;font-size:12px;font-weight:600;"></span>
</div>
<script>
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
        if "quick-upload-bar" not in html:
            html = html.replace("</body>", snippet + "\n</body>")
            p.write_text(html, encoding="utf-8")
PYEOF
if [ -f "/usr/share/novnc/vnc.html" ]; then
    cp /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true
fi

# 3. Start virtual Xvfb display
echo "Starting virtual display Xvfb on :99..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render -noreset &
sleep 2

# 4. Start Openbox & Ultra-Fast VNC Server
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

echo "Starting low-latency VNC server on port 5900..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 -noxdamage -nowf >/tmp/x11vnc.log 2>&1 &
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

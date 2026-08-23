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

# 2. Ensure noVNC root defaults to vnc.html so visiting '/' loads the web interface
if [ -f "/usr/share/novnc/vnc.html" ]; then
    cp /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true
elif [ -f "/usr/share/novnc/vnc_lite.html" ]; then
    cp /usr/share/novnc/vnc_lite.html /usr/share/novnc/index.html 2>/dev/null || true
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
sleep 2

# 5. Bind noVNC HTML5 proxy to primary deployment PORT
APP_PORT="${PORT:-${WEBSITES_PORT:-8080}}"
echo "Starting noVNC HTML5 web proxy on port ${APP_PORT}..."
websockify --web /usr/share/novnc "${APP_PORT}" localhost:5900 &
sleep 2

echo "Launching DocSummarizer QML Desktop Application..."
while true; do
    python run.py
    EXIT_CODE=$?
    echo "DocSummarizer process exited with code ${EXIT_CODE}. Restarting in 2s..."
    sleep 2
done

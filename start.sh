#!/bin/bash

export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
export QT_QUICK_BACKEND=software
export QSG_RENDER_LOOP=basic
export QSG_RENDERER_BATCH_NODE_SIZE=64
export OLLAMA_HOST=127.0.0.1:11434

# 1. Start Ollama service in the background if installed
if command -v ollama >/dev/null 2>&1; then
    echo "Starting background Ollama service..."
    ollama serve >/tmp/ollama.log 2>&1 &
    sleep 3
    (ollama pull llama3 >/dev/null 2>&1 &) || true
fi

# 2. Ensure noVNC root defaults to vnc.html so visiting '/' loads the web interface
if [ -f "/usr/share/novnc/vnc.html" ]; then
    cp /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true
elif [ -f "/usr/share/novnc/vnc_lite.html" ]; then
    cp /usr/share/novnc/vnc_lite.html /usr/share/novnc/index.html 2>/dev/null || true
fi

# 3. Start virtual Xvfb display with 16-bit color depth for 2.5x faster VNC encoding
echo "Starting low-latency virtual display Xvfb on :99..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 1280x800x16 -ac +extension GLX +render &
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
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 -noxdamage -wait 10 -defer 10 -ncache 10 -async 5 >/dev/null 2>&1 &
sleep 2

# 5. Bind noVNC HTML5 proxy to primary deployment PORT
APP_PORT="${PORT:-${WEBSITES_PORT:-8080}}"
echo "Starting low-latency noVNC web proxy on port ${APP_PORT}..."
websockify --web /usr/share/novnc --heartbeat 30 "${APP_PORT}" localhost:5900 &
sleep 2

echo "Launching DocSummarizer QML Desktop Application..."
exec python run.py

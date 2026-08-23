#!/bin/bash

export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
export QT_QUICK_BACKEND=software
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

# 3. Start virtual Xvfb display
echo "Starting virtual display Xvfb on :99..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render &
sleep 2

# 4. Start Openbox & VNC
echo "Starting Openbox window manager on :99..."
openbox --sm-disable >/dev/null 2>&1 &
sleep 1

echo "Starting VNC server on port 5900..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 -noxdamage -nowf >/dev/null 2>&1 &
sleep 2

# 5. Serve Ultra-Fast Native Web Application on main deployment PORT
APP_PORT="${PORT:-${WEBSITES_PORT:-8080}}"
echo "Starting DocSummarizer Native Web Application on port ${APP_PORT}..."

# Launch QML desktop app in virtual display in background if needed
python run.py >/tmp/qml.log 2>&1 &

# Execute Web Server on primary PORT for 60fps local file picker experience
exec python -m docsummarizer.web_app --port "${APP_PORT}"

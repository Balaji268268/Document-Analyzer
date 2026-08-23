#!/bin/bash
set -e

export DISPLAY=:99

echo "Starting virtual display Xvfb on :99..."
Xvfb :99 -screen 0 1280x800x24 &
sleep 2

echo "Starting Openbox window manager on :99..."
openbox --sm-disable &
sleep 1

echo "Starting VNC server on port 5900..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 &
sleep 2

echo "Starting noVNC HTML5 web proxy on port 8080..."
if command -v websockify >/dev/null 2>&1; then
    websockify --web /usr/share/novnc 8080 localhost:5900 &
elif [ -f "/usr/share/novnc/utils/novnc_proxy" ]; then
    /usr/share/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 8080 &
fi

sleep 2

echo "Launching DocSummarizer Application..."
python run.py

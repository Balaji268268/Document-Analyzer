#!/bin/bash
set -e

export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
export QT_QUICK_BACKEND=software

# Ensure noVNC root defaults to vnc.html so visiting '/' loads the web app interface
if [ -f "/usr/share/novnc/vnc.html" ]; then
    cp /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true
elif [ -f "/usr/share/novnc/vnc_lite.html" ]; then
    cp /usr/share/novnc/vnc_lite.html /usr/share/novnc/index.html 2>/dev/null || true
fi

echo "Starting virtual display Xvfb on :99..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render &
sleep 2

echo "Starting Openbox window manager on :99..."
openbox --sm-disable &
sleep 1

echo "Starting VNC server on port 5900..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 -noxdamage -nowf &
sleep 2

echo "Starting noVNC HTML5 web proxy on port 8080..."
websockify --web /usr/share/novnc 8080 localhost:5900 &
sleep 2

echo "Launching DocSummarizer QML Application..."
python run.py

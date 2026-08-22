#!/bin/bash
set -e

echo "Starting Virtual X11 Display (Xvfb)..."
Xvfb :99 -screen 0 1280x800x24 &
sleep 2

echo "Starting Window Manager (Fluxbox)..."
fluxbox -display :99 &
sleep 1

echo "Starting VNC Server (x11vnc)..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 -quiet &
sleep 1

echo "Starting HTML5 Web Bridge (noVNC / websockify)..."
websockify --web=/usr/share/novnc 7860 localhost:5900 &
sleep 1

echo "Launching PySide6 QML Desktop Application..."
DISPLAY=:99 python run.py

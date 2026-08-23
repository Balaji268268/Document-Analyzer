#!/bin/bash
set -e

echo "Starting virtual display Xvfb on :99..."
Xvfb :99 -screen 0 1280x800x24 &
sleep 1

echo "Starting Openbox window manager..."
openbox &

echo "Starting VNC server on port 5900..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 &
sleep 1

echo "Starting noVNC HTML5 web proxy on port 8080..."
/usr/share/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 8080 &

echo "Launching DocSummarizer Application..."
python run.py

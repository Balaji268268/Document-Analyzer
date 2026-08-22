# Dockerfile for Hugging Face Spaces — Streaming PySide6 QML Desktop App via noVNC
FROM python:3.11-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Install Xvfb, VNC, noVNC, and Qt 6 dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    fluxbox \
    libgl1-mesa-glx \
    libegl1 \
    libdbus-1-3 \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libfontconfig1 \
    libglib2.0-0 \
    tesseract-ocr \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Make start script executable
RUN chmod +x /app/start.sh

# Expose Hugging Face default app port
EXPOSE 7860

# Launch VNC + QML Desktop application
CMD ["/app/start.sh"]

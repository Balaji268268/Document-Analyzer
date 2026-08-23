# Dockerfile for DocSummarizer Web Streaming (Render, DigitalOcean, Azure, Cloud Deployment)
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=xcb

WORKDIR /app

# Install system dependencies: Linux Qt libraries, procps, Xvfb, Openbox, x11vnc, noVNC
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    xvfb \
    x11vnc \
    openbox \
    novnc \
    websockify \
    libegl1 \
    libgl1 \
    libxkbcommon0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python package dependencies including GUI extras (PySide6)
RUN python -m pip install --upgrade pip && \
    python -m pip install -e ".[gui]"

# Expose web streaming port for cloud hosting
EXPOSE 8080

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]

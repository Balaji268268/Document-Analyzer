# Dockerfile for DocSummarizer Web Streaming (Render, DigitalOcean, Azure, Cloud Deployment)
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen
ENV QT_QUICK_BACKEND=software

WORKDIR /app

# Install all Linux Qt/PySide6 dependencies, procps, Xvfb, Openbox, x11vnc, noVNC
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
    libxkbcommon-x11-0 \
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
    libxcb-util1 \
    libx11-xcb1 \
    libsm6 \
    libice6 \
    curl \
    git \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Ollama engine for Linux container hosting
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy project files
COPY . /app

# Install Python package dependencies including GUI extras (PySide6)
RUN python -m pip install --upgrade pip && \
    python -m pip install -e ".[gui]"

# Expose web streaming port for cloud hosting
EXPOSE 8080

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]

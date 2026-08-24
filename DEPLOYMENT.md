# Deployment & Distribution Guide

Complete guide for deploying **DocSummarizer** as a standalone desktop application or a cloud-hosted container.

---

## 🖥️ 1. Native Desktop Executable (PyInstaller)

Build a standalone executable bundle for Windows or Linux:

```bash
# 1. Install packaging dependencies
pip install -e ".[gui,runtime,dev]" pyinstaller

# 2. Build executable package
pyinstaller --noconfirm DocSummarizer.spec
```

- **Windows Output**: `dist/DocSummarizer/DocSummarizer.exe`
- **Linux Output**: `dist/DocSummarizer/DocSummarizer`

---

## 🐳 2. Docker & Container Deployment

DocSummarizer packages a virtual X11 desktop and web server in a single container:

```bash
# Build Docker image
docker build -t docsummarizer .

# Run container on port 8080
docker run -d -p 8080:8080 --name docsummarizer docsummarizer
```

Access the interface at `http://localhost:8080`.

---

## ☁️ 3. Cloud Container Deployment

Deploy the Docker container to any container platform:

### Azure App Service / Container Instances
1. Create an **App Service (Linux Container)** or **Azure Container Instance (ACI)**.
2. Connect your GitHub repository (`Balaji268268/Document-Analyzer`).
3. Set environment variable `WEBSITES_PORT=8080`.

### Render / DigitalOcean App Platform / AWS App Runner
1. Create a **Web Service** from GitHub.
2. Select **Docker** environment.
3. Configure HTTP Port: `8080`.

---

## 🚀 4. Automated GitHub Releases (CI/CD)

The repository automatically builds and attaches binaries to GitHub releases on semver tags:

```bash
git tag v2.0.4
git push origin v2.0.4
```

The GitHub Actions workflow compiles and uploads `DocSummarizer-windows-x64.zip` and `DocSummarizer-linux-x64.zip` to the Releases tab.

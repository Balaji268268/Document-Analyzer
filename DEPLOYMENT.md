# Desktop Deployment & Release Guide — DocSummarizer

Technical guide for building, packaging, and distributing **DocSummarizer** as a standalone native desktop application for Windows and Linux.

---

## 🖥️ 1. Local Executable Packaging (PyInstaller)

DocSummarizer uses `PyInstaller` with a customized spec configuration to bundle Python, PySide6, QML components, and binary dependencies.

### Step 1: Install Build Requirements
```bash
pip install -e ".[gui,runtime,dev]" pyinstaller
```

### Step 2: Build Desktop Package
```bash
pyinstaller --noconfirm --onedir --windowed --name "DocSummarizer" --paths "src" run.py
```

- **Output Path**: `dist/DocSummarizer/`
- **Windows Executable**: `dist/DocSummarizer/DocSummarizer.exe`
- **Linux Executable**: `dist/DocSummarizer/DocSummarizer`

---

## 🚀 2. Automated GitHub Releases (CI/CD)

The repository includes an automated GitHub Actions release workflow ([`.github/workflows/release.yml`](file:///.github/workflows/release.yml)).

### Triggering an Automated Release

1. **Tag your release** with a semver tag:
   ```bash
   git tag v2.0.0
   git push origin v2.0.0
   ```

2. **GitHub Actions** will automatically:
   - Run tests and static analysis.
   - Build the standalone executable on Windows and Linux runners.
   - Create a zip archive (`DocSummarizer-windows-x64.zip` / `DocSummarizer-linux-x64.zip`).
   - Attach the binary assets directly to your **[GitHub Release Page](https://github.com/Balaji268268/Document-Analyzer/releases)**.

---

## 📦 3. PyPI Package Distribution

To allow users to install DocSummarizer directly via `pip`:

```bash
# Build wheel and source distribution
python -m pip install build
python -m build

# Publish to PyPI
python -m pip install twine
python -m twine upload dist/*
```

Users can then launch the app on any OS with:
```bash
pip install docsummarizer
docsummarizer
```

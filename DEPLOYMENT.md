# Deployment Guide — Document-Analyzer

Complete technical guide for deploying **Document-Analyzer** to **Vercel**, **Render**, **Hugging Face**, and **Desktop Executable Releases**.

---

## ⚡ 1. Deploying on Vercel (Python Serverless API)

[Vercel](https://vercel.com) supports Python Serverless Functions natively using `@vercel/python`.

### Step 1: Repository Structure for Vercel
Ensure your repository includes a `vercel.json` configuration and an `api/index.py` entry point:

```text
Document-Analyzer/
├── vercel.json         # Vercel routing & build configuration
├── api/
│   └── index.py        # Python serverless function entry point
├── src/                # Core application source
└── pyproject.toml      # Package dependencies
```

### Step 2: Vercel Configuration (`vercel.json`)
```json
{
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

### Step 3: Vercel Python Function (`api/index.py`)
```python
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

# Add src layout to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docsummarizer.document_parser import analyze_document, extract_text


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "status": "online",
            "app": "Document-Analyzer API",
            "version": "2.0.0",
            "supported_formats": [".pdf", ".docx", ".rtf", ".txt", ".md", ".png", ".jpg"],
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))
```

### Step 4: Deploy to Vercel

#### Option A: Via Vercel Web Dashboard (Recommended)
1. Log in to **[vercel.com/new](https://vercel.com/new)** using your GitHub account (`Balaji268268`).
2. Select your repository: **`Balaji268268/Document-Analyzer`**.
3. Keep default settings and click **Deploy**.
4. Vercel will build the deployment and assign a live URL:  
   👉 **`https://document-analyzer-balaji268268.vercel.app`**

#### Option B: Via Vercel CLI
```bash
# Install Vercel CLI globally
npm install -g vercel

# Log in and deploy
vercel login
vercel --prod
```

---

## 🌐 2. Deploying on Render (Web Service)

1. Navigate to **[dashboard.render.com](https://dashboard.render.com)**.
2. Select **New +** → **Web Service**.
3. Connect repository `Balaji268268/Document-Analyzer`.
4. Set Build Command: `pip install -e ".[dev,runtime]"`
5. Click **Create Web Service**.

---

## 🤗 3. Deploying on Hugging Face Spaces

1. Create a new Space at **[huggingface.co/new-space](https://huggingface.co/new-space)**.
2. Select **Space SDK: Gradio** or **Docker**.
3. Push your repository:
   ```bash
   git remote add space https://huggingface.co/spaces/Balaji268268/Document-Analyzer
   git push space master
   ```

---

## 💾 4. Desktop Executable Distribution (.exe)

For desktop distribution without server hosting:

```bash
# Build single-file desktop executable
pyinstaller DocSummarizer.spec
```

The compiled binary will be placed in `dist/DocSummarizer.exe` (Windows) or `dist/DocSummarizer` (Linux).

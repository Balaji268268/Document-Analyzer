# 🔷 Microsoft Azure Deployment Guide for DocSummarizer

Deploy **DocSummarizer** live on **Microsoft Azure** using **Azure App Service** or **Azure Container Instances (ACI)** for a public production URL (`https://<your-app-name>.azurewebsites.net`).

---

## Method 1: Azure App Service (Linux Container / Continuous Deployment)

Azure App Service connects directly to your GitHub repository (`Balaji268268/Document-Analyzer`) and automatically builds the included [`Dockerfile`](file:///d:/Doc-Summarizer/Dockerfile).

### Step-by-Step Instructions:

1. **Log in to Azure Portal**:
   - Go to [portal.azure.com](https://portal.azure.com).

2. **Create a Web App**:
   - Search for **App Services** in the top search bar and click **Create → Web App**.

3. **Basics Tab**:
   - **Subscription**: Select your Azure subscription.
   - **Resource Group**: Create new (e.g. `docsummarizer-rg`).
   - **Name**: Enter a unique app name (e.g., `docsummarizer-web`).
   - **Publish**: Select **Docker Container**.
   - **Operating System**: **Linux**.
   - **Region**: Choose your nearest Azure region.
   - **Pricing Plan**: Select **Free F1** or **Basic B1**.

4. **Docker Tab**:
   - **Options**: Single Container.
   - **Image Source**: **GitHub Actions** or **Docker Hub**.
   - Select repository **`Balaji268268/Document-Analyzer`** and branch `master`.

5. **Configure Port Environment Variable**:
   - In your new Web App, go to **Settings → Environment variables** (or **Configuration**).
   - Add a new application setting:
     - **Name**: `WEBSITES_PORT`
     - **Value**: `8080`
   - Click **Apply / Save**.

6. **Access Your Live Azure URL**:
   - Open your web browser to:
     `https://<your-app-name>.azurewebsites.net`

---

## Method 2: Azure Container Instances (ACI via Azure CLI)

Run DocSummarizer directly on Azure Container Instances using the Azure CLI:

```bash
# 1. Create a Resource Group
az group create --name docsummarizer-rg --location eastus

# 2. Deploy Container Instance
az container create \
  --resource-group docsummarizer-rg \
  --name docsummarizer-app \
  --image ghcr.io/balaji268268/document-analyzer:latest \
  --dns-name-label docsummarizer-live \
  --ports 8080
```

### Access Your ACI App:
- Open `http://docsummarizer-live.eastus.azurecontainer.io:8080` in your web browser!

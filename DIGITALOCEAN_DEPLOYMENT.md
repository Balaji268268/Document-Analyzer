# 🌊 DigitalOcean Deployment Guide for DocSummarizer

Deploy **DocSummarizer** live on **DigitalOcean** with an instant public web URL (`https://<your-app>.ondigitalocean.app`) or on a DigitalOcean Droplet VPS.

---

## Method 1: DigitalOcean App Platform (Automated & Recommended)

DigitalOcean App Platform automatically builds your repository from GitHub using the included [`Dockerfile`](file:///d:/Doc-Summarizer/Dockerfile) and hosts your app on a live HTTPS domain.

### Step-by-Step Instructions:

1. **Log in to DigitalOcean**:
   - Go to [cloud.digitalocean.com](https://cloud.digitalocean.com) and click **Apps** in the left sidebar.

2. **Create New App**:
   - Click **Create App**.
   - Choose **GitHub** as the source code repository.
   - Select repository: **`Balaji268268/Document-Analyzer`** and branch `master`.

3. **Configure Resource**:
   - DigitalOcean will detect the **`Dockerfile`** automatically.
   - Set HTTP Port: **`8080`**.
   - Resource Size: Select **Basic** or **General Purpose** ($5/mo–$12/mo).

4. **Deploy**:
   - Click **Launch App**.
   - DigitalOcean builds the container and provides your live public web URL:
     `https://document-analyzer-xxxxx.ondigitalocean.app`

5. **Access the App**:
   - Open your live DigitalOcean URL in any web browser to use **DocSummarizer**!

---

## Method 2: DigitalOcean Droplet VPS (Ubuntu Server)

If you prefer deploying on a dedicated DigitalOcean Droplet VPS ($4/mo–$6/mo) with full root access:

### Step-by-Step Instructions:

1. **Create a Droplet**:
   - In DigitalOcean Cloud Console, click **Create → Droplets**.
   - Select **Ubuntu 22.04 LTS (x64)**.
   - Plan: **Basic** ($4/mo or $6/mo).

2. **Connect via SSH**:
   ```bash
   ssh root@<YOUR_DROPLET_IP>
   ```

3. **Install Docker**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

4. **Clone and Run Container**:
   ```bash
   git clone https://github.com/Balaji268268/Document-Analyzer.git
   cd Document-Analyzer
   docker build -t docsummarizer-web .
   docker run -d -p 80:8080 --name docsummarizer --restart unless-stopped docsummarizer-web
   ```

5. **Access Your Live Website**:
   - Open `http://<YOUR_DROPLET_IP>` in any web browser!

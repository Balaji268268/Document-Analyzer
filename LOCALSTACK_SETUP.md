# 🧪 LocalStack AWS Emulation & Local Cloud Testing Guide

Run **DocSummarizer** alongside **LocalStack** locally on your machine to test AWS cloud services (S3 buckets, API Gateway, Lambda) without needing real AWS credentials or incurring costs.

---

## Prerequisites

- **Docker Desktop** installed and running on your computer.

---

## 🚀 Quickstart: Running DocSummarizer + LocalStack

1. **Start Services with Docker Compose**:
   Run the following command in the project directory:
   ```powershell
   docker-compose up -d
   ```

2. **Verify Running Services**:
   ```powershell
   docker-compose ps
   ```
   You will see:
   - `docsummarizer-web` running on port `8080`.
   - `docsummarizer-localstack` running on port `4566` (LocalStack AWS Edge).

3. **Access the Local Web App**:
   - Open your browser to **`http://localhost:8080`**.

---

## 🛠️ Interacting with LocalStack AWS Services

LocalStack emulates AWS endpoints on `http://localhost:4566`.

### Example: Create a Local AWS S3 Bucket
Using AWS CLI pointing to LocalStack endpoint:
```powershell
aws --endpoint-url=http://localhost:4566 s3 mb s3://docsummarizer-documents
```

### Example: Upload a Document to Local S3
```powershell
aws --endpoint-url=http://localhost:4566 s3 cp sample.pdf s3://docsummarizer-documents/
```

### Example: List Local S3 Buckets
```powershell
aws --endpoint-url=http://localhost:4566 s3 ls
```

---

## 🛑 Stopping Services

To stop LocalStack and DocSummarizer containers:
```powershell
docker-compose down
```

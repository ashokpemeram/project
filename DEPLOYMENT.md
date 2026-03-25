# Deployment Guide - Medical Image Protection System

## 📋 Pre-Deployment Checklist

- [ ] Test application locally (both frontend and backend)
- [ ] Verify model is loading correctly
- [ ] Update environment variables for production
- [ ] Set up domain name (if applicable)
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging
- [ ] Implement rate limiting
- [ ] Add authentication (if required)

---

## 🐳 Docker Deployment (Recommended)

### Backend Docker Setup

1. **Create `backend/Dockerfile`:**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p model/weights storage/protected uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Create `backend/.dockerignore`:**

```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.git
.gitignore
uploads/*
!uploads/.gitkeep
```

3. **Build and run:**

```bash
cd backend
docker build -t medical-image-backend .
docker run -p 8000:8000 -v $(pwd)/model/weights:/app/model/weights medical-image-backend
```

### Frontend Docker Setup

1. **Create `frontend/Dockerfile`:**

```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

2. **Create `frontend/nginx.conf`:**

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Build and run:**

```bash
cd frontend
docker build -t medical-image-frontend .
docker run -p 80:80 medical-image-frontend
```

### Docker Compose (Full Stack)

**Create `docker-compose.yml` in project root:**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./model/weights:/app/model/weights
      - ./backend/uploads:/app/uploads
    environment:
      - DEVICE=cpu
      - MODEL_PATH=/app/model/weights/model.pth
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    restart: unless-stopped
```

**Run the full stack:**

```bash
docker-compose up -d
```

---

## ☁️ Cloud Deployment Options

### 1. AWS Deployment

#### Backend on AWS EC2

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Clone your repository
git clone your-repo-url
cd project/backend

# Run with Docker
docker build -t backend .
docker run -d -p 8000:8000 backend
```

#### Frontend on AWS S3 + CloudFront

```bash
# Build frontend
cd frontend
npm run build

# Install AWS CLI
npm install -g aws-cli

# Deploy to S3
aws s3 sync build/ s3://your-bucket-name

# Configure CloudFront for CDN
```

### 2. Google Cloud Platform

#### Backend on Cloud Run

```bash
# Install gcloud CLI
gcloud init

# Build and deploy
cd backend
gcloud builds submit --tag gcr.io/your-project/backend
gcloud run deploy backend --image gcr.io/your-project/backend --platform managed
```

#### Frontend on Firebase Hosting

```bash
cd frontend
npm run build

# Install Firebase CLI
npm install -g firebase-tools

# Initialize and deploy
firebase init hosting
firebase deploy
```

### 3. Heroku Deployment

#### Backend on Heroku

```bash
# Install Heroku CLI
heroku login

# Create app
cd backend
heroku create your-app-name

# Add Procfile
echo "web: uvicorn app:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git push heroku main
```

#### Frontend on Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

cd frontend
vercel --prod
```

### 4. DigitalOcean App Platform

1. Connect your GitHub repository
2. Select backend and frontend as separate components
3. Configure build commands:
   - Backend: `pip install -r requirements.txt`
   - Frontend: `npm run build`
4. Set environment variables
5. Deploy

---

## 🔒 Production Configuration

### Backend Production Settings

**Update `backend/config.py`:**

```python
import os

# Production settings
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')

# CORS
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://yourdomain.com').split(',')

# File upload limits
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10485760))
```

### Frontend Production Settings

**Update `frontend/.env.production`:**

```env
REACT_APP_API_URL=https://api.yourdomain.com
```

---

## 🔐 Security Best Practices

1. **Enable HTTPS:**
   - Use Let's Encrypt for free SSL certificates
   - Configure SSL in Nginx/Apache

2. **Add Rate Limiting:**

```python
# backend/app.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/protect-image")
@limiter.limit("10/minute")
async def protect_image(...):
    ...
```

3. **Add Authentication:**

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/protect-image")
async def protect_image(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify token
    ...
```

4. **Environment Variables:**
   - Never commit `.env` files
   - Use secrets management (AWS Secrets Manager, etc.)

---

## 📊 Monitoring & Logging

### Add Logging

```python
# backend/app.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Health Check Endpoint

Already implemented at `/api/health` - use for monitoring services.

---

## 🚀 Performance Optimization

1. **Backend:**
   - Use Gunicorn with multiple workers
   - Enable response compression
   - Cache model in memory (already implemented)

2. **Frontend:**
   - Enable gzip compression
   - Use CDN for static assets
   - Implement lazy loading

---

## 📈 Scaling Considerations

1. **Horizontal Scaling:**
   - Use load balancer (AWS ELB, Nginx)
   - Deploy multiple backend instances
   - Share model file via network storage

2. **Vertical Scaling:**
   - Upgrade to GPU instances for faster inference
   - Increase memory for larger models

---

## 🆘 Rollback Strategy

```bash
# Docker rollback
docker ps  # Find container ID
docker stop <container-id>
docker run <previous-image>

# Git rollback
git revert HEAD
git push origin main
```

---

## ✅ Post-Deployment Verification

1. Test API endpoints: `curl https://api.yourdomain.com/api/health`
2. Upload test image through UI
3. Check logs for errors
4. Monitor resource usage
5. Test from different locations/devices

---

**Need help? Check the main README.md for troubleshooting tips.**

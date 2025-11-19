# ORCHA - VPS Deployment Guide

## System Requirements

- **OS**: Ubuntu 20.04+ / Debian 11+
- **Python**: 3.12.x
- **RAM**: Minimum 2GB (4GB+ recommended)
- **Storage**: 10GB+ free space

## Core Dependencies

### 1. PostgreSQL 14+
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Create database:
```bash
sudo -u postgres psql
CREATE DATABASE orcha_db;
CREATE USER liwa WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE orcha_db TO liwa;
\q
```

### 2. Redis 6+
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Python & System Tools
```bash
sudo apt install python3.12 python3.12-venv python3-pip
```

## Application Setup

### 1. Clone & Setup
```bash
cd /opt
git clone <your-repo-url> orcha
cd orcha
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Environment Configuration
Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://liwa:your_secure_password@localhost:5432/orcha_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security - CHANGE THIS
JWT_SECRET_KEY=generate-a-secure-32-char-minimum-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External Services (configure your endpoints)
LMSTUDIO_URL=http://your-lm-studio-host:1234
LMSTUDIO_VISION_MODEL=llava-v1.6-34b
GEMMA_MODEL=google/gemma-3-12b
OCR_SERVICE_URL=http://localhost:8001
RAG_SERVICE_URL=http://localhost:8002

# Timeouts
LM_TIMEOUT=500
RAG_TIMEOUT=15
OCR_TIMEOUT=60
```

### 3. Initialize Database
```bash
python init_database.py
```

### 4. Run with Uvicorn
Development:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Production (systemd service):
```bash
sudo nano /etc/systemd/system/orcha.service
```

```ini
[Unit]
Description=ORCHA Orchestrator API
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/orcha
Environment="PATH=/opt/orcha/venv/bin"
ExecStart=/opt/orcha/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable & start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable orcha
sudo systemctl start orcha
```

## Firewall & Security

```bash
# Open required ports
sudo ufw allow 8000/tcp  # API
sudo ufw allow 22/tcp    # SSH
sudo ufw enable
```

## Nginx Reverse Proxy (Optional but Recommended)

```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/orcha
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/orcha /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Python Dependencies (requirements.txt)

- fastapi>=0.104.0
- uvicorn[standard]>=0.24.0
- httpx>=0.25.0
- sqlalchemy>=2.0.0
- asyncpg>=0.29.0
- alembic>=1.12.0
- pydantic>=2.0.0
- python-dotenv==1.0.0
- redis==4.6.0
- prometheus-client==0.16.0
- loguru==0.7.0
- PyPDF2==3.0.1
- bcrypt==4.0.1
- passlib[bcrypt]==1.7.4
- python-jose[cryptography]==3.3.0
- python-multipart==0.0.6
- email-validator==2.0.0

## External Services (Configure Separately)

1. **LM Studio**: Install on separate server/local network (http://your-host:1234)
2. **OCR Service**: PaddleOCR service (http://your-host:8001)
3. **RAG Service**: Document retrieval service (http://your-host:8002)

## Monitoring & Logs

Check logs:
```bash
sudo journalctl -u orcha -f
```

Check status:
```bash
sudo systemctl status orcha
```

## Maintenance

Restart service:
```bash
sudo systemctl restart orcha
```

Update code:
```bash
cd /opt/orcha
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart orcha
```









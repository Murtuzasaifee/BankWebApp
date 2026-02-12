# Good Bank FastAPI - EC2 Deployment Guide

## Prerequisites

- AWS Account with EC2 access
- SSH key pair (`.pem` file)
- Project files ready for upload

---

## 1. Launch EC2 Instance

### AWS Console Steps

1. Go to **EC2 Dashboard** > **Launch Instance**
2. **Name**: `GoodBank-Chat-Server`
3. **AMI**: Amazon Linux 2023 (Free Tier eligible)
4. **Instance Type**: `t2.micro` (Free Tier - 750 hrs/month for 12 months)
5. **Key Pair**: Select or create a key pair (download the `.pem` file)
6. **Security Group**: Create new with these inbound rules:

| Type       | Port | Source    | Description            |
|------------|------|-----------|------------------------|
| SSH        | 22   | My IP     | SSH access             |
| Custom TCP | 8000 | 0.0.0.0/0| Application access     |

7. **Storage**: 8 GB gp3 (default, free tier)
8. Click **Launch Instance**

### Estimated Cost
- **Free Tier**: $0/month (first 12 months, t2.micro)
- **After Free Tier**: ~$9.30/month (t2.micro, us-east-1)

---

## 2. Connect to EC2

```bash
# Set permissions on key file
chmod 400 your-key.pem

# Connect via SSH
ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

---

## 3. Install Python 3 on EC2

```bash
# Update system packages
sudo yum update -y

# Install Python 3 and pip
sudo yum install python3 python3-pip -y

# Verify installation
python3 --version
pip3 --version
```

---

## 4. Upload Project Files

From your **local machine**, upload the project:

```bash
# Upload entire project folder
scp -i your-key.pem -r /path/to/GoodBank ec2-user@YOUR_EC2_PUBLIC_IP:/home/ec2-user/goodbank
```

### Files to Upload

```
goodbank/
├── .env                  # Your configured environment file
├── .env.example
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── session.py
│   ├── dependencies.py
│   ├── query_agent.py
│   ├── demo_data.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── loan.py
│   │   └── health.py
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/script.js
│   └── templates/
│       └── index.html
└── deployment_scripts/
    ├── deploy.sh
    ├── manage.sh
    └── goodbank.service
```

---

## 5. Configure Environment

On the EC2 instance:

```bash
cd /home/ec2-user/goodbank

# If you haven't uploaded .env, create from template
cp .env.example .env
nano .env
```

### Critical .env Settings for EC2

```ini
# MUST be 0.0.0.0 for EC2 (not 127.0.0.1)
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Set to false for production
DEBUG_MODE=false

# Fill in your actual credentials
API_KEY=your_api_key
WORKSPACE_ID=your_workspace_id
PLATFORM_USERNAME=your_username
PLATFORM_PASSWORD=your_password
ASSET_VERSION_ID=your_asset_id
```

---

## 6. Deploy Application

### Option A: Quick Deploy Script

```bash
cd /home/ec2-user/goodbank
bash deployment_scripts/deploy.sh
```

### Option B: Manual Setup

```bash
cd /home/ec2-user/goodbank

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Update SERVER_HOST in .env
sed -i 's/SERVER_HOST=127.0.0.1/SERVER_HOST=0.0.0.0/' .env

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 7. Running the Application

### Manual Start (foreground)

```bash
cd /home/ec2-user/goodbank
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Background Start (using manage script)

```bash
bash deployment_scripts/manage.sh start
bash deployment_scripts/manage.sh status
bash deployment_scripts/manage.sh logs     # View logs
bash deployment_scripts/manage.sh stop
bash deployment_scripts/manage.sh restart
```

### Systemd Service (auto-start on reboot)

```bash
# Copy service file
sudo cp deployment_scripts/goodbank.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable goodbank
sudo systemctl start goodbank

# Check status
sudo systemctl status goodbank

# View logs
sudo journalctl -u goodbank -f
```

---

## 8. Verify Deployment

```bash
# Get your EC2 public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Test health endpoint
curl http://YOUR_EC2_PUBLIC_IP:8000/health

# Test config endpoint
curl http://YOUR_EC2_PUBLIC_IP:8000/config
```

Open in browser: `http://YOUR_EC2_PUBLIC_IP:8000`

---

## 9. Updating Code

### Update Specific Files

```bash
# From local machine
scp -i your-key.pem app/routers/chat.py ec2-user@YOUR_EC2_IP:/home/ec2-user/goodbank/app/routers/

# On EC2, restart the app
bash deployment_scripts/manage.sh restart
# Or with systemd:
sudo systemctl restart goodbank
```

### Replace Entire App

```bash
# From local machine
scp -i your-key.pem -r app/ ec2-user@YOUR_EC2_IP:/home/ec2-user/goodbank/

# On EC2
bash deployment_scripts/manage.sh restart
```

### Update Dependencies

```bash
# Upload new requirements.txt
scp -i your-key.pem requirements.txt ec2-user@YOUR_EC2_IP:/home/ec2-user/goodbank/

# On EC2
cd /home/ec2-user/goodbank
source venv/bin/activate
pip install -r requirements.txt
bash deployment_scripts/manage.sh restart
```

---

## 10. Troubleshooting

### App Won't Start

```bash
# Check logs
tail -50 /home/ec2-user/goodbank/app.log
tail -50 /home/ec2-user/goodbank/app-error.log

# Check if port is in use
sudo lsof -i :8000

# Verify .env exists and is correct
cat /home/ec2-user/goodbank/.env
```

### Can't Access from Browser

1. Check Security Group has port 8000 open to `0.0.0.0/0`
2. Verify `SERVER_HOST=0.0.0.0` in `.env`
3. Check the app is running: `bash deployment_scripts/manage.sh status`
4. Test locally on EC2: `curl http://localhost:8000/health`

### Token/Auth Errors

```bash
# Check credentials in .env
grep -E "API_KEY|PLATFORM_USERNAME|PLATFORM_PASSWORD" .env

# Check app logs for token refresh errors
grep -i "token\|auth\|401" /home/ec2-user/goodbank/app.log
```

### Python/Package Issues

```bash
# Verify Python version
python3 --version   # Should be 3.8+

# Reinstall packages
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start app | `bash deployment_scripts/manage.sh start` |
| Stop app | `bash deployment_scripts/manage.sh stop` |
| Restart app | `bash deployment_scripts/manage.sh restart` |
| View status | `bash deployment_scripts/manage.sh status` |
| View logs | `bash deployment_scripts/manage.sh logs` |
| Health check | `curl http://localhost:8000/health` |
| Start with systemd | `sudo systemctl start goodbank` |
| Stop with systemd | `sudo systemctl stop goodbank` |
| Enable auto-start | `sudo systemctl enable goodbank` |

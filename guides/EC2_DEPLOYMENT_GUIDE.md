# Banking Web Application with FastAPI - EC2 Deployment Guide

## Prerequisites

- AWS Account with EC2 access
- SSH key pair (`.pem` file)
- Project files ready for upload

---

## 1. Launch EC2 Instance

### AWS Console Steps

1. Go to **EC2 Dashboard** > **Launch Instance**
2. **Name**: `BankApp-Chat-Server`
3. **AMI**: Amazon Linux 2023 (Free Tier eligible)
4. **Instance Type**: `t2.micro` (Free Tier - 750 hrs/month for 12 months)
5. **Key Pair**: Select or create a key pair (download the `.pem` file)
6. **Security Group**: Create new with these inbound rules:

| Type       | Port | Source    | Description            |
|------------|------|-----------|------------------------|
| SSH        | 22   | My IP     | SSH access             |
| Custom TCP | 8000 | 0.0.0.0/0| Application access     |

7. **Storage**: 8 GB gp3 (default, free tier)
8. **Advanced Details** > **User Data**: Expand this section and paste the following script to install dependencies automatically on boot:

   ```bash
   #!/bin/bash
   yum update -y
   yum install -y python3 python3-pip git screen
   ```

9. Click **Launch Instance**

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

> **Note**: If you included the User Data script in Step 1, these packages will install automatically on first boot. You can skip the `yum` commands and directly verify the installation.

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
scp -i your-key.pem -r /path/to/BankApp ec2-user@YOUR_EC2_PUBLIC_IP:/home/ec2-user/bankapp
```

### Files to Upload

```
bankapp/
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
    └── bankapp.service
```

---

## 5. Configure Environment

On the EC2 instance:

```bash
cd /home/ec2-user/bankapp

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
ENVIRONMENT=production
SECRET_KEY=your_secure_random_key_here
TENANT=your_tenant
API_KEY=your_api_key
WORKSPACE_ID=your_workspace_id
PLATFORM_USERNAME=your_username
PLATFORM_PASSWORD=your_password
ASSET_VERSION_ID=your_asset_id
ASSET_VERSION_ID_LOGGED_IN=your_logged_in_asset_id
LOAN_AGENT_ASSET_ID=your_loan_agent_asset_id
```

---

## 6. Deploy Application

### Option A: Quick Deploy Script

```bash
cd /home/ec2-user/bankapp
bash deployment_scripts/deploy.sh
```

### Option B: Manual Setup

```bash
cd /home/ec2-user/bankapp

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
cd /home/ec2-user/bankapp
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
sudo cp deployment_scripts/bankapp.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable bankapp
sudo systemctl start bankapp

# Check status
sudo systemctl status bankapp

# View logs
sudo journalctl -u bankapp -f
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

## 9. Updating Code (Fast Sync)

The easiest and most robust way to push changes from your local machine to your EC2 instance is by using the `sync_to_ec2.sh` helper script. It uses `rsync` to only upload modified files, meaning deployments are extremely fast. Crucially, it automatically respects your `.gitignore` file, so development items (like `.env`, `venv/`, `__pycache__`, formatting configs, etc.) are never accidentally uploaded to your production server.

### Basic Code Update
From your local machine project directory:
```bash
# Basic sync (using default SSH configuration)
bash deployment_scripts/sync_to_ec2.sh ec2-user@YOUR_EC2_IP /home/ec2-user/bankapp

# Sync using a specific AWS PEM key
bash deployment_scripts/sync_to_ec2.sh -i your-key.pem ec2-user@YOUR_EC2_IP /home/ec2-user/bankapp
```
*Note: After a basic sync, you will still need to manually restart the application on the EC2 instance.*

### Update Code AND Automatically Redeploy (Recommended)
You can append the `--redeploy` flag to the script. This flag synchronizes your files securely and immediately logs into your EC2 instance to restart your application automatically.

```bash
bash deployment_scripts/sync_to_ec2.sh --redeploy -i your-key.pem ec2-user@YOUR_EC2_IP /home/ec2-user/bankapp
```

### Manual Restart Command (If not using `--redeploy`)
If you chose the basic update, remember to reboot the app manually on EC2:
```bash
# On EC2 instance:
bash deployment_scripts/manage.sh restart

# Or if you use systemd:
sudo systemctl restart bankapp
```

### Dependency Updates
By default, the sync script will push a modified `requirements.txt` file. However, you must tell the remote server to install the new packages.
```bash
# 1. First sync files securely
bash deployment_scripts/sync_to_ec2.sh -i your-key.pem ec2-user@YOUR_EC2_IP /home/ec2-user/bankapp

# 2. Then SSH into the EC2 node
ssh -i your-key.pem ec2-user@YOUR_EC2_IP

# 3. Update the Python env
cd /home/ec2-user/bankapp
source venv/bin/activate
pip install -r requirements.txt
bash deployment_scripts/manage.sh restart
```

---

## 10. Troubleshooting

### App Won't Start

```bash
# Check logs
tail -50 /home/ec2-user/bankapp/app.log
tail -50 /home/ec2-user/bankapp/app-error.log

# Check if port is in use
sudo lsof -i :8000

# Verify .env exists and is correct
cat /home/ec2-user/bankapp/.env
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
grep -i "token\|auth\|401" /home/ec2-user/bankapp/app.log
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
| Start with systemd | `sudo systemctl start bankapp` |
| Stop with systemd | `sudo systemctl stop bankapp` |
| Enable auto-start | `sudo systemctl enable bankapp` |

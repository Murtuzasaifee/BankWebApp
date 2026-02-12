# Good Bank Chat Application - AWS EC2 Deployment Guide

## 🎯 Recommended: EC2 t2.micro (FREE TIER)

For a demo with 2-3 users, **EC2 t2.micro** is the cheapest and easiest option:
- **Cost**: FREE for 12 months (750 hours/month free tier)
- **After free tier**: ~$8.50/month
- **Setup time**: ~15 minutes

---

## 📁 Files You'll Need

Your application files + scripts I provided:
```
chat_app_aws/
├── app.py
├── config.py          → Replace with config_ec2.py (or edit SERVER_HOST)
├── query_agent.py
├── requirements.txt
├── deploy.sh          → Auto-setup script (I provided)
├── manage.sh          → App management script (I provided)
├── Good Bank.service        → Optional: for auto-restart (I provided)
└── templates/
    └── index.html
```

---

## 🚀 Step-by-Step Deployment

### Step 1: Launch EC2 Instance (AWS Console)

1. **Go to EC2 Dashboard**
   - Login to AWS Console → Search "EC2" → Click "Launch Instance"

2. **Configure Instance**
   
   | Setting | Value |
   |---------|-------|
   | **Name** | `Good Bank-Chat-Demo` |
   | **AMI** | Amazon Linux 2023 AMI (Free tier eligible) |
   | **Instance Type** | `t2.micro` (Free tier eligible) |
   | **Key Pair** | Create new → Download `.pem` file (SAVE THIS!) |

3. **Network Settings** → Click "Edit"
   - ✅ Allow SSH traffic from: My IP
   - ✅ Allow HTTP traffic from: Anywhere (0.0.0.0/0)
   - ✅ Allow HTTPS traffic from: Anywhere (0.0.0.0/0)
   - Click **"Add security group rule"**:
     - Type: Custom TCP
     - Port: **8000**
     - Source: Anywhere (0.0.0.0/0)

4. **Advanced Details** → Scroll down to **"User data"** → Paste content of `ec2-setup.sh`:
   ```bash
   #!/bin/bash
   yum update -y
   yum install -y python3 python3-pip git screen
   mkdir -p /home/ec2-user/chat_app_aws/templates
   chown -R ec2-user:ec2-user /home/ec2-user/chat_app_aws
   ```
   *(This auto-installs dependencies when instance first boots)*

5. Click **"Launch Instance"**

---

### Step 2: Wait for Instance to Start

1. Click on the Instance ID
2. Wait until **Instance State** shows "Running"
3. Wait until **Status Checks** shows "2/2 checks passed" (~2 minutes)
4. Copy the **Public IPv4 address** (e.g., `3.15.123.45`)

---

### Step 3: Prepare Your Files Locally

Before uploading, organize all files in one folder:

```
chat_app_aws/
├── app.py
├── config.py          ← Use config_ec2.py or edit SERVER_HOST
├── query_agent.py
├── requirements.txt
├── deploy.sh          ← From files I provided
├── manage.sh          ← From files I provided
├── Good Bank.service        ← From files I provided (optional)
└── templates/
    └── index.html
```

**⚠️ CRITICAL: Either:**
- Replace your `config.py` with `config_ec2.py` (rename it to config.py), OR
- Edit line ~68 in your config.py:
  ```python
  SERVER_HOST = '0.0.0.0'  # Changed from '127.0.0.1'
  ```

---

### Step 4: Upload Files to EC2

**Option A: Using SCP (Recommended)**

On your local machine terminal:
```bash
# Navigate to parent folder of your app
cd /path/to/parent/folder

# Upload entire folder
scp -i your-key.pem -r chat_app_aws ec2-user@YOUR_PUBLIC_IP:~
```

On Windows for setting the permission of pem file:
```bash
# Reset all the permission
icacls.exe "goodbank_chat_app" /reset

# Grant Access to yourself
icacls.exe "goodbank_chat_app" /grant:r "$($env:username):(R)"

# Remove everyone else
icacls.exe "goodbank_chat_app" /inheritance:r

```

**Option B: Using FileZilla (GUI)**
1. Open FileZilla
2. Host: `sftp://YOUR_PUBLIC_IP`
3. Username: `ec2-user`
4. Key file: Your `.pem` file
5. Drag and drop your `chat_app_aws` folder

---

### Step 5: Connect to EC2 and Run deploy.sh

**Connect via AWS Console (Easiest):**
1. Select your instance → Click "Connect"
2. Choose "EC2 Instance Connect" → Click "Connect"

**Or via SSH:**
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@YOUR_PUBLIC_IP
```

**Run the deploy script:**
```bash
cd ~/chat_app_aws
chmod +x deploy.sh manage.sh
./deploy.sh
```

✅ `deploy.sh` automatically:
- Creates Python virtual environment
- Installs all dependencies from requirements.txt
- Fixes SERVER_HOST if still set to 127.0.0.1
- Shows you the access URL

---

### Step 6: Start the Application Using manage.sh

```bash
./manage.sh start
```

✅ That's it! The script will:
- Start the app in background
- Show you the public URL
- Save logs to app.log

**Other manage.sh commands:**
```bash
./manage.sh status   # Check if app is running
./manage.sh stop     # Stop the app
./manage.sh restart  # Restart the app
./manage.sh logs     # View live logs (Ctrl+C to exit)
```

---

### Step 7: Access Your Application

Open browser and go to:
```
http://YOUR_PUBLIC_IP:8000
```

Example: `http://3.15.123.45:8000`

---

## 📋 Summary: All Commands You'll Run on EC2

```bash
# 1. Navigate to app folder
cd ~/chat_app_aws

# 2. Make scripts executable
chmod +x deploy.sh manage.sh

# 3. Run setup (first time only)
./deploy.sh

# 4. Start the app
./manage.sh start

# Done! Access at http://YOUR_IP:8000
```

---

## 🔧 Optional: Auto-Start on Reboot (Using Good Bank.service)

If you want the app to automatically restart when EC2 reboots:

```bash
# Copy service file to systemd
sudo cp Good Bank.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable Good Bank
sudo systemctl start Good Bank

# Check status
sudo systemctl status Good Bank
```

After this, use systemctl instead of manage.sh:
```bash
sudo systemctl start Good Bank
sudo systemctl stop Good Bank
sudo systemctl restart Good Bank
sudo systemctl status Good Bank
```

---

## 🛠️ Troubleshooting

### Can't access the website?
```bash
./manage.sh status          # Is it running?
./manage.sh logs            # Any errors?
grep SERVER_HOST config.py  # Should show 0.0.0.0
```
Also verify Security Group has port 8000 open in AWS Console.

### App crashes on start?
```bash
./manage.sh logs            # See error details
```

### Permission denied on scripts?
```bash
chmod +x deploy.sh manage.sh
```

### Need to update code?
```bash
./manage.sh stop
# Upload new files via SCP
./manage.sh start
```

---

## 💰 Cost Summary

| Component | Free Tier | After Free Tier |
|-----------|-----------|-----------------|
| EC2 t2.micro | FREE (750 hrs/mo) | ~$8.50/month |
| Storage 8GB | FREE (30GB free) | ~$0.80/month |
| **Total** | **FREE** | **~$9.30/month** |

---

## 📞 Your Demo URL

Share this with your 2-3 demo users:
```
http://YOUR_PUBLIC_IP:8000
```

For a friendlier URL (free): `http://YOUR-IP-WITH-DASHES.nip.io:8000`
Example: `http://3-15-123-45.nip.io:8000`

# Good Bank App - Update & Redeploy Guide

A quick reference for updating your app on EC2 after making code changes.

---

## 🔄 Scenario 1: Updating a Few Files

Use this when you've changed only 1-3 files (e.g., `app.py`, `config.py`, or HTML).

### Step 1: Stop the running app (on EC2)
```bash
cd ~/chat_app_aws
./manage.sh stop

# If that doesn't work, force kill:
pkill -f "python app.py"
```

### Step 2: Upload changed files (from local machine)
```bash
# Upload specific files
scp -i your-key.pem app.py ec2-user@YOUR_EC2_IP:~/chat_app_aws/
scp -i your-key.pem config.py ec2-user@YOUR_EC2_IP:~/chat_app_aws/

# For HTML template
scp -i your-key.pem templates/index.html ec2-user@YOUR_EC2_IP:~/chat_app_aws/templates/
```

### Step 3: Start the app (on EC2)
```bash
cd ~/chat_app_aws
./manage.sh start
```

---

## 📁 Scenario 2: Replacing Entire Folder

Use this when you've made major changes across multiple files.

### Step 1: Stop and delete old folder (on EC2)
```bash
cd ~
pkill -f "python app.py"
rm -rf ~/chat_app_aws
```

### Step 2: Upload new folder (from local machine)

**⚠️ IMPORTANT: Avoid nested folder issue!**

```bash
# Option A: Upload from INSIDE your local chat_app_aws folder
cd /path/to/your/chat_app_aws
scp -i your-key.pem -r . ec2-user@YOUR_EC2_IP:~/chat_app_aws

# Option B: Or upload the folder (will create chat_app_aws on EC2)
cd /path/to/parent/folder
scp -i your-key.pem -r chat_app_aws ec2-user@YOUR_EC2_IP:~
```

### Step 3: Deploy and start (on EC2)
```bash
cd ~/chat_app_aws
chmod +x deploy.sh manage.sh
./deploy.sh
./manage.sh start
```

---

## 🛠️ Scenario 3: Only Changed requirements.txt

If you added new Python packages:

```bash
# On EC2
cd ~/chat_app_aws
./manage.sh stop
source venv/bin/activate
pip install -r requirements.txt
./manage.sh start
```

---

## 📋 Quick Command Reference

| Task | Command (on EC2) |
|------|------------------|
| Stop app | `./manage.sh stop` |
| Force stop | `pkill -f "python app.py"` |
| Start app | `./manage.sh start` |
| Restart app | `./manage.sh restart` |
| Check status | `./manage.sh status` |
| View logs | `./manage.sh logs` |
| Check port 8000 | `fuser 8000/tcp` |
| Kill port 8000 | `fuser -k 8000/tcp` |

---

## ⚠️ Common Issues & Fixes

### 1. "Address already in use - Port 8000"
Old process still running. Fix:
```bash
pkill -f "python app.py"
# or
fuser -k 8000/tcp
```

### 2. Nested folder (chat_app_aws/chat_app_aws/)
You uploaded the folder inside itself. Fix:
```bash
# On EC2 - flatten it
cd ~
rm -rf ~/chat_app_aws
mv ~/chat_app_aws/chat_app_aws ~/chat_app_aws  # if nested

# Or re-upload correctly from local:
cd /path/to/your/chat_app_aws   # go INSIDE the folder
scp -i your-key.pem -r . ec2-user@YOUR_EC2_IP:~/chat_app_aws
```

### 3. Public IP not showing / changed
AWS EC2 changes IP after stop/start. Get current IP:
```bash
# On EC2
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4
```
Or just check EC2 Console → Instance → Public IPv4.

### 4. Permission denied on scripts
```bash
chmod +x deploy.sh manage.sh
```

### 5. Module not found error
Virtual environment not activated or packages missing:
```bash
cd ~/chat_app_aws
source venv/bin/activate
pip install -r requirements.txt
./manage.sh start
```

### 6. Config issue - Can't connect from browser
Check SERVER_HOST in config.py:
```bash
grep SERVER_HOST config.py
# Should show: SERVER_HOST = '0.0.0.0'
```

---

## 🔁 Complete Update Workflow (Copy-Paste Ready)

### On EC2 - Prepare for update:
```bash
cd ~/chat_app_aws && ./manage.sh stop
pkill -f "python app.py" 2>/dev/null
```

### On Local - Upload files:
```bash
# Single file
scp -i your-key.pem FILENAME ec2-user@YOUR_IP:~/chat_app_aws/

# Entire folder (from inside chat_app_aws folder)
scp -i your-key.pem -r . ec2-user@YOUR_IP:~/chat_app_aws
```

### On EC2 - Start:
```bash
cd ~/chat_app_aws && ./manage.sh start
```

---

## 💡 Pro Tips

1. **Always stop before updating** - Prevents port conflicts

2. **Check logs if something fails**:
   ```bash
   ./manage.sh logs
   # or
   tail -50 ~/chat_app_aws/app.log
   ```

3. **Test locally first** - Run `python app.py` on your machine before uploading

4. **Bookmark your EC2 Console** - Fastest way to get your current public IP

5. **Keep your .pem file safe** - You can't download it again!

---

## 🌐 Access Your App

```
http://YOUR_EC2_PUBLIC_IP:8000
```

Get your IP from EC2 Console or run the IP command above.

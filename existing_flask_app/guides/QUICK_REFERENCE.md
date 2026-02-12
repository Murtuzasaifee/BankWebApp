# AWS EC2 Quick Reference Card

## 🎯 5-Minute Deployment Checklist

### In AWS Console:

```
☐ 1. Go to EC2 → Launch Instance
☐ 2. Name: Good Bank-Chat-Demo
☐ 3. AMI: Amazon Linux 2023 (Free tier)
☐ 4. Instance: t2.micro (Free tier)
☐ 5. Key pair: Create new, download .pem
☐ 6. Security Group:
      ☐ SSH (22) - My IP
      ☐ HTTP (80) - Anywhere
      ☐ Custom TCP (8000) - Anywhere
☐ 7. Launch Instance
☐ 8. Wait for "2/2 checks passed"
☐ 9. Copy Public IP address
```

### On Your Local Machine:

```bash
# Upload files to EC2
scp -i your-key.pem -r ./your-folder ec2-user@YOUR_IP:~/chat_app_aws
```

### On EC2 (via SSH or Instance Connect):

```bash
# One-time setup
cd ~/chat_app_aws
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Fix config (IMPORTANT!)
sed -i "s/127.0.0.1/0.0.0.0/g" config.py

# Start app
nohup python app.py > app.log 2>&1 &
```

### Access Your App:

```
http://YOUR_PUBLIC_IP:8000
```

---

## 🔧 Common Commands

| Task | Command |
|------|---------|
| Start app | `source venv/bin/activate && nohup python app.py > app.log 2>&1 &` |
| Stop app | `pkill -f "python app.py"` |
| View logs | `tail -f app.log` |
| Check status | `ps aux \| grep python` |
| Restart | `pkill -f "python app.py" && source venv/bin/activate && nohup python app.py > app.log 2>&1 &` |

---

## ⚠️ Critical Settings

### config.py must have:
```python
SERVER_HOST = '0.0.0.0'  # NOT 127.0.0.1
```

### Security Group must allow:
```
Port 8000 from 0.0.0.0/0 (or specific IPs)
```

---

## 💰 Cost: FREE (12 months free tier)

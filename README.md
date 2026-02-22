# Banking Web Application with FastAPI

A modern banking web application built with FastAPI, integrating with AI Agent Platform (IntellectSee) for intelligent customer support. Features session-based authentication, loan applications, and real-time chat with AI agents.

## 🚀 Features

- **AI-Powered Chat**: Intelligent customer support using AI Agent Platform
- **Session-Based Authentication**: Secure login with demo users
- **Loan Application System**: Submit and process loan applications
- **Dual Agent Context**: Different AI agents for guest vs logged-in users
- **Responsive UI**: Modern, mobile-friendly interface
- **Environment Support**: Seamless local and production deployment

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)
- For EC2 deployment: AWS account with EC2 instance

## 🏠 Local Development

### Quick Start

1. **Clone the repository**
   ```bash
   cd BankApp
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

3. **Deploy and run**
   ```bash
   bash deployment_scripts/deploy.sh local
   ```

   The application will:
   - Create a virtual environment
   - Install dependencies
   - Configure settings for local development
   - Start the server at http://127.0.0.1:8000

### Manual Setup (Alternative)

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure .env file**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Management Commands

```bash
# Start the application
bash deployment_scripts/manage.sh start

# Stop the application
bash deployment_scripts/manage.sh stop

# Restart the application
bash deployment_scripts/manage.sh restart

# Check status
bash deployment_scripts/manage.sh status

# View logs (last 50 lines)
bash deployment_scripts/manage.sh logs

# Follow logs in real-time
bash deployment_scripts/manage.sh logs -f
```

## ☁️ AWS EC2 Deployment

### Prerequisites

1. **Launch EC2 Instance**
   - AMI: Ubuntu Server 22.04 LTS or Amazon Linux 2
   - Instance Type: t2.micro (minimum) or higher
   - Security Group: Allow inbound traffic on port 8000

2. **Configure Security Group**
   ```
   Type: Custom TCP
   Protocol: TCP
   Port Range: 8000
   Source: 0.0.0.0/0 (or your IP for security)
   ```

### Deployment Steps

1. **Connect to EC2 instance**
   ```bash
   ssh -i your-key.pem ec2-user@your-ec2-public-ip
   # OR for Ubuntu:
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

2. **Install Python and Git** (if not already installed)
   ```bash
   # For Amazon Linux 2
   sudo yum update -y
   sudo yum install python3 python3-pip git -y

   # For Ubuntu
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git -y
   ```

3. **Upload application files**

   **Option A: Using SCP (from local machine)**
   ```bash
   scp -i your-key.pem -r BankApp ec2-user@your-ec2-ip:~/
   ```

   **Option B: Using Git**
   ```bash
   git clone your-repository-url
   cd BankApp
   ```

4. **Configure environment**
   ```bash
   cd BankApp
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

   Ensure you set appropriate values for:
   - `PLATFORM_USERNAME` and `PLATFORM_PASSWORD`
   - `API_KEY` and `WORKSPACE_ID`
   - `CHATNOW_ASSET_ID` and related IDs
   - `SECRET_KEY` (generate a strong key)

5. **Deploy and run**
   ```bash
   bash deployment_scripts/deploy.sh production
   ```

   The script will:
   - Auto-detect EC2 environment
   - Configure settings for production (0.0.0.0, debug=false)
   - Create virtual environment
   - Install dependencies
   - Start the application
   - Display the public access URL

6. **Access your application**
   ```
   http://YOUR_EC2_PUBLIC_IP:8000
   ```

### Optional: Configure Systemd Service (Auto-start on Reboot)

1. **Create systemd service file**
   ```bash
   sudo nano /etc/systemd/system/bankapp.service
   ```

2. **Add the following content** (adjust paths as needed):
   ```ini
   [Unit]
   Description=Banking Web Application with FastAPI
   After=network.target

   [Service]
   Type=simple
   User=ec2-user
   WorkingDirectory=/home/ec2-user/BankApp
   EnvironmentFile=/home/ec2-user/BankApp/.env
   ExecStart=/home/ec2-user/BankApp/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bankapp
   sudo systemctl start bankapp
   sudo systemctl status bankapp
   ```

4. **Manage the service**
   ```bash
   sudo systemctl stop bankapp      # Stop
   sudo systemctl restart bankapp   # Restart
   sudo systemctl status bankapp    # Check status
   sudo journalctl -u bankapp -f    # View logs
   ```

## 🔧 Configuration

### Environment Variables (.env)

```ini
# AI Agent Platform Credentials
PLATFORM_BASE_URL=https://api.intellectseecstag.com/magicplatform/v1
AUTH_BASE_URL=https://api.intellectseecstag.com/accesstoken
TENANT=your_tenant
API_KEY=your_api_key
WORKSPACE_ID=your_workspace_id
PLATFORM_USERNAME=your_username
PLATFORM_PASSWORD=your_password

# Agent Configuration
CHATNOW_ASSET_ID=guest_agent_asset_version_id
INTELLICHAT_ASSET_ID=logged_in_agent_asset_version_id
LOAN_AGENT_ASSET_ID=loan_processing_agent_asset_id
AGENT_NAME=Bank Support Agent
CONVERSATION_NAME=Bank Customer Support Chat
QUERY_TIMEOUT=60

# Application Configuration
ENVIRONMENT=local  # or "production"
SECRET_KEY=your_secret_key_here
SERVER_HOST=127.0.0.1  # 0.0.0.0 for production
SERVER_PORT=8000
DEBUG_MODE=true  # false for production
```

### Demo Users

The application includes two demo users:

1. **Mohammed Faisal**
   - Username: `Mohammed Faisal`
   - Password: `password`
   - Features: Multiple accounts, transactions, loan history

2. **Ahmed Al Mansouri**
   - Username: `Ahmed Al Mansouri`
   - Password: `password`
   - Features: Savings account, recent transactions

## 📁 Project Structure

```
BankApp/
├── app/
│   ├── core/              # Core configuration and dependencies
│   │   ├── config.py      # Settings and environment management
│   │   ├── session.py     # Session management (HMAC-based)
│   │   └── dependencies.py # Shared dependencies
│   ├── services/          # External service integrations
│   │   └── query_agent.py # AI Agent Platform client
│   ├── models/            # Pydantic models
│   │   └── schemas.py     # Request/response schemas
│   ├── data/              # Static data
│   │   └── demo_data.py   # Demo users and accounts
│   ├── routers/           # API route handlers
│   │   ├── pages.py       # HTML page routes
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── chat.py        # Chat endpoints
│   │   ├── loan.py        # Loan application endpoints
│   │   └── health.py      # Health check endpoints
│   ├── static/            # Static assets (CSS, JS)
│   ├── templates/         # Jinja2 HTML templates
│   └── main.py            # FastAPI application entry point
├── deployment_scripts/
│   ├── deploy.sh          # Automated deployment script
│   ├── manage.sh          # Application management script
│   └── bankapp.service   # Systemd service file (optional)
├── guides/
│   └── EC2_DEPLOYMENT_GUIDE.md  # Detailed EC2 deployment guide
├── .env                   # Environment configuration (not in git)
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🧪 Testing Locally

1. **Start the application**
   ```bash
   bash deployment_scripts/deploy.sh local
   ```

2. **Access the application**
   - Open browser: http://127.0.0.1:8000
   - Test guest chat (click chat icon)
   - Login with demo credentials
   - Test logged-in chat (different agent context)
   - Submit a loan application

3. **API Endpoints**
   - Health check: http://127.0.0.1:8000/health
   - Configuration: http://127.0.0.1:8000/config
   - API docs: http://127.0.0.1:8000/docs (FastAPI auto-generated)

## 🔍 Troubleshooting

### Application won't start

1. **Check logs**
   ```bash
   bash deployment_scripts/manage.sh logs
   # OR
   tail -f app.log
   ```

2. **Verify .env file**
   ```bash
   cat .env  # Check all required fields are filled
   ```

3. **Check port availability**
   ```bash
   lsof -i :8000  # Check if port 8000 is in use
   ```

### Connection refused on EC2

1. **Verify security group** allows inbound traffic on port 8000
2. **Check application is running**
   ```bash
   bash deployment_scripts/manage.sh status
   ```
3. **Verify SERVER_HOST is set to 0.0.0.0** in .env

### Agent not responding

1. **Verify credentials** in .env (PLATFORM_USERNAME, PLATFORM_PASSWORD, API_KEY)
2. **Check asset version IDs** are correct
3. **Test health endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

### Session issues

1. **Clear browser cookies**
2. **Restart application**
   ```bash
   bash deployment_scripts/manage.sh restart
   ```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [EC2 Deployment Guide](guides/EC2_DEPLOYMENT_GUIDE.md)
- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/pydantic_settings/)

## 🛡️ Security Notes

- **Never commit .env file** to version control
- **Generate strong SECRET_KEY** for production
- **Use HTTPS** in production (configure reverse proxy like Nginx)
- **Restrict security group** to specific IPs when possible
- **Keep dependencies updated** regularly

## 📄 License

This is a demo application for banking support chat functionality.

## 👥 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs: `bash deployment_scripts/manage.sh logs`
3. Check [EC2 Deployment Guide](guides/EC2_DEPLOYMENT_GUIDE.md) for detailed steps

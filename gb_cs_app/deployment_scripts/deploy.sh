#!/bin/bash
# Quick Deploy Script for Good Bank Chat Application
# Run this after uploading your application files to EC2

echo "=========================================="
echo "Good Bank Chat Application - Quick Deploy"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found!"
    echo "Please run this script from your app directory (where app.py is located)"
    exit 1
fi

if [ ! -f "config.py" ]; then
    echo "❌ Error: config.py not found!"
    exit 1
fi

# Check if SERVER_HOST is set correctly
if grep -q "SERVER_HOST = '127.0.0.1'" config.py; then
    echo "⚠️  Updating SERVER_HOST from 127.0.0.1 to 0.0.0.0..."
    sed -i "s/SERVER_HOST = '127.0.0.1'/SERVER_HOST = '0.0.0.0'/g" config.py
    echo "✅ SERVER_HOST updated!"
fi

echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo ""
echo "  Option 1 (Foreground - for testing):"
echo "    source venv/bin/activate"
echo "    python app.py"
echo ""
echo "  Option 2 (Background - for demo):"
echo "    source venv/bin/activate"
echo "    nohup python app.py > app.log 2>&1 &"
echo ""
echo "Your app will be available at:"
echo "  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR_PUBLIC_IP'):8000"
echo ""
echo "=========================================="

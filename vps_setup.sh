#!/bin/bash
# Quick VPS Deployment Script for Material Identification API
# Run this on your VPS after uploading files

echo "=========================================="
echo "Material Identification API - VPS Setup"
echo "=========================================="

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "Installing Python and dependencies..."
sudo apt install python3 python3-pip python3-venv -y

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install flask flask-cors tensorflow pillow numpy gunicorn

# Test the application
echo "Testing application..."
python backend_api.py &
sleep 5
curl http://localhost:5001/health
kill %1

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To run the API server:"
echo "  source venv/bin/activate"
echo "  python backend_api.py"
echo ""
echo "To run in production with Gunicorn:"
echo "  source venv/bin/activate"
echo "  gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 backend_api:app"
echo ""
echo "To run in background:"
echo "  nohup gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 backend_api:app > api.log 2>&1 &"
echo ""
echo "=========================================="

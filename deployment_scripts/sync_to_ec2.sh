#!/bin/bash
# ============================================================================
# sync_to_ec2.sh - Smart Deployment Script using rsync
# 
# Usage: 
#   bash deployment_scripts/sync_to_ec2.sh [options] <user@ec2-address> <target-directory>
#
# Examples:
#   bash deployment_scripts/sync_to_ec2.sh ec2-user@34.22.x.x /home/ec2-user/BankApp
#   bash deployment_scripts/sync_to_ec2.sh -i ~/.ssh/my_key.pem ec2-user@34.22.x.x /home/ec2-user/BankApp
#   bash deployment_scripts/sync_to_ec2.sh --deploy ec2-user@34.22.x.x /home/ec2-user/BankApp
#   bash deployment_scripts/sync_to_ec2.sh --redeploy ec2-user@34.22.x.x /home/ec2-user/BankApp
#   bash deployment_scripts/sync_to_ec2.sh --fresh ec2-user@34.22.x.x /home/ec2-user/BankApp
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse arguments
SSH_KEY=""
DEPLOY=false
REDEPLOY=false
FRESH=false

while [[ "$#" -gt 2 ]]; do
    case $1 in
        -i|--identity) SSH_KEY="$2"; shift ;;
        --deploy) DEPLOY=true ;;
        --redeploy) REDEPLOY=true ;;
        --fresh) FRESH=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 [-i key.pem] [--deploy] [--redeploy] [--fresh] <user@ec2-host> <target-directory>"
    exit 1
fi

EC2_HOST="$1"
TARGET_DIR="$2"

echo "============================================"
echo "  Deploying BankApp to EC2                  "
echo "============================================"

# Change to project root to ensure rsync paths are correct relative to the repo
cd "$PROJECT_ROOT"

# Build SSH command based on identity file presence
if [ -n "$SSH_KEY" ]; then
    SSH_CMD="ssh -i $SSH_KEY"
    echo "Using SSH Key: $SSH_KEY"
else
    SSH_CMD="ssh"
    echo "Using default SSH agent configuration."
fi
echo "Target: $EC2_HOST:$TARGET_DIR"
echo ""

# Ensure target directory exists on remote before rsyncing
echo "Ensuring target directory exists..."
$SSH_CMD "$EC2_HOST" "mkdir -p $TARGET_DIR"

echo "Syncing files..."
# Run rsync:
# -a: archive mode (preserves permissions, times, etc.)
# -v: verbose
# -z: compress file data during the transfer
# --delete: delete extraneous files from destination
# --include='.env': prioritize explicitly copying the actual credentials
# --exclude='.env.example': prevent copying the sample template over
# --filter: use .gitignore patterns to ignore files
rsync -avz --delete \
    -e "$SSH_CMD" \
    --include='.env' \
    --exclude='.env.example' \
    --filter=':- .gitignore' \
    --exclude='venv/' \
    --exclude='*.pem' \
    --exclude='.git/' \
    --exclude='.gitignore' \
    ./ "$EC2_HOST:$TARGET_DIR/"

echo ""
echo "Sync Complete!"

# Kill any process running on port 8000 before deployment
if [ "$DEPLOY" = true ] || [ "$REDEPLOY" = true ] || [ "$FRESH" = true ]; then
    echo "Checking if port 8000 is in use on EC2..."
    $SSH_CMD "$EC2_HOST" "PID=\$(sudo lsof -t -i:8000 2>/dev/null || true); if [ -n \"\$PID\" ]; then echo \"  - Killing process on port 8000 (PID: \$PID)...\"; sudo kill -9 \$PID; sleep 2; echo \"  - Port 8000 is now free.\"; else echo \"  - Port 8000 is free.\"; fi"
    echo ""
fi

# Handle optional deployment scripts
if [ "$DEPLOY" = true ]; then
    echo "============================================"
    echo "  Triggering Initial Deployment on EC2      "
    echo "============================================"
    $SSH_CMD "$EC2_HOST" "cd $TARGET_DIR && bash deployment_scripts/deploy.sh production"
    echo "Deployment command executed."
elif [ "$REDEPLOY" = true ]; then
    echo "============================================"
    echo "  Triggering Redeployment on EC2            "
    echo "============================================"
    $SSH_CMD "$EC2_HOST" "cd $TARGET_DIR && if [ ! -d 'venv' ]; then echo 'Virtual environment missing, recreating...'; bash deployment_scripts/deploy.sh production; else bash deployment_scripts/manage.sh restart; fi"
    echo "Redeployment command executed."
elif [ "$FRESH" = true ]; then
    echo "============================================"
    echo "  Triggering Fresh Deployment on EC2        "
    echo "============================================"
    echo "Removing existing virtual environment and redeploying from scratch..."
    $SSH_CMD "$EC2_HOST" "cd $TARGET_DIR && rm -rf venv; bash deployment_scripts/deploy.sh production"
    echo "Fresh deployment command executed."
fi

echo ""
echo "Deployment Process Finished Successfully."

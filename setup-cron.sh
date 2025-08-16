#!/bin/bash

# Setup cron job for auto-deployment
# Run this once on the GCP instance

set -e

echo "Setting up auto-deployment cron job..."

# Copy the auto-deploy script to home directory
cp auto-deploy.sh ~/auto-deploy.sh
chmod +x ~/auto-deploy.sh

# Create log directory
mkdir -p ~/logs

# Add cron job (runs every minute)
(crontab -l 2>/dev/null; echo "* * * * * ~/auto-deploy.sh >> ~/logs/auto-deploy.log 2>&1") | crontab -

echo "✅ Cron job configured to run every minute"
echo "📋 Check logs with: tail -f ~/logs/auto-deploy.log"
echo "🔧 To remove cron job: crontab -e"
#!/bin/bash

# Check status of containers and services on GCP instance

GCP_PROJECT_ID="playground-161404"
GCP_INSTANCE_NAME="the-gigi"
GCP_ZONE="us-west1-c"

echo "🔍 Checking container status on GCP instance..."
echo ""

# Execute commands remotely
gcloud compute ssh --zone "$GCP_ZONE" "$GCP_INSTANCE_NAME" --project "$GCP_PROJECT_ID" --command "
echo '=== Docker Container Status ==='
docker ps -a

echo ''
echo '=== Docker Images ==='
docker images | grep wendler

echo ''
echo '=== Auto-deploy Script ==='
if [ -f ~/auto-deploy.sh ]; then
    echo 'Auto-deploy script exists'
    grep -n 'wendler-data\|~/data' ~/auto-deploy.sh || echo 'No volume mount patterns found'
else
    echo 'Auto-deploy script not found'
fi

echo ''
echo '=== Cron Jobs ==='
crontab -l | grep auto-deploy || echo 'No auto-deploy cron job found'

echo ''
echo '=== Recent Auto-deploy Logs ==='
if [ -f ~/logs/auto-deploy.log ]; then
    tail -10 ~/logs/auto-deploy.log
else
    echo 'No auto-deploy logs found'
fi

echo ''
echo '=== Directory Structure ==='
ls -la ~/ | grep -E 'data|wendler'
"
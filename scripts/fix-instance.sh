#!/bin/bash

# Fix the instance with updated auto-deploy script and image name

GCP_PROJECT_ID="playground-161404"
GCP_INSTANCE_NAME="the-gigi"
GCP_ZONE="us-west1-c"

echo "🔧 Fixing instance with updated auto-deploy script..."
echo ""

# Copy the updated auto-deploy script to instance
echo "📁 Copying updated auto-deploy script to instance..."
gcloud compute scp /Users/gigi/git/wendler-5-3-1/scripts/auto-deploy.sh $GCP_INSTANCE_NAME:~/auto-deploy.sh --zone "$GCP_ZONE" --project "$GCP_PROJECT_ID"

# Execute fix commands remotely
echo "🔧 Applying fixes on instance..."
gcloud compute ssh --zone "$GCP_ZONE" "$GCP_INSTANCE_NAME" --project "$GCP_PROJECT_ID" --command "
echo 'Making auto-deploy script executable...'
chmod +x ~/auto-deploy.sh

echo ''
echo 'Stopping any existing container...'
docker stop wendler-backend 2>/dev/null || true
docker rm wendler-backend 2>/dev/null || true

echo ''
echo 'Creating wendler-data directory...'
mkdir -p ~/wendler-data

echo ''
echo 'Moving existing database if it exists...'
if [ -f ~/data/wendler.db ]; then
    echo 'Moving database from ~/data to ~/wendler-data'
    cp ~/data/wendler.db ~/wendler-data/
else
    echo 'No existing database found in ~/data'
fi

echo ''
echo 'Running updated auto-deploy script...'
~/auto-deploy.sh

echo ''
echo '=== Final Status ==='
docker ps -a | grep wendler
"

echo ""
echo "✅ Fix completed!"
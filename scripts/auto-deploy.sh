#!/bin/bash

# Auto-deployment script for Wendler 5-3-1 backend
# Checks for new Docker image and updates container if available

set -e

IMAGE_NAME="ghcr.io/the-gigi/wendler-5-3-1:latest"
CONTAINER_NAME="wendler-backend"
PORT="8000"

echo "$(date): Checking for new image updates..."

# Pull the latest image (this will only download if there's a new version)
docker pull $IMAGE_NAME

# Get the image ID of the pulled image
NEW_IMAGE_ID=$(docker images --no-trunc --quiet $IMAGE_NAME)

# Get the image ID of the running container (if any)
RUNNING_IMAGE_ID=""
if docker ps --filter "name=$CONTAINER_NAME" --format "{{.ID}}" | head -1 | xargs -I {} docker inspect --format="{{.Image}}" {} 2>/dev/null; then
    RUNNING_IMAGE_ID=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.ID}}" | head -1 | xargs -I {} docker inspect --format="{{.Image}}" {})
fi

# Compare image IDs
if [ "$NEW_IMAGE_ID" != "$RUNNING_IMAGE_ID" ]; then
    echo "$(date): New image detected! Updating container..."
    
    # Stop and remove old container
    docker ps --filter "name=$CONTAINER_NAME" --format "{{.ID}}" | head -1 | xargs -r docker stop
    docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.ID}}" | head -1 | xargs -r docker rm
    
    # Ensure data directory exists on host
    mkdir -p ~/wendler-data
    
    # Start new container with specific name and volume mount for database persistence
    docker run -d --name $CONTAINER_NAME -p $PORT:$PORT \
        -v ~/wendler-data:/app/data \
        -e FRONTEND_ORIGIN="https://the-gigi.github.io" \
        $IMAGE_NAME
    
    echo "$(date): Container updated successfully!"
    
    # Clean up old images (keep last 3 versions)
    docker images $IMAGE_NAME --format "{{.ID}}" | tail -n +4 | xargs -r docker rmi
    
else
    echo "$(date): No updates available. Container is up to date."
fi
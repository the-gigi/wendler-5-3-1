#!/bin/bash

# Complete initialization script for Wendler 5-3-1 on GCP
# Idempotent - safe to run multiple times

set -e

echo "🚀 Initializing Wendler 5-3-1 deployment on GCP..."

# Function to install Docker (idempotent)
install_docker() {
    if command -v docker >/dev/null 2>&1; then
        echo "✅ Docker already installed: $(docker --version)"
        return 0
    fi

    echo "🐳 Installing Docker on GCP Debian instance..."

    # Clean up any existing Docker repositories
    sudo rm -f /etc/apt/sources.list.d/docker.list
    sudo rm -f /etc/apt/sources.list.d/*docker*
    sudo rm -f /etc/apt/keyrings/docker.gpg
    sudo rm -f /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Remove any Docker entries from all sources
    sudo sed -i '/download\.docker\.com/d' /etc/apt/sources.list 2>/dev/null || true
    sudo find /etc/apt/sources.list.d/ -name "*.list" -exec sudo sed -i '/download\.docker\.com/d' {} \; 2>/dev/null || true

    # Update package index
    sudo apt-get update

    # Install prerequisites
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Set up the repository for Debian
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Update package index again
    sudo apt-get update

    # Install Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add current user to docker group (to run without sudo)
    sudo usermod -aG docker $USER

    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker

    echo "✅ Docker installed successfully!"
    echo "⚠️  You may need to log out and back in to use Docker without sudo"

    # Test installation with sudo for now
    sudo docker --version
}

# Function to setup auto-deployment (idempotent)
setup_auto_deploy() {
    echo "🔄 Setting up auto-deployment..."

    # Create auto-deploy script
    cat > ~/auto-deploy.sh << 'EOF'
#!/bin/bash

# Auto-deployment script for Wendler 5-3-1 backend
# Checks for new Docker image and updates container if available

set -e

IMAGE_NAME="ghcr.io/the-gigi/wendler-5-3-1/backend:latest"
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
    docker ps --filter "name=$CONTAINER_NAME" --format "{{.ID}}" | head -1 | xargs -r docker stop 2>/dev/null || true
    docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.ID}}" | head -1 | xargs -r docker rm 2>/dev/null || true
    
    # Create database directory if it doesn't exist
    mkdir -p ~/data
    
    # Start new container with specific name and volume mount
    docker run -d --name $CONTAINER_NAME -p $PORT:$PORT -v ~/data:/app/data $IMAGE_NAME
    
    echo "$(date): Container updated successfully!"
    
    # Clean up old images (keep last 3 versions)
    docker images $IMAGE_NAME --format "{{.ID}}" | tail -n +4 | xargs -r docker rmi 2>/dev/null || true
    
else
    echo "$(date): No updates available. Container is up to date."
fi
EOF

    chmod +x ~/auto-deploy.sh

    # Create log directory
    mkdir -p ~/logs

    # Check if auto-deploy cron job already exists
    if crontab -l 2>/dev/null | grep -q "auto-deploy.sh"; then
        echo "✅ Auto-deploy cron job already configured"
    else
        echo "⏰ Setting up auto-deploy cron job..."
        # Add auto-deploy cron job (runs every minute)
        (crontab -l 2>/dev/null; echo "* * * * * ~/auto-deploy.sh >> ~/logs/auto-deploy.log 2>&1") | crontab -
        echo "✅ Auto-deploy cron job configured to run every minute"
    fi

    # Check if backup cron job already exists
    if crontab -l 2>/dev/null | grep -q "backup-db.sh"; then
        echo "✅ Backup cron job already configured"
    else
        echo "⏰ Setting up daily backup cron job..."
        # Add backup cron job (runs daily at 2 AM)
        (crontab -l 2>/dev/null; echo "0 2 * * * ~/backup-db.sh >> ~/logs/backup.log 2>&1") | crontab -
        echo "✅ Daily backup cron job configured for 2 AM"
    fi
}

# Function to start initial container (idempotent)
start_initial_container() {
    echo "🐳 Setting up initial container..."
    
    # Check if container is already running
    if docker ps --filter "name=wendler-backend" --format "{{.Names}}" | grep -q "wendler-backend"; then
        echo "✅ Container 'wendler-backend' is already running"
        return 0
    fi

    # Remove any stopped container with the same name
    docker ps -a --filter "name=wendler-backend" --format "{{.ID}}" | head -1 | xargs -r docker rm 2>/dev/null || true

    # Create database directory if it doesn't exist
    mkdir -p ~/data

    # Pull and run the backend container with volume mount
    docker pull ghcr.io/the-gigi/wendler-5-3-1/backend:latest
    docker run -d --name wendler-backend -p 8000:8000 -v ~/data:/app/data ghcr.io/the-gigi/wendler-5-3-1/backend:latest
    
    echo "✅ Container started successfully!"
}

# Main execution
main() {
    # Install Docker
    install_docker
    
    # Setup auto-deployment
    setup_auto_deploy
    
    # Create database directory
    mkdir -p ~/data
    echo "📁 Created database directory: ~/data"
    
    # Start initial container (use sudo if user not in docker group yet)
    if groups $USER | grep -q docker; then
        start_initial_container
    else
        echo "🐳 Starting initial container with sudo (user not yet in docker group)..."
        sudo docker pull ghcr.io/the-gigi/wendler-5-3-1/backend:latest || true
        sudo docker ps --filter "name=wendler-backend" --format "{{.ID}}" | head -1 | xargs -r sudo docker stop 2>/dev/null || true
        sudo docker ps -a --filter "name=wendler-backend" --format "{{.ID}}" | head -1 | xargs -r sudo docker rm 2>/dev/null || true
        sudo docker run -d --name wendler-backend -p 8000:8000 -v ~/data:/app/data ghcr.io/the-gigi/wendler-5-3-1/backend:latest
        echo "✅ Container started successfully!"
    fi
    
    # Get external IP
    EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/network-interfaces/0/external-ip 2>/dev/null || echo "UNKNOWN")
    
    echo ""
    echo "🎉 Initialization complete!"
    echo "📱 App should be available at: http://$EXTERNAL_IP:8000"
    echo "📊 API docs at: http://$EXTERNAL_IP:8000/docs"
    echo "📋 Check auto-deploy logs with: tail -f ~/logs/auto-deploy.log"
    echo "🔧 Container status: docker ps"
}

# Function to setup firewall rule (idempotent)
setup_firewall() {
    echo "🔥 Setting up firewall rule..."
    
    # Check if firewall rule already exists
    if gcloud compute firewall-rules describe allow-port-8000 --project="playground-161404" >/dev/null 2>&1; then
        echo "✅ Firewall rule 'allow-port-8000' already exists"
    else
        echo "🔧 Creating firewall rule to allow port 8000..."
        gcloud compute firewall-rules create allow-port-8000 --allow tcp:8000 --source-ranges 0.0.0.0/0 --description "Allow port 8000" --project="playground-161404"
        echo "✅ Firewall rule created successfully!"
    fi
}

# Check if we're running locally (has gcloud) or remotely (GCP instance)
if command -v gcloud >/dev/null 2>&1 && [[ -n "${GOOGLE_CLOUD_PROJECT:-}" || -f ~/.config/gcloud/configurations/config_default ]]; then
    echo "🚀 Detected local environment with gcloud - deploying to GCP instance..."
    
    # Setup firewall rule locally
    setup_firewall
    
    # Copy scripts to GCP instance
    gcloud compute scp init.sh backup-db.sh the-gigi:~ --zone "us-west1-c" --project "playground-161404"
    
    # Execute script remotely
    gcloud compute ssh --zone "us-west1-c" "the-gigi" --project "playground-161404" --command "bash ~/init.sh"
    
    # Get and display external IP
    echo ""
    echo "🎯 Getting external IP address..."
    EXTERNAL_IP=$(gcloud compute instances describe the-gigi --zone="us-west1-c" --project="playground-161404" --format="get(networkInterfaces[0].accessConfigs[0].natIP)")
    echo "🌐 Your app should be available at: http://$EXTERNAL_IP:8000"
    echo "📊 API docs at: http://$EXTERNAL_IP:8000/docs"
else
    # We're running on the remote instance
    main
fi
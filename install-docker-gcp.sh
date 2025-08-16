#!/bin/bash

# Docker installation script for GCP Debian instance
set -e

# Function to install Docker on the remote instance
install_docker() {
    echo "🐳 Installing Docker on GCP Debian instance..."

    # Clean up any existing Docker repositories
    sudo rm -f /etc/apt/sources.list.d/docker.list
    sudo rm -f /etc/apt/sources.list.d/*docker*
    sudo rm -f /etc/apt/keyrings/docker.gpg
    sudo rm -f /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Remove any Docker entries from all sources
    sudo sed -i '/download\.docker\.com/d' /etc/apt/sources.list
    sudo find /etc/apt/sources.list.d/ -name "*.list" -exec sudo sed -i '/download\.docker\.com/d' {} \; 2>/dev/null

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
    echo "⚠️  Log out and back in to use Docker without sudo"
    echo "🧪 Test with: docker --version"

    # Test installation
    sudo docker --version
    sudo docker run hello-world
}

# Check if we're running locally (to deploy) or remotely (to install)
if [[ "${1:-}" == "deploy" ]]; then
    echo "🚀 Deploying Docker installation to GCP..."
    
    # Copy script to GCP instance
    gcloud compute scp install-docker-gcp.sh the-gigi:~ --zone "us-west1-c" --project "playground-161404"
    
    # Execute script remotely
    gcloud compute ssh --zone "us-west1-c" "the-gigi" --project "playground-161404" --command "bash ~/install-docker-gcp.sh"
else
    # We're running on the remote instance, so install Docker
    install_docker
fi
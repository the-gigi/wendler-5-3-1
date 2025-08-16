# Scripts Directory

This directory contains all deployment and utility scripts for the Wendler 5-3-1 application.

## Scripts Overview

### Main Deployment
- **`init.sh`** - Main deployment script (run locally to deploy to GCP)
- **`run-tests.sh`** - Run all tests (backend + frontend)

### GCP Instance Scripts  
- **`auto-deploy.sh`** - Auto-deployment script (runs on GCP instance via cron)
- **`backup-db.sh`** - Database backup script (runs on GCP instance via cron)

### Legacy/Alternative Scripts
- **`install-docker-gcp.sh`** - Docker installation script (integrated into init.sh)
- **`setup-cron.sh`** - Cron job setup script (integrated into init.sh)

## Usage

1. **Update configuration** in `init.sh` and `backup-db.sh` for your GCP environment
2. **Run deployment**: `./scripts/init.sh`
3. **Run tests**: `./scripts/run-tests.sh`

The main `init.sh` script handles copying the necessary scripts to your GCP instance automatically.
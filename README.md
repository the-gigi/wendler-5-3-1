# Wendler 5-3-1 Training App

[![CI Pipeline](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/ci.yml/badge.svg)](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/ci.yml)
[![Backend Tests](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/backend-tests.yml)
[![Frontend Tests](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/frontend-tests.yml)

A proper [Wendler](https://www.jimwendler.com/pages/about-jim) [5-3-1](https://thefitness.wiki/5-3-1-primer/) app with comprehensive backend and frontend testing!

## 🚀 Quick Start for Users

**Use the app now:** 🌐 **[https://the-gigi.github.io/wendler-5-3-1](https://the-gigi.github.io/wendler-5-3-1)**

The frontend is deployed automatically to GitHub Pages and connects to a live backend running on Google Cloud Platform.

## Features

- **Complete 5-3-1 Training System**: 4-week cycles with proper progression
- **Expandable Cycle History**: View all historical cycles with full workout details
- **Real-time Workout Tracking**: Track sets, reps, and weights for every movement
- **Training Max Management**: Automatic progression and manual adjustments
- **Comprehensive Testing**: 85%+ backend coverage with automated CI/CD

## Architecture

### Backend

- **FastAPI** with SQLModel for modern Python web development
- **SQLite** database with Alembic migrations
- **Comprehensive test suite** (62 tests, 85% coverage)
- **OAuth authentication** (Google, GitHub, Facebook)
- **Docker containerization** with multi-platform support

### Frontend

- **React Native** with web support via Webpack
- **TypeScript** for type safety
- **Expandable drawer UI** for intuitive cycle navigation
- **Real-time API integration** with loading states

## Testing

All tests run automatically on push/PR via GitHub Actions:

- ✅ **Backend**: 62 tests covering models, CRUD, and business logic
- ✅ **Frontend**: Jest tests with linting and build verification
- ✅ **Integration**: Combined CI pipeline with status reporting
- ✅ **Docker**: Automated image builds with vulnerability scanning

### Running Tests Locally

```bash
# Run all tests with a single command
./scripts/run-tests.sh

# Or run tests individually:
cd backend && uv run pytest --cov=.      # Backend tests
cd frontend/WendlerApp && npm test       # Frontend tests
```

## Deployment Overview

This application uses a modern, automated deployment setup:

### Frontend (React Native Web)
- **Platform**: GitHub Pages
- **URL**: [https://the-gigi.github.io/wendler-5-3-1](https://the-gigi.github.io/wendler-5-3-1)
- **Deployment**: Automatic via GitHub Actions when `frontend/WendlerApp/` changes
- **Build**: Webpack production build with environment-specific backend URL

### Backend (FastAPI)
- **Platform**: Google Cloud Platform (Debian VM)
- **Containerization**: Docker with multi-platform images
- **Auto-deployment**: Cron job checks for new images every minute
- **Database**: SQLite with persistent volume mapping and daily GCS backups
- **Monitoring**: Container health checks and deployment logs

### Infrastructure
- **Container Registry**: GitHub Container Registry (GHCR)
- **CI/CD**: GitHub Actions for testing, building, and deployment
- **Backup**: Daily SQLite backups to Google Cloud Storage (3-day retention)
- **Security**: Firewall rules, non-root container execution

## Docker Images

Pre-built Docker images are available on GitHub Container Registry:

🐳 *
*[ghcr.io/the-gigi/wendler-5-3-1/backend](https://github.com/users/the-gigi/packages/container/wendler-5-3-1%2Fbackend)
**

```bash
# Pull and run the latest backend image
docker pull ghcr.io/the-gigi/wendler-5-3-1/backend:latest
docker run -p 8000:8000 ghcr.io/the-gigi/wendler-5-3-1/backend:latest

# Or use a specific commit SHA
docker pull ghcr.io/the-gigi/wendler-5-3-1/backend:main-abc1234
```

## Frontend Deployment

The frontend is automatically deployed to GitHub Pages at:

🌐 **[https://the-gigi.github.io/wendler-5-3-1](https://the-gigi.github.io/wendler-5-3-1)**

### First-time setup:
1. Go to your repository **Settings** → **Pages**
2. Under **Source**, select **"GitHub Actions"**
3. Click **Save**

The deployment then happens automatically when changes are pushed to the `frontend/WendlerApp/` directory on the main branch.

## Backend Deployment

**First:** Update the GCP configuration variables at the top of `scripts/init.sh` and `scripts/backup-db.sh` for your environment:
```bash
GCP_PROJECT_ID="your-project-id"
GCP_INSTANCE_NAME="your-instance-name"  
GCP_ZONE="your-zone"
```

Then deploy everything to your GCP Debian instance with a single command:

```bash
# Run locally to deploy everything to GCP
./scripts/init.sh
```

**What the init script does:**
- ✅ Creates GCP firewall rule to allow port 8000 (idempotent)
- ✅ Copies deployment scripts to the GCP instance  
- ✅ Remotely installs Docker on the GCP instance (idempotent)
- ✅ Sets up auto-deployment cron job (checks for updates every minute)
- ✅ Sets up daily database backup to Google Cloud Storage (2 AM daily)
- ✅ Creates persistent data directory and starts the backend container
- ✅ Shows you the app URL and next steps

The data is stored in an SQLite database file at `~/data/wendler.db` on the GCP instance (mapped as volume to container).
Daily backups are stored in Google Cloud Storage, keeping the 3 most recent backups.

**Access your app at:** `http://YOUR_EXTERNAL_IP:8000`  
**API docs at:** `http://YOUR_EXTERNAL_IP:8000/docs`

### Host Monitoring

Run the following commands to monitor the deployment (set the variables first):

```bash
GCP_PROJECT_ID="playground-161404"
GCP_INSTANCE_NAME="the-gigi"
GCP_ZONE="us-west1-c"

gcloud compute ssh --zone $ZONE $GCP_INSTANCE_NAME --project $GCP_PROJECT_ID 

# Check container status
docker ps

# Monitor auto-deployment logs
tail -f ~/logs/auto-deploy.log

# Monitor backup logs  
tail -f ~/logs/backup.log

# Manual deployment check
~/auto-deploy.sh

# Manual backup
~/backup-db.sh

# View database
sqlite3 ~/data/wendler.db

# List cloud backups
gsutil ls gs://wendler-5-3-1-backups/

# Restore from backup
gsutil cp gs://wendler-5-3-1-backups/wendler_backup_YYYYMMDD.db ~/data/wendler.db
```

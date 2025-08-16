# Wendler 5-3-1 Training App

[![CI Pipeline](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/ci.yml/badge.svg)](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/ci.yml)
[![Backend Tests](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/backend-tests.yml)
[![Frontend Tests](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/the-gigi/wendler-5-3-1/actions/workflows/frontend-tests.yml)

A proper [Wendler](https://www.jimwendler.com/pages/about-jim) [5-3-1](https://thefitness.wiki/5-3-1-primer/) app with
comprehensive backend and frontend testing!

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
./run-tests.sh

# Or run tests individually:
cd backend && uv run pytest --cov=.      # Backend tests
cd frontend/WendlerApp && npm test       # Frontend tests
```

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

The deployment happens automatically when changes are pushed to the `frontend/WendlerApp/` directory on the main branch.

## Backend Deployment

Deploy everything to your GCP Debian instance with a single command:

```bash
# Deploy everything: firewall, Docker, auto-deployment, and start the app
./init.sh
```

The init script automatically detects whether it's running locally or on the GCP instance and does everything:

**When run locally:**
- ✅ Creates firewall rule to allow port 8000 (idempotent)
- ✅ Copies itself to the GCP instance and runs it there
- ✅ Shows you the app URL and next steps

**When run on GCP instance:**
- ✅ Installs Docker (idempotent - safe to run multiple times)
- ✅ Sets up auto-deployment cron job (checks for updates every minute)
- ✅ Sets up daily database backup to Google Cloud Storage (2 AM daily)
- ✅ Pulls and starts the latest backend container with persistent data volume

The data is stored in an SQLite database file at `~/data/wendler.db` (mapped as volume to container).
Daily backups are stored in Google Cloud Storage, keeping the 3 most recent backups.

**Access your app at:** `http://YOUR_EXTERNAL_IP:8000`  
**API docs at:** `http://YOUR_EXTERNAL_IP:8000/docs`

### Monitoring

```bash
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

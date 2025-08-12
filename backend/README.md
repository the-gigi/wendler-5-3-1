# Wendler 5-3-1 Backend

FastAPI backend for the Wendler 5-3-1 workout tracking application. Handles user authentication via OAuth (Google, GitHub, Facebook), 1RM data storage, and onboarding flow.

## Features

- **OAuth Authentication**: Google, GitHub, and Facebook login support
- **User Management**: User registration, JWT token management
- **1RM Tracking**: CRUD operations for one-rep-max data for the 4 main lifts
- **Onboarding Flow**: New user setup with initial 1RM entry
- **Database**: SQLite with SQLAlchemy ORM and Alembic migrations

## Setup

### Prerequisites
- Python 3.12+
- uv (Python package manager)

### First Time Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   GITHUB_CLIENT_ID=your_github_client_id_here
   GITHUB_CLIENT_SECRET=your_github_client_secret_here
   FACEBOOK_CLIENT_ID=your_facebook_client_id_here
   FACEBOOK_CLIENT_SECRET=your_facebook_client_secret_here
   JWT_SECRET=your_secure_random_string_here
   ```

3. **Set up database**:
   ```bash
   uv run alembic upgrade head
   ```

### Getting OAuth Credentials

#### Google OAuth:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create OAuth 2.0 Client ID
5. Add redirect URI: `http://localhost:8000/auth/google/callback`
6. Copy Client ID and Secret to `.env`

#### GitHub OAuth:
1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Set Authorization callback URL: `http://localhost:8000/auth/github/callback`
4. Copy Client ID and Secret to `.env`

#### Facebook OAuth:
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create App → Consumer
3. Add Facebook Login product
4. Set Valid OAuth Redirect URI: `http://localhost:8000/auth/facebook/callback`
5. Copy App ID and Secret to `.env`

## Running

### Development
```bash
uv run main.py
```

Server will start at `http://localhost:8000`

### API Documentation
Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── main.py              # FastAPI application and routes
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic schemas for API validation
├── crud.py              # Database operations
├── database.py          # Database configuration
├── alembic/             # Database migrations
├── .env.example         # Environment variables template
└── wendler.db           # SQLite database (created after first run)
```

## API Endpoints

### Authentication
- `GET /auth/{provider}` - Initiate OAuth login
- `GET /auth/{provider}/callback` - OAuth callback
- `GET /me` - Get current user info

### 1RM Management
- `GET /one-rms` - Get all user's 1RM records
- `GET /one-rms/{movement}` - Get specific movement 1RM
- `POST /one-rms` - Create new 1RM record
- `PUT /one-rms/{movement}` - Update existing 1RM
- `DELETE /one-rms/{movement}` - Delete 1RM record

### Onboarding
- `POST /onboarding` - Complete user onboarding with all 4 1RMs
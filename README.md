# Wendler 5-3-1 Training App

[![CI Pipeline](https://github.com/gigi/wendler-5-3-1/actions/workflows/ci.yml/badge.svg)](https://github.com/gigi/wendler-5-3-1/actions/workflows/ci.yml)
[![Backend Tests](https://github.com/gigi/wendler-5-3-1/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/gigi/wendler-5-3-1/actions/workflows/backend-tests.yml)
[![Frontend Tests](https://github.com/gigi/wendler-5-3-1/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/gigi/wendler-5-3-1/actions/workflows/frontend-tests.yml)

A proper Wendler 5-3-1 app with comprehensive backend and frontend testing!

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

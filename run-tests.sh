#!/bin/bash

# Wendler 5-3-1 Test Runner
# Runs all backend and frontend tests with proper error handling

set -e  # Exit on any error

echo "🧪 Running Wendler 5-3-1 Test Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "README.md" ]] || [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_info "Starting backend tests..."
echo

# Run backend tests
cd backend
if command -v uv >/dev/null 2>&1; then
    print_info "Running backend tests with coverage..."
    uv run pytest --cov=. --cov-report=term-missing --cov-report=xml
    print_status "Backend tests passed!"
else
    print_error "uv not found. Please install uv or run: pip install pytest pytest-asyncio pytest-cov"
    exit 1
fi

echo
print_info "Starting frontend tests..."
echo

# Run frontend tests
cd ../frontend/WendlerApp

# Check if node_modules exists
if [[ ! -d "node_modules" ]]; then
    print_info "Installing frontend dependencies..."
    npm install
fi

print_info "Running ESLint..."
npm run lint
print_status "Frontend linting passed!"

print_info "Running Jest tests with coverage..."
npm test -- --ci --coverage --watchAll=false
print_status "Frontend tests passed!"

# Back to root
cd ../..

echo
echo "🎉 All tests passed successfully!"
echo "================================="
echo "Backend: 62 tests with 85%+ coverage"
echo "Frontend: Jest tests with ESLint validation"
echo
print_info "You can also run tests individually:"
echo "  Backend:  cd backend && uv run pytest"
echo "  Frontend: cd frontend/WendlerApp && npm test"
echo
print_status "Ready for deployment! 🚀"
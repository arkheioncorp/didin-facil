# Justfile for TikTrend Finder

# List available commands
default:
    @just --list

# --- Development ---

# Start all services (Docker + Tauri)
dev:
    @echo "Starting Docker services..."
    cd docker && docker compose up -d
    @echo "Starting Tauri app..."
    npm run tauri dev

# Start only backend services
dev-backend:
    cd docker && docker compose up -d

# Start only frontend
dev-frontend:
    npm run dev

# --- Testing ---

# Run all tests
test: test-unit test-e2e

# Run unit tests (Frontend + Backend)
test-unit:
    npm run test
    cd backend && pytest

# Run E2E tests
test-e2e:
    npm run test:e2e

# --- Linting ---

# Lint everything
lint: lint-frontend lint-backend lint-rust

# Lint Frontend
lint-frontend:
    npm run lint

# Lint Backend (Python)
lint-backend:
    cd backend && ruff check .

# Lint Rust
lint-rust:
    cd src-tauri && cargo clippy -- -D warnings

# --- Build ---

# Build everything
build: build-frontend build-app

# Build Frontend
build-frontend:
    npm run build

# Build Tauri App
build-app:
    npm run tauri build

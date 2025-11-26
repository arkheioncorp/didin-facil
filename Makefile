.PHONY: dev build test lint format clean docker-up docker-down setup

dev:
	@echo "Starting development environment..."
	@make -j 2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn api.main:app --reload

dev-frontend:
	npm run tauri dev

build:
	@echo "Building application..."
	npm run build
	npm run tauri build

test:
	@echo "Running tests..."
	npm run test
	cd backend && pytest

lint:
	@echo "Linting..."
	npm run lint
	cd backend && flake8 .

format:
	@echo "Formatting..."
	npm run format
	cd backend && black .

clean:
	rm -rf dist
	rm -rf src-tauri/target
	find . -type d -name "__pycache__" -exec rm -rf {} +

docker-up:
	docker-compose -f docker/docker-compose.yml up -d --build

docker-down:
	docker-compose -f docker/docker-compose.yml down

setup:
	@echo "Setting up project..."
	./scripts/install.sh

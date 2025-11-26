#!/bin/bash

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running."
  exit 1
fi

echo "Starting Backend Services..."
cd docker && docker compose up -d

echo "Starting Tauri App..."
cd ..
npm run tauri dev

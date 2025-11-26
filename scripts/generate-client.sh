#!/bin/bash

# Generate TypeScript client from FastAPI OpenAPI spec
# Requires: openapi-typescript-codegen

API_URL="http://localhost:8000/openapi.json"
OUTPUT_DIR="./src/services/api"

echo "Generating API client from $API_URL..."

# Check if openapi-typescript-codegen is installed
if ! command -v npx &> /dev/null; then
    echo "Error: npx is not installed."
    exit 1
fi

npx openapi-typescript-codegen --input $API_URL --output $OUTPUT_DIR --client axios --name ApiClient

echo "Done! Client generated in $OUTPUT_DIR"

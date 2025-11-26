#!/bin/bash

# Export OpenAPI schema from FastAPI
# Requires backend to be running or importable

echo "Exporting OpenAPI schema..."
cd backend
python -c "from api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > ../docs/openapi.json
echo "Done! Schema saved to docs/openapi.json"

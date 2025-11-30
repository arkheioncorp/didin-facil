#!/bin/bash

# Create subdirectories in docs/
mkdir -p docs/product
mkdir -p docs/technical
mkdir -p docs/api
mkdir -p docs/ops
mkdir -p docs/integrations

# Move Product & Strategy files
mv docs/PRD.md docs/product/ 2>/dev/null
mv docs/USER-STORIES.md docs/product/ 2>/dev/null
mv docs/ROADMAP.md docs/product/ 2>/dev/null
mv docs/FAQ.md docs/product/ 2>/dev/null
mv docs/LAUNCH-GUIDE.md docs/product/ 2>/dev/null

# Move Technical Architecture files
mv docs/ARCHITECTURE.md docs/technical/ 2>/dev/null
mv docs/DATABASE-SCHEMA.md docs/technical/ 2>/dev/null
mv docs/SCALING.md docs/technical/ 2>/dev/null
mv docs/SECURITY.md docs/technical/ 2>/dev/null

# Move API & Development files
mv docs/API-REFERENCE.md docs/api/ 2>/dev/null
mv docs/CHECKOUT-API.md docs/api/ 2>/dev/null
mv docs/TIKTOK-API-REFERENCE.md docs/api/ 2>/dev/null
mv docs/TESTING.md docs/api/ 2>/dev/null

# Move Operations & Deployment files
mv docs/DEPLOYMENT.md docs/ops/ 2>/dev/null
mv docs/DNS-SETUP.md docs/ops/ 2>/dev/null

# Move Integrations & Modules files
mv docs/INTEGRATIONS-GUIDE.md docs/integrations/ 2>/dev/null
mv docs/INTEGRATION-ROADMAP.md docs/integrations/ 2>/dev/null
mv docs/MARKETPLACE-INTEGRATIONS.md docs/integrations/ 2>/dev/null
mv docs/SETUP-INTEGRATIONS.md docs/integrations/ 2>/dev/null
mv docs/VENDOR-MODULES-GUIDE.md docs/integrations/ 2>/dev/null
mv docs/SELLER-BOT.md docs/integrations/ 2>/dev/null
mv docs/YOUTUBE-SETUP.md docs/integrations/ 2>/dev/null

echo "Docs organization complete."

# ============================================================================
# TikTrend Finder - Frontend Dockerfile
# ============================================================================
# React + Vite frontend service
# Build: docker build -f docker/frontend.Dockerfile -t tiktrend-frontend .
# ============================================================================

# Stage 1: Builder
FROM node:20-alpine as builder

WORKDIR /app

# Build arguments for environment variables
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Stage 2: Runtime
FROM nginx:alpine

# Copy build artifacts
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx configuration template (from root)
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Railway uses dynamic PORT - nginx:alpine supports envsubst via templates
ENV PORT=80

# Expose port
EXPOSE ${PORT}

CMD ["nginx", "-g", "daemon off;"]

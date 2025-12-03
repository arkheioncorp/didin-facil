# ============================================================================
# TikTrend Finder - Frontend Dockerfile
# ============================================================================
# React + Vite frontend service
# Build: docker build -f docker/frontend.Dockerfile -t tiktrend-frontend .
# ============================================================================

# Stage 1: Builder
FROM node:20-alpine as builder

WORKDIR /app

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

# Copy Nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Railway uses $PORT, but Nginx listens on 80 by default. 
# We need to configure Nginx to listen on $PORT or map it)
# Railway automatically maps the exposed port.
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

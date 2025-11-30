#!/bin/bash
# =============================================================================
# Didin Fácil - Systemd Services Installation Script
# Installs and configures systemd services for production deployment
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/didin-facil"
SERVICE_USER="didin"
SERVICE_GROUP="didin"
SYSTEMD_DIR="/etc/systemd/system"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

create_user() {
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "User $SERVICE_USER already exists"
    else
        log_info "Creating user $SERVICE_USER..."
        useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
        log_success "User $SERVICE_USER created"
    fi
}

create_directories() {
    log_info "Creating directories..."
    
    mkdir -p "$INSTALL_DIR/backend/data"
    mkdir -p "$INSTALL_DIR/backend/logs"
    
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    
    log_success "Directories created"
}

install_services() {
    log_info "Installing systemd services..."
    
    # Copy service files
    cp docker/systemd/didin-scraper.service "$SYSTEMD_DIR/"
    
    # Set permissions
    chmod 644 "$SYSTEMD_DIR/didin-scraper.service"
    
    # Reload systemd
    systemctl daemon-reload
    
    log_success "Services installed"
}

enable_services() {
    log_info "Enabling services..."
    
    systemctl enable didin-scraper.service
    
    log_success "Services enabled"
}

start_services() {
    log_info "Starting services..."
    
    systemctl start didin-scraper.service
    
    log_success "Services started"
}

show_status() {
    echo ""
    log_info "Service Status:"
    echo "================================================"
    systemctl status didin-scraper.service --no-pager || true
    echo "================================================"
    echo ""
    log_info "Useful commands:"
    echo "  - View logs: journalctl -u didin-scraper -f"
    echo "  - Restart: systemctl restart didin-scraper"
    echo "  - Stop: systemctl stop didin-scraper"
    echo "  - Status: systemctl status didin-scraper"
}

# Main
main() {
    echo "================================================"
    echo "  Didin Fácil - Systemd Services Installer"
    echo "================================================"
    echo ""
    
    check_root
    create_user
    create_directories
    install_services
    enable_services
    start_services
    show_status
    
    log_success "Installation complete!"
}

# Run
main "$@"

#!/bin/bash
# Deep Debug Test Runner
# Comprehensive logging and error capture

set -e

DIR="/home/jhonslife/Didin Facil"
LOG_DIR="/tmp/tiktrend-debug"

echo "🔍 TikTrend Deep Debug Session"
echo "================================"
echo ""

# Setup
mkdir -p "$LOG_DIR"
cd "$DIR"

echo "📋 Pre-flight checks..."
echo "  Chrome: $(which google-chrome || echo 'NOT FOUND')"
echo "  Cargo: $(cargo --version)"
echo "  Rust: $(rustc --version)"
echo ""

# Check logging setup
echo "📋 Checking logging implementation..."
grep -r "log::" src-tauri/src/ --include="*.rs" | wc -l | xargs echo "  Log statements found:"
echo ""

# Build check
echo "📋 Building with full debug..."
cd src-tauri
if cargo build 2>&1 | tee "$LOG_DIR/build.log" | grep -E "(error|warning)" | tail -5; then
    echo ""
fi

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "✅ Build successful"
else
    echo "❌ Build failed!"
    echo "See: $LOG_DIR/build.log"
    exit 1
fi

echo ""
echo "📊 Binary stats:"
ls -lh target/debug/tiktrend-finder | awk '{print "  Size: "$5}'
echo ""

# Environment
echo "📋 Environment variables for Tauri:"
echo "  RUST_LOG=debug"
echo "  RUST_BACKTRACE=1"
echo ""

echo "🚀 Ready to start Tauri!"
echo ""
echo "Run with full logging:"
echo "  RUST_LOG=debug RUST_BACKTRACE=1 cargo tauri dev 2>&1 | tee $LOG_DIR/tauri.log"
echo ""
echo "Logs will be saved to: $LOG_DIR/"
echo ""
echo "To monitor in real-time:"
echo "  tail -f $LOG_DIR/tauri.log"

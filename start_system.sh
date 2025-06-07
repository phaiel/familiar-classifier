#!/bin/bash

# 🧠 Familiar Classifier - Complete System Startup
# Starts both hot path service and UI in the correct order

set -e

echo "🧠 Familiar Classifier - Complete System Startup"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    print_error "Cargo (Rust) not found. Please install Rust: https://rustup.rs/"
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    print_error "Python not found. Please install Python 3.8+."
    exit 1
fi

# Determine Python command
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

print_status "Using Python: $PYTHON_CMD"

# Check if UI dependencies are installed
print_status "Checking UI dependencies..."
if ! $PYTHON_CMD -c "import streamlit" &> /dev/null; then
    print_warning "Installing UI dependencies..."
    $PYTHON_CMD -m pip install -r ui/requirements.txt
    if [ $? -eq 0 ]; then
        print_success "UI dependencies installed"
    else
        print_error "Failed to install UI dependencies"
        exit 1
    fi
else
    print_success "UI dependencies already installed"
fi

# Build hot path service
print_status "Building hot path service..."
cd hot_path
if cargo build --release; then
    print_success "Hot path service built successfully"
else
    print_error "Failed to build hot path service"
    exit 1
fi
cd ..

# Start hot path service in background
print_status "Starting hot path service on port 3000..."
cd hot_path
cargo run --release > ../hot_path.log 2>&1 &
HOT_PATH_PID=$!
cd ..

# Wait for hot path to start
print_status "Waiting for hot path service to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        print_success "Hot path service is running (PID: $HOT_PATH_PID)"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Hot path service failed to start within 30 seconds"
        print_error "Check hot_path.log for details"
        kill $HOT_PATH_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Load patterns
print_status "Loading patterns into hot path..."
if curl -s -X POST http://localhost:3000/reload-patterns -H "Content-Type: application/json" -d '{}' > /dev/null; then
    print_success "Patterns loaded successfully"
else
    print_warning "Pattern loading failed - you can reload manually from the UI"
fi

# Start UI
print_status "Starting Streamlit UI on port 8501..."
print_success "System startup complete!"
echo ""
echo "🌐 Access the UI at: http://localhost:8501"
echo "🔥 Hot path API at: http://localhost:3000"
echo "📋 Hot path logs: hot_path.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Cleanup function
cleanup() {
    echo ""
    print_status "Shutting down services..."
    kill $HOT_PATH_PID 2>/dev/null || true
    print_success "All services stopped"
    exit 0
}

# Trap cleanup function on script exit
trap cleanup INT TERM

# Start UI (this will run in foreground)
cd ui
$PYTHON_CMD run_ui.py

# This line should never be reached, but just in case
cleanup 
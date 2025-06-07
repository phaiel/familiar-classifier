#!/bin/bash
set -e

echo "🧠 Familiar Pattern Classification - Native Setup (No Docker)"
echo "=========================================================="

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✅ Poetry check passed"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
poetry install

# Install Qdrant natively (multiple options)
echo ""
echo "🗂️  Setting up Qdrant vector database..."

# Option 1: Try Homebrew (macOS)
if command -v brew &> /dev/null; then
    echo "🍺 Installing Qdrant via Homebrew..."
    brew install qdrant/tap/qdrant || echo "Homebrew install failed, trying other methods..."
fi

# Option 2: Download binary (Linux/macOS)
if ! command -v qdrant &> /dev/null; then
    echo "📥 Downloading Qdrant binary..."
    
    # Detect OS
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    if [[ "$ARCH" == "x86_64" ]]; then
        ARCH="x86_64"
    elif [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "aarch64" ]]; then
        ARCH="aarch64"
    fi
    
    QDRANT_VERSION="v1.7.4"
    DOWNLOAD_URL="https://github.com/qdrant/qdrant/releases/download/${QDRANT_VERSION}/qdrant-${OS}-${ARCH}"
    
    # Create local bin directory
    mkdir -p ~/.local/bin
    
    # Download and install
    curl -L "$DOWNLOAD_URL" -o ~/.local/bin/qdrant
    chmod +x ~/.local/bin/qdrant
    
    # Add to PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc 2>/dev/null || true
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
fi

# Start Qdrant in background
echo ""
echo "🚀 Starting Qdrant server..."
mkdir -p ./qdrant_data
qdrant --storage-path ./qdrant_data &
QDRANT_PID=$!

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:6333/health &> /dev/null; then
        echo "✅ Qdrant is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Qdrant failed to start after 30 seconds"
        kill $QDRANT_PID 2>/dev/null || true
        exit 1
    fi
    
    sleep 1
done

# Build pattern index
echo ""
echo "🔧 Building pattern index..."
poetry run python -m cold_path.tools.build_pattern_index --overwrite

# Test classification
echo ""
echo "🧪 Testing classification..."
poetry run python -m cold_path.cli test-classify "He napped in his crib early this morning"

echo ""
echo "🎉 Native setup completed successfully!"
echo ""
echo "Qdrant is running with PID: $QDRANT_PID"
echo "To stop Qdrant later: kill $QDRANT_PID"
echo ""
echo "Next steps:"
echo "  1. Start the classification service:"
echo "     poetry run python -m hot_path.classifier_service"
echo ""
echo "  2. Test the API:"
echo "     python examples/basic_usage.py"
echo ""
echo "  3. Manage patterns:"
echo "     poetry run python -m cold_path.cli --help" 
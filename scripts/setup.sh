#!/bin/bash
set -e

echo "🧠 Familiar Pattern Classification - Setup Script"
echo "================================================"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker not running. Please start Docker first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
poetry install

# Start Qdrant
echo ""
echo "🚀 Starting Qdrant vector database..."
docker-compose up -d qdrant

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:6333/health &> /dev/null; then
        echo "✅ Qdrant is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Qdrant failed to start after 30 seconds"
        exit 1
    fi
    
    sleep 1
done

# Export schemas for Rust bridge (Python cold path)
echo ""
echo "🌉 Exporting schemas for hot path bridge..."
poetry run python -m cold_path.bridge_cli bridge-export

# Build pattern index (Python cold path)
echo ""
echo "🔧 Building pattern index..."
poetry run python -m cold_path.tools.build_pattern_index --overwrite

# Verify index
echo ""
echo "🔍 Verifying pattern index..."
poetry run python -m cold_path.cli validate-patterns

# Build Rust hot path service
echo ""
echo "🦀 Building Rust hot path service..."
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust/Cargo not found. Please install Rust first:"
    echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

cd hot_path
cargo build --release
cd ..

# Test classification (Python CLI can still test the pattern loading)
echo ""
echo "🧪 Testing pattern validation..."
poetry run python -m cold_path.cli validate-patterns

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Architecture:"
echo "  🧊 Cold Path (Python): Pattern definitions, schema validation, index building"
echo "  🔥 Hot Path (Rust): High-performance classification service"
echo ""
echo "Next steps:"
echo "  1. Start the Rust classification service:"
echo "     cd hot_path && cargo run --release"
echo ""
echo "  2. In another terminal, test the API:"
echo "     curl -X POST http://localhost:8000/classify \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"text\": \"He napped in his crib early this morning\"}'"
echo ""
echo "  3. Use the Python CLI for pattern management:"
echo "     poetry run python -m cold_path.cli --help"
echo ""
echo "  4. View API documentation (once Rust service is running):"
echo "     http://localhost:8000/" 
#!/usr/bin/env python3
"""
🚀 Familiar Classifier UI Launcher
Starts the Streamlit web interface for pattern creation and classification testing
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import requests
        import yaml
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install -r ui/requirements.txt")
        return False

def check_hot_path_service():
    """Check if the hot path service is running."""
    try:
        import requests
        response = requests.get("http://localhost:3000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Hot path service is running")
            return True
        else:
            print(f"⚠️ Hot path service responded with status {response.status_code}")
            return False
    except Exception:
        print("⚠️ Hot path service not running")
        print("   Start with: cd hot_path && cargo run")
        return False

def main():
    """Main launcher function."""
    print("🧠 Familiar Classifier UI Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check hot path service (optional)
    check_hot_path_service()
    
    # Ensure we're in the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"Working directory: {os.getcwd()}")
    print(f"UI directory: {Path(__file__).parent}")
    
    # Set UI directory for Streamlit
    ui_dir = Path(__file__).parent
    
    print("\n🚀 Starting Streamlit UI...")
    print("📍 UI will be available at: http://localhost:8501")
    print("⌨️  Press Ctrl+C to stop")
    print()
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(ui_dir / "app.py"),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 UI stopped")
    except Exception as e:
        print(f"❌ Error starting UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
#!/bin/bash

# Build script for PDN Chat deployment
# This script handles dependency installation with proper error handling

set -e  # Exit on any error

echo "Starting build process..."

# Upgrade pip first
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Clear any existing packages that might conflict
echo "Clearing conflicting packages..."
pip uninstall -y cryptography || true

# Install requirements with constraints
echo "Installing requirements with constraints..."
pip install --no-cache-dir --force-reinstall -r requirements.txt -c constraints.txt

# Verify cryptography installation
echo "Verifying cryptography installation..."
python -c "import cryptography; print(f'Cryptography version: {cryptography.__version__}')"

echo "Build completed successfully!"

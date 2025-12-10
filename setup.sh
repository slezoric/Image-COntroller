#!/bin/bash

# Define the virtual environment directory name
VENV_DIR="venv"

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created in $VENV_DIR"
else
    echo "Virtual environment already exists in $VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo "Dependencies installed."
else
    echo "requirements.txt not found."
fi

echo "Setup complete. To activate the virtual environment, run:"
echo "source $VENV_DIR/bin/activate"

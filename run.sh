#!/bin/bash

# Script ko location ma jane
cd "$(dirname "$0")"

# Path settings
ENV_PATH="../env"
DOTENV_FILE="../.env"

# 1. Python Check
if command -v python3 &>/dev/null; then
    PYTHON_EXE="python3"
elif command -v python &>/dev/null; then
    PYTHON_EXE="python"
else
    echo "Error: Python install bhayeko chaina!"
    exit 1
fi

echo "Using $PYTHON_EXE..."

# 2. Virtual Environment Activate
if [ -d "$ENV_PATH/Scripts" ]; then
    source "$ENV_PATH/Scripts/activate"
elif [ -d "$ENV_PATH/bin" ]; then
    source "$ENV_PATH/bin/activate"
else
    echo "Error: Virtual environment bhetiyena!"
    exit 1
fi

# 3. Dependencies Install
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# 4. Django Run (Migrations + Server)
if [ -f "manage.py" ]; then
    # Yadi .env bahira chha bhane, manually export garne (Optional but safe)
    if [ -f "$DOTENV_FILE" ]; then
        echo "Loading environment variables from $DOTENV_FILE"
        # Exporting variables so Django can see them
        export $(grep -v '^#' "$DOTENV_FILE" | xargs)
    fi

    echo "Applying migrations..."
    python manage.py makemigrations
    python manage.py migrate

    echo "----------------------------------------"
    echo "Setup Complete! Starting Django Server..."
    echo "----------------------------------------"
    python manage.py runserver
else
    echo "Error: manage.py bhetiyena!"
    exit 1
fi
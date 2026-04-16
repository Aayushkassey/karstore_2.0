#!/bin/bash

# Virtual environment folder ko naam
ENV_NAME="env"
# Django project folder jaha manage.py chha
PROJECT_FOLDER="karstore"

# 1. Correct Python command bhetaune
if command -v python3 &>/dev/null; then
    PYTHON_EXE="python3"
elif command -v python &>/dev/null; then
    PYTHON_EXE="python"
else
    echo "Error: Python install bhayeko chaina!"
    exit 1
fi

echo "Using $PYTHON_EXE..."

# 2. Virtual environment chaina bhane banaune
if [ ! -d "$ENV_NAME" ]; then
    echo "Creating virtual environment: $ENV_NAME..."
    $PYTHON_EXE -m venv $ENV_NAME
fi

# 3. Environment activate garne (Windows/Git Bash ra Linux/Mac dubai ko lagi)
if [ -d "$ENV_NAME/Scripts" ]; then
    source $ENV_NAME/Scripts/activate
else
    source $ENV_NAME/bin/activate
fi

# 4. Dependencies install garne
echo "Installing/Updating dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt bhetiyena!"
fi

# 5. Django Project vitra gayera migrations ra server start garne
if [ -d "$PROJECT_FOLDER" ]; then
    echo "Entering $PROJECT_FOLDER folder..."
    cd $PROJECT_FOLDER
    
    echo "Applying database migrations..."
    python manage.py makemigrations
    python manage.py migrate

    echo "----------------------------------------"
    echo "Setup Complete! Starting Django Server..."
    echo "----------------------------------------"
    python manage.py runserver
else
    echo "Error: $PROJECT_FOLDER folder bhetiyena! manage.py check gara."
    exit 1
fi
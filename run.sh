#!/bin/bash

# Path settings
# Virtual environment root ma chha, tesaile path milayeko
ENV_PATH="../env"
# Django project vitrai run.sh vako le folder name chahidaina
# Tara manage.py yehi folder ma chha ki nai check garne

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

# 2. Virtual environment activate garne (Root directory bata)
if [ -d "$ENV_PATH/Scripts" ]; then
    source $ENV_PATH/Scripts/activate
elif [ -d "$ENV_PATH/bin" ]; then
    source $ENV_PATH/bin/activate
else
    echo "Error: Virtual environment 'env' root folder ma bhetiyena!"
    exit 1
fi

# 3. Dependencies install garne (Yehi folder ko requirements.txt bata)
echo "Installing/Updating dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt yehi folder ma bhetiyena!"
fi

# 4. Django migrations ra server start garne
if [ -f "manage.py" ]; then
    echo "Applying database migrations..."
    python manage.py makemigrations
    python manage.py migrate

    echo "----------------------------------------"
    echo "Setup Complete! Starting Django Server..."
    echo "----------------------------------------"
    python manage.py runserver
else
    echo "Error: manage.py bhetiyena! script 'karstore' folder bhitra rakha."
    exit 1
fi
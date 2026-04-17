#!/bin/bash

# Script भएको फोल्डरमा जाने
cd "$(dirname "$0")"

# Path settings: 'env' र '.env' अहिलेकै फोल्डर (..) भन्दा बाहिर वा सँगै छन्
# यदि 'env' फोल्डर 'karstore' भित्रै छ भने "./env" राख्नुहोस्
# यदि 'env' फोल्डर 'karstore' को बाहिर छ भने "../env" ठिक छ
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
    echo "Error: Virtual environment bhetiyena! Path milayera check garnuhos: $ENV_PATH"
    exit 1
fi

# 3. Dependencies Install
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# 4. Django Run
if [ -f "manage.py" ]; then
    # .env फाइल लोड गर्ने
    if [ -f "$DOTENV_FILE" ]; then
        echo "Loading environment variables from $DOTENV_FILE"
        export $(grep -v '^#' "$DOTENV_FILE" | xargs)
    fi

    echo "Applying migrations..."
    $PYTHON_EXE manage.py makemigrations
    $PYTHON_EXE manage.py migrate

    echo "----------------------------------------"
    echo "Setup Complete! Starting Django Server..."
    echo "----------------------------------------"
    $PYTHON_EXE manage.py runserver
else
    echo "Error: manage.py bhetiyena!"
    exit 1
fi
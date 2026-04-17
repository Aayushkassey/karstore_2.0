#!/bin/bash
cd ..
py -m pip install python-decouple
if [ -d "karstore_2.0" ]; then
    cd karstore_2.0
else
    cd karstore
fi
# 1. Virtual environment chhaina bhane banaune (Install garne part)
if [ ! -d "../env" ]; then
    echo "Virtual environment bhetiyena. Create gardai chhu..."
    python -m venv ../env
fi

# 2. Environment activate garne
source ../env/Scripts/activate 2>/dev/null || source ../env/bin/activate

# 3. Dependencies install garne
echo "Installing/Updating dependencies..."
pip install -r requirements.txt

# 4. Database setup garne
echo "Migrating database..."
python manage.py makemigrations
python manage.py migrate

# 5. Link dekhaune ra Server start garne
echo ""
echo "------------------------------------------------"
echo "  WEBSITE READY: http://127.0.0.1:8000/"
echo "------------------------------------------------"
echo ""

python manage.py runserver
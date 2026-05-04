#!/bin/bash

# १. Virtual Environment (env) सेटअप
if [ ! -d "env" ]; then
    echo "🚀 Creating Virtual Environment..."
    python -m venv env
fi

# २. Environment Activate गर्ने (Windows/Git Bash र Linux दुवैका लागि)
echo "⚡ Activating environment..."
source env/Scripts/activate 2>/dev/null || source env/bin/activate

# ३. Requirements.txt बाट सबै प्याकेज अपडेट गर्ने
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# ४. Database Migrations चलाउने
echo "📂 Setting up Database..."
python manage.py makemigrations
python manage.py migrate

# ५. सर्भर स्टार्ट गर्ने
echo ""
echo "------------------------------------------------"
echo " ✅ KAR STORE IS READY: http://127.0.0.1:8000/"
echo "------------------------------------------------"
echo ""

python manage.py runserver
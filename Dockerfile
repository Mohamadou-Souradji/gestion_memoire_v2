FROM python:3.11-slim

# Empêche Python de générer des fichiers .pyc et force l'affichage des logs en temps réel
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Installation des dépendances système nécessaires pour PostgreSQL et GCC
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copie l'intégralité du projet
COPY . .

# Render utilise le port 10000 par défaut pour les services Web
EXPOSE 10000

# La commande magique : 
# 1. On applique les migrations (pour que la table OTP existe)
# 2. On collecte les fichiers statiques (pour le design CSS)
# 3. On lance le serveur sur le port 10000
CMD python manage.py migrate --no-input && \
    python manage.py collectstatic --no-input && \
    gunicorn config.wsgi:application --bind 0.0.0.0:10000

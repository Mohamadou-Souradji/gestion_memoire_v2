FROM python:3.11-slim

# Empêche la création de fichiers .pyc et assure un affichage immédiat des logs
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

# Copie du reste du projet
COPY . .

# Rendre le script build.sh exécutable
RUN chmod +x build.sh

# Exposition du port par défaut (Render utilisera 10000)
EXPOSE 8000

# Commande finale : exécute le build (migrations + data) PUIS lance le serveur
CMD sh -c "./build.sh && gunicorn config.wsgi:application --bind 0.0.0.0:10000"

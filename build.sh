#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# SUPPRIME la ligne makemigrations (on ne le fait qu'en local)
python manage.py migrate --no-input

# À laisser uniquement si tu veux réinitialiser les données ESCEP à chaque build
# python manage.py charger_donnees_test

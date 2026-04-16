#!/usr/bin/env bash
set -o errexit

# Installation et statiques
pip install -r requirements.txt
python manage.py collectstatic --no-input

# 1. On force le marquage de la migration problématique comme "faite"
python manage.py migrate etudiant 0003 --fake

# 2. On lance toutes les autres migrations normalement
python manage.py migrate --no-input

# 3. On charge les données ESCEP
python manage.py charger_donnees_test

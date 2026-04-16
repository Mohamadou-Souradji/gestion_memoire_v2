# ESCEP Niger — Guide de déploiement sur Render

## 1. Préparer le dépôt Git

```bash
cd escep_v2
git init
git add .
git commit -m "Initial commit — ESCEP Niger v2"

# Créer le dépôt sur GitHub/GitLab, puis :
git remote add origin https://github.com/VOTRE_USER/escep-niger.git
git push -u origin main
```

---

## 2. Variables d'environnement à créer sur Render

Dans le Dashboard Render → votre Web Service → **Environment** → ajouter :

| Clé | Valeur |
|---|---|
| `SECRET_KEY` | Générer sur [djecrety.ir](https://djecrety.ir) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `escep-niger.onrender.com,votre-domaine.ne` |
| `DATABASE_URL` | Rempli automatiquement par Render PostgreSQL |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST_USER` | votre adresse Gmail |
| `EMAIL_HOST_PASSWORD` | mot de passe d'application Gmail |
| `DEFAULT_FROM_EMAIL` | `ESCEP Niger <noreply@escep.ne>` |
| `ZEROGPT_API_KEY` | votre clé ZeroGPT (gratuit sur zerogpt.com) |
| `GPTZERO_API_KEY` | votre clé GPTZero (optionnel) |
| `AI_DETECTION_THRESHOLD` | `70` |
| `OTP_VALIDITY_MINUTES` | `10` |

---

## 3. Fichiers nécessaires à la racine du projet

### `build.sh`
```bash
#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py charger_donnees_test
```

### `requirements.txt` — ajouter si absent
```
gunicorn
whitenoise
psycopg2-binary
dj-database-url
```

### `Procfile`
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 4. Adapter `settings.py` pour la production

Ajouter en bas de `config/settings.py` :

```python
# ── Production (Render) ────────────────────────────────────
import dj_database_url, os

if not DEBUG:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600, ssl_require=True
    )
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS.split(',') if h]
```

---

## 5. Créer le Web Service sur Render

1. Aller sur **render.com** → **New** → **Web Service**
2. Connecter votre dépôt GitHub
3. Paramètres :
   - **Runtime** : `Python 3`
   - **Build Command** : `./build.sh`
   - **Start Command** : `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
4. **Add PostgreSQL** : New → PostgreSQL → copier l'URL dans `DATABASE_URL`
5. Cliquer **Deploy**

---

## 6. Fichiers media (uploads)

Render ne persiste pas les fichiers uploadés entre déploiements.
Pour les fichiers PDF/images, utilisez un service externe :

**Option recommandée — Cloudinary (gratuit)**

```bash
pip install cloudinary django-cloudinary-storage
```

```python
# settings.py
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY':    config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

Variables Render à ajouter :
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Inscription gratuite sur **cloudinary.com** → Dashboard → copier les 3 clés.

---

## 7. Double authentification (2FA) — processus

Le système envoie un code OTP à 6 chiffres par e-mail à chaque connexion.

### Flux de connexion :
```
Étape 1 : Saisir identifiant + mot de passe
    ↓ (si correct)
Étape 2 : Un code à 6 chiffres est envoyé à l'adresse e-mail du compte
    ↓ (code valable 10 minutes, 3 tentatives max)
Étape 3 : Saisir le code → accès au tableau de bord
```

### Configuration Gmail :
1. Aller sur **myaccount.google.com** → Sécurité
2. Activer la validation en deux étapes
3. Rechercher **"Mots de passe des applications"**
4. Générer un mot de passe pour "Courrier"
5. Copier ce mot de passe (16 caractères) dans `EMAIL_HOST_PASSWORD`

### Fallback (si e-mail non configuré) :
Si `EMAIL_HOST_USER` est vide, la connexion passe directement sans OTP.
Utile en développement local.

---

## 8. Commandes après premier déploiement

```bash
# Via Render Shell (Dashboard → Shell) :
python manage.py createsuperuser
python manage.py charger_donnees_test  # si besoin des données de test
```

---

## Structure simplifiée

```
escep_v2/
├── apps/               # Modules Django par rôle
├── templates/          # Templates HTML
├── static/             # CSS, images, JS
├── config/             # settings.py, urls.py
├── manage.py
├── Procfile            # Démarrage Render/Heroku
├── build.sh            # Script de build
├── requirements.txt
└── .env                # Variables locales (NE PAS pousser sur Git)
```

> **Important** : ajouter `.env` dans `.gitignore` avant de pousser sur Git.

---

## 9. .gitignore recommandé

```gitignore
.env
*.pyc
__pycache__/
staticfiles/
media/
db.sqlite3
.DS_Store
```

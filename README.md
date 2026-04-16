# ESCEP Niger — Plateforme de gestion des mémoires et rapports de stage

## Démarrage rapide

```bash
# 1. Configurer l'e-mail et l'API IA dans .env
# 2. Lancer
docker-compose up --build

# 3. Créer le super-admin (première fois)
docker exec -it escep_web python manage.py createsuperuser

# 4. Accéder à http://localhost:8000
```

---

## Configuration `.env` obligatoire

```env
# ── E-mail (Gmail recommandé) ──────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=MOT_DE_PASSE_APPLICATION_GMAIL

# ── Analyse IA ─────────────────────────────────────────────
# Option 1 : ZeroGPT GRATUIT (recommandé pour démarrer)
# → Inscription : https://zerogpt.com → Dashboard → API Keys
ZEROGPT_API_KEY=votre_cle_zerogpt_ici

# Option 2 : GPTZero (payant ~45$/mois, plus précis)
# → Inscription : https://gptzero.me → API Keys
GPTZERO_API_KEY=votre_cle_gptzero_ici

# Seuil rejet IA (%)
AI_DETECTION_THRESHOLD=70
```

> **Priorité :** ZeroGPT est testé en premier (gratuit). Si la clé est absente, GPTZero est essayé. Sinon l'analyse heuristique locale est utilisée.

> **Comment obtenir la clé ZeroGPT :**
> 1. Aller sur **zerogpt.com** → S'inscrire (email + mot de passe)
> 2. Dashboard → **API** ou **Settings** → **Generate API Key**
> 3. Copier la clé dans `.env` → `ZEROGPT_API_KEY=la_cle_copiee`
> 4. `docker-compose restart web`

> **Gmail** : Paramètres Google → Sécurité → Mots de passe des applications → Générer.
> **GPTZero** : inscription sur gptzero.me, onglet "API Keys", copier la clé.
> Si `GPTZERO_API_KEY` est vide, l'analyse heuristique locale est utilisée.

---

## Comptes de test (chargés automatiquement au démarrage)

| Rôle               | Identifiant         | Mot de passe |
|--------------------|---------------------|--------------|
| Super admin        | `admin`             | `admin123`   |
| Directeur études   | `de_escep`          | `de123`      |
| Direction générale | `dg_escep`          | `dg123`      |
| Bibliothécaire     | `biblio_escep`      | `biblio123`  |
| Chef INFO          | `chef_info`         | `chef123`    |
| Chef TELECOM       | `chef_telecom`      | `chef123`    |
| Chef POSTE         | `chef_poste`        | `chef123`    |
| Jury INFO (pré.)   | `jury_ali`          | `jury123`    |
| Jury TELECOM (pré.)| `jury_issa`         | `jury123`    |
| Étudiants (10)     | `saidou.mahamadou`… | `etud123`    |

**Matricules étudiants INFO :** `2021INFO001` → `2021INFO003`, `2022INFO010`, `2022INFO011`
**Matricules TELECOM :** `2021TELECOM001`, `2021TELECOM002`, `2022TELECOM010`
**Matricules POSTE :** `2021POSTE001`, `2021POSTE002`

> L'étudiant se connecte, puis saisit son matricule + `2024-2025` pour lier son compte.

---

## Workflow complet

```
ÉTUDIANT
  1. Se connecte → saisit son matricule pour lier sa fiche
  2. Propose un thème (vérification similarité ≥75% → rejet automatique)
     Champs : thème, promotion, encadreur, entreprise, lieu, période, description
  3. Chef valide ou rejette avec motif → étudiant notifié
  4. Dépose son dossier (mémoire PDF + 3 quitus PDF/image)
     → Analyse IA automatique 40–60s (GPTZero ou heuristique)
     → Taux ≥ 70% : rejet automatique
     → Taux < 70% : dossier transmis au chef
  5. Chef instruit : valide ou rejette avec motif
  6. Chef propose jury + calendrier → soumis au Directeur des études
  7. DE valide → soumis à la Direction Générale (ou rejette → retour chef)
  8. DG valide → soutenance programmée → TOUS notifiés
     (étudiant, chef, DE, membres jury)
  9. Soutenance → président du jury saisit le PV
     → étudiant et chef notifiés
 10. Étudiant dépose PDF final + quitus président (même page que le dépôt)
     → Analyse IA du document final
     → Chef valide → bibliothèque notifiée
 11. Bibliothécaire indexe et publie le document

REPRODUCTION DU PROCESSUS
  → Possible si l'étudiant est enregistré avec une nouvelle année académique
```

---

## Menus par rôle

### Étudiant
| Lien | Description |
|---|---|
| Tableau de bord | Profil, stats, soutenance, PV, propositions |
| Mon matricule | Lier la fiche étudiant au compte |
| Proposer un thème | Soumission avec vérification anti-doublon |
| Déposer un dossier | Dépôt initial (avant soutenance) ET dépôt final (après PV) |
| Bibliothèque | Consultation des mémoires publiés avec filtres |
| Notifications | Toutes les notifications — clic pour marquer lue |

### Chef de département
| Lien | Description |
|---|---|
| Tableau de bord | Stats + propositions récentes |
| Propositions thèmes | Par défaut : en attente — filtres (nom, année, spécialité, statut) |
| Dossiers soutenance | Par défaut : en instruction + rejetés — voir PDF + taux IA + note |
| Instruire dossiers | Valide_chef + rejete_de — proposer jury et calendrier |
| Mes jurys | CRUD via modaux — identifiant/mot de passe créés |
| Notifications | Toutes les notifications |

### Directeur des études
| Lien | Description |
|---|---|
| Tableau de bord | Stats globales + départements |
| Propositions jury | Filtres — bouton **Valider tout** ou individuellement |
| Étudiants | CRUD complet (ajouter/modifier/supprimer) via modaux |
| Utilisateurs | Créer tous les comptes — affectation département si chef |
| Notifications | |

### Direction générale
| Lien | Description |
|---|---|
| Tableau de bord | Stats globales |
| Validation finale | Propositions validées DE — bouton **Valider tout** ou individuellement |
| Notifications | |

### Jury
| Lien | Description |
|---|---|
| Mes soutenances | Soutenances programmées, mémoire PDF, saisir PV (président seulement) |
| Historique | Soutenances gérées avec résultats |
| Notifications | |

### Bibliothécaire
| Lien | Description |
|---|---|
| Tableau de bord | Résumé + documents à indexer |
| Mémoires | Indexer, publier/dépublier — filtres spécialité, année, promotion |
| Notifications | |

---

## Analyse IA — fonctionnement

**Avec GPTZero (recommandé) :**
- Extrait 5000 caractères du PDF
- Appelle `https://api.gptzero.me/v2/predict/text`
- Retourne `completely_generated_prob * 100`

**Sans clé GPTZero (heuristique locale) :**
- Extraction texte PyPDF2
- Score basé sur : marqueurs IA (fr+en), phrases longues, transitions, vocabulaire générique, densité ponctuation
- Résultat approximatif — moins fiable

**Durée :** 40–60 secondes garanties. L'écran est bloqué avec barre de progression.

---

## Commandes utiles

```bash
# Recharger les données de test (après reset BDD)
docker exec -it escep_web python manage.py charger_donnees_test

# Migrations après modification des modèles
docker exec -it escep_web python manage.py makemigrations
docker exec -it escep_web python manage.py migrate

# Reset complet (supprime toutes les données)
docker-compose down -v && docker-compose up --build
```

---

## Structure du projet

```
escep_v2/
├── apps/
│   ├── authentication/     # User + OTP 2FA (désactivé en mode test)
│   ├── etudiant/           # Modèles principaux + analyse IA
│   ├── chef_departement/   # Gestion dossiers + jurys
│   ├── directeur_etudes/   # Supervision + création comptes
│   ├── direction_generale/ # Validation finale
│   ├── jury/               # Consultation + saisie PV
│   └── bibliotheque/       # Indexation + publication
├── templates/
│   ├── shared/             # base.html, filtres, modaux, notifications (partiaux)
│   └── {role}/             # Templates par rôle
├── static/css/escep.css    # Charte ESCEP — bleu #1A4F8A, jaune #F5C518
├── config/                 # settings.py, urls.py
├── docker-compose.yml
├── Dockerfile
└── .env
```

"""
Commande Django pour insérer des données de test ESCEP Niger.
Usage : python manage.py charger_donnees_test
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.etudiant.models import Departement, Specialite, Etudiant

User = get_user_model()


class Command(BaseCommand):
    help = 'Insère des données de test réalistes pour ESCEP Niger'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Chargement des données de test ESCEP Niger ===\n'))

        self._creer_comptes_administration()
        self._creer_departements_et_chefs()
        self._creer_jurys()
        self._creer_etudiants()

        self.stdout.write(self.style.SUCCESS('\n✔ Données de test insérées avec succès !\n'))
        self._afficher_recapitulatif()

    # ─────────────────────────────────────────────────────────────
    # COMPTES ADMINISTRATION
    # ─────────────────────────────────────────────────────────────
    def _creer_comptes_administration(self):
        self.stdout.write('→ Création des comptes administration...')

        # Super admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@escep.ne',
                password='admin123',
                first_name='Super',
                last_name='Administrateur',
                role='directeur_etudes',
            )

        # Directeur des études
        User.objects.get_or_create(
            username='de_escep',
            defaults=dict(
                email='directeur.etudes@escep.ne',
                first_name='Moussa',
                last_name='ADAMOU',
                role='directeur_etudes',
                telephone='+227 20 72 11 00',
                is_staff=True,
            )
        )[0].set_password('de123')
        User.objects.filter(username='de_escep').update()
        u = User.objects.get(username='de_escep')
        u.set_password('de123')
        u.save()

        # Direction générale
        u, _ = User.objects.get_or_create(
            username='dg_escep',
            defaults=dict(
                email='direction.generale@escep.ne',
                first_name='Aïchatou',
                last_name='MAHAMANE',
                role='direction_generale',
                telephone='+227 20 72 00 01',
            )
        )
        u.set_password('dg123')
        u.save()

        # Bibliothécaire
        u, _ = User.objects.get_or_create(
            username='biblio_escep',
            defaults=dict(
                email='bibliotheque@escep.ne',
                first_name='Fatouma',
                last_name='SOULEY',
                role='bibliotheque',
                telephone='+227 20 72 00 05',
            )
        )
        u.set_password('biblio123')
        u.save()

        self.stdout.write(self.style.SUCCESS('  ✔ Comptes administration créés'))

    # ─────────────────────────────────────────────────────────────
    # DÉPARTEMENTS, SPÉCIALITÉS ET CHEFS
    # ─────────────────────────────────────────────────────────────
    def _creer_departements_et_chefs(self):
        self.stdout.write('→ Création des départements et chefs...')

        donnees = [
            {
                'dept': {'code': 'INFO', 'nom': 'Informatique', 'description': 'Département Informatique et Systèmes'},
                'chef': {
                    'username': 'chef_info',
                    'first_name': 'Ibrahim',
                    'last_name': 'HAROUNA',
                    'email': 'chef.info@escep.ne',
                    'telephone': '+227 96 11 22 33',
                    'password': 'chef123',
                },
                'specialites': [
                    {'code': 'L3-GL',  'nom': 'Génie Logiciel',           'niveau': 'L3'},
                    {'code': 'M1-SI',  'nom': 'Systèmes Informatiques',   'niveau': 'M1'},
                    {'code': 'M2-GL',  'nom': 'Génie Logiciel',           'niveau': 'M2'},
                ],
            },
            {
                'dept': {'code': 'TELECOM', 'nom': 'Télécommunications', 'description': 'Département Télécommunications et Réseaux'},
                'chef': {
                    'username': 'chef_telecom',
                    'first_name': 'Oumarou',
                    'last_name': 'ISSOUFOU',
                    'email': 'chef.telecom@escep.ne',
                    'telephone': '+227 96 44 55 66',
                    'password': 'chef123',
                },
                'specialites': [
                    {'code': 'L3-RDS', 'nom': 'Réseaux et Systèmes',      'niveau': 'L3'},
                    {'code': 'M1-RT',  'nom': 'Réseaux et Télécoms',      'niveau': 'M1'},
                    {'code': 'M2-RDS', 'nom': 'Réseaux et Systèmes',      'niveau': 'M2'},
                ],
            },
            {
                'dept': {'code': 'POSTE', 'nom': 'Poste et Services Postaux', 'description': 'Département Poste et Services'},
                'chef': {
                    'username': 'chef_poste',
                    'first_name': 'Mariama',
                    'last_name': 'ABDOU',
                    'email': 'chef.poste@escep.ne',
                    'telephone': '+227 96 77 88 99',
                    'password': 'chef123',
                },
                'specialites': [
                    {'code': 'L3-SP',  'nom': 'Services Postaux',         'niveau': 'L3'},
                    {'code': 'M1-GLP', 'nom': 'Gestion et Logistique Postale', 'niveau': 'M1'},
                ],
            },
        ]

        for d in donnees:
            # Créer le chef
            chef, _ = User.objects.get_or_create(
                username=d['chef']['username'],
                defaults=dict(
                    first_name=d['chef']['first_name'],
                    last_name=d['chef']['last_name'],
                    email=d['chef']['email'],
                    telephone=d['chef']['telephone'],
                    role='chef_departement',
                )
            )
            chef.set_password(d['chef']['password'])
            chef.save()

            # Créer le département avec ce chef
            dept, _ = Departement.objects.get_or_create(
                code=d['dept']['code'],
                defaults=dict(
                    nom=d['dept']['nom'],
                    description=d['dept']['description'],
                    chef=chef,
                )
            )
            if dept.chef != chef:
                dept.chef = chef
                dept.save()

            # Créer les spécialités
            for s in d['specialites']:
                Specialite.objects.get_or_create(
                    departement=dept,
                    code=s['code'],
                    defaults=dict(nom=s['nom'], niveau=s['niveau'])
                )

        self.stdout.write(self.style.SUCCESS('  ✔ 3 départements, 8 spécialités, 3 chefs créés'))

    # ─────────────────────────────────────────────────────────────
    # JURYS
    # ─────────────────────────────────────────────────────────────
    def _creer_jurys(self):
        self.stdout.write('→ Création des membres de jury...')
        from apps.chef_departement.models import MembreJury

        jurys_data = [
            # Jury département INFO
            {
                'chef_username': 'chef_info',
                'membres': [
                    {
                        'username': 'jury_ali',
                        'nom': 'MAIDADJI', 'prenom': 'Ali',
                        'email': 'ali.maidadji@escep.ne',
                        'telephone': '+227 91 11 22 33',
                        'specialite': 'Génie Logiciel, Bases de données',
                        'statut': 'permanent',
                        'password': 'jury123',
                    },
                    {
                        'username': 'jury_sani',
                        'nom': 'GARBA', 'prenom': 'Sani',
                        'email': 'sani.garba@escep.ne',
                        'telephone': '+227 91 33 44 55',
                        'specialite': 'Intelligence Artificielle, Python',
                        'statut': 'vacataire',
                        'password': 'jury123',
                    },
                    {
                        'username': 'jury_zara',
                        'nom': 'MOUSSA', 'prenom': 'Zara',
                        'email': 'zara.moussa@escep.ne',
                        'telephone': '+227 91 55 66 77',
                        'specialite': 'Systèmes embarqués, C/C++',
                        'statut': 'permanent',
                        'password': 'jury123',
                    },
                ],
            },
            # Jury département TELECOM
            {
                'chef_username': 'chef_telecom',
                'membres': [
                    {
                        'username': 'jury_issa',
                        'nom': 'TAHIROU', 'prenom': 'Issa',
                        'email': 'issa.tahirou@escep.ne',
                        'telephone': '+227 92 11 22 33',
                        'specialite': 'Réseaux IP, Cisco',
                        'statut': 'permanent',
                        'password': 'jury123',
                    },
                    {
                        'username': 'jury_halima',
                        'nom': 'IBRAHIM', 'prenom': 'Halima',
                        'email': 'halima.ibrahim@escep.ne',
                        'telephone': '+227 92 44 55 66',
                        'specialite': 'Télécommunications mobiles, 4G/5G',
                        'statut': 'vacataire',
                        'password': 'jury123',
                    },
                ],
            },
            # Jury département POSTE
            {
                'chef_username': 'chef_poste',
                'membres': [
                    {
                        'username': 'jury_boube',
                        'nom': 'HASSANE', 'prenom': 'Boubacar',
                        'email': 'boubacar.hassane@escep.ne',
                        'telephone': '+227 93 11 22 33',
                        'specialite': 'Logistique, Supply Chain',
                        'statut': 'permanent',
                        'password': 'jury123',
                    },
                ],
            },
        ]

        for data in jurys_data:
            chef = User.objects.get(username=data['chef_username'])
            for m in data['membres']:
                # Créer le compte User du jury
                user_jury, _ = User.objects.get_or_create(
                    username=m['username'],
                    defaults=dict(
                        first_name=m['prenom'],
                        last_name=m['nom'],
                        email=m['email'],
                        telephone=m['telephone'],
                        role='jury',
                    )
                )
                user_jury.set_password(m['password'])
                user_jury.save()

                # Créer la fiche MembreJury
                jury_obj, _ = MembreJury.objects.get_or_create(
                    email=m['email'],
                    defaults=dict(
                        chef=chef,
                        user=user_jury,
                        nom=m['nom'],
                        prenom=m['prenom'],
                        telephone=m['telephone'],
                        specialite=m['specialite'],
                        statut=m['statut'],
                    )
                )
                if jury_obj.user != user_jury:
                    jury_obj.user = user_jury
                    jury_obj.save()

        self.stdout.write(self.style.SUCCESS('  ✔ 6 membres de jury créés'))

    # ─────────────────────────────────────────────────────────────
    # ÉTUDIANTS
    # ─────────────────────────────────────────────────────────────
    def _creer_etudiants(self):
        self.stdout.write('→ Création des étudiants...')

        etudiants_data = [
            # ── Département INFO — L3-GL ──────────────────────────
            {
                'matricule': '2021INFO001',
                'nom': 'MAHAMADOU', 'prenom': 'Saidou',
                'email': 'saidou.mahamadou@etudiant.escep.ne',
                'specialite_code': 'L3-GL',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'saidou.mahamadou',
                'password': 'etud123',
            },
            {
                'matricule': '2021INFO002',
                'nom': 'ABDOULAYE', 'prenom': 'Hadiza',
                'email': 'hadiza.abdoulaye@etudiant.escep.ne',
                'specialite_code': 'L3-GL',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'hadiza.abdoulaye',
                'password': 'etud123',
            },
            {
                'matricule': '2021INFO003',
                'nom': 'SOUNTALMA', 'prenom': 'Moussa',
                'email': 'moussa.sountalma@etudiant.escep.ne',
                'specialite_code': 'L3-GL',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'moussa.sountalma',
                'password': 'etud123',
            },
            # ── Département INFO — M2-GL ──────────────────────────
            {
                'matricule': '2022INFO010',
                'nom': 'OUMAROU', 'prenom': 'Aïssatou',
                'email': 'aissatou.oumarou@etudiant.escep.ne',
                'specialite_code': 'M2-GL',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'aissatou.oumarou',
                'password': 'etud123',
            },
            {
                'matricule': '2022INFO011',
                'nom': 'GARBA', 'prenom': 'Alhassane',
                'email': 'alhassane.garba@etudiant.escep.ne',
                'specialite_code': 'M2-GL',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'alhassane.garba',
                'password': 'etud123',
            },
            # ── Département TELECOM — L3-RDS ─────────────────────
            {
                'matricule': '2021TELECOM001',
                'nom': 'HAMIDOU', 'prenom': 'Rachidatou',
                'email': 'rachidatou.hamidou@etudiant.escep.ne',
                'specialite_code': 'L3-RDS',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'rachidatou.hamidou',
                'password': 'etud123',
            },
            {
                'matricule': '2021TELECOM002',
                'nom': 'MOUTARI', 'prenom': 'Illiassou',
                'email': 'illiassou.moutari@etudiant.escep.ne',
                'specialite_code': 'L3-RDS',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'illiassou.moutari',
                'password': 'etud123',
            },
            # ── Département TELECOM — M2-RDS ─────────────────────
            {
                'matricule': '2022TELECOM010',
                'nom': 'SALIFOU', 'prenom': 'Nafissa',
                'email': 'nafissa.salifou@etudiant.escep.ne',
                'specialite_code': 'M2-RDS',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'nafissa.salifou',
                'password': 'etud123',
            },
            # ── Département POSTE — L3-SP ─────────────────────────
            {
                'matricule': '2021POSTE001',
                'nom': 'ISSAKA', 'prenom': 'Balkissa',
                'email': 'balkissa.issaka@etudiant.escep.ne',
                'specialite_code': 'L3-SP',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'balkissa.issaka',
                'password': 'etud123',
            },
            {
                'matricule': '2021POSTE002',
                'nom': 'CHAIBOU', 'prenom': 'Adamou',
                'email': 'adamou.chaibou@etudiant.escep.ne',
                'specialite_code': 'L3-SP',
                'annee_academique': '2024-2025',
                'promotion': 'Promotion 2025',
                'username': 'adamou.chaibou',
                'password': 'etud123',
            },
        ]

        for e in etudiants_data:
            spe = Specialite.objects.get(code=e['specialite_code'])

            # Créer le compte User de l'étudiant
            user, _ = User.objects.get_or_create(
                username=e['username'],
                defaults=dict(
                    first_name=e['prenom'],
                    last_name=e['nom'],
                    email=e['email'],
                    role='etudiant',
                )
            )
            user.set_password(e['password'])
            user.save()

            # Créer la fiche étudiant (NON liée au User — liée via vérification matricule)
            Etudiant.objects.get_or_create(
                matricule=e['matricule'],
                defaults=dict(
                    nom=e['nom'],
                    prenom=e['prenom'],
                    email=e['email'],
                    specialite=spe,
                    annee_academique=e['annee_academique'],
                    promotion=e['promotion'],
                    # user=None intentionnellement — sera lié quand l'étudiant
                    # saisit son matricule sur la plateforme
                )
            )

        self.stdout.write(self.style.SUCCESS('  ✔ 10 étudiants créés (fiches + comptes)'))

    # ─────────────────────────────────────────────────────────────
    # RÉCAPITULATIF
    # ─────────────────────────────────────────────────────────────
    def _afficher_recapitulatif(self):
        self.stdout.write('\n' + '='*55)
        self.stdout.write(self.style.MIGRATE_HEADING('  COMPTES DE TEST ESCEP NIGER'))
        self.stdout.write('='*55)
        self.stdout.write(self.style.WARNING('\n  ADMINISTRATION'))
        self.stdout.write('  Rôle                Identifiant       Mot de passe')
        self.stdout.write('  ─────────────────────────────────────────────────')
        self.stdout.write('  Super admin         admin             admin123')
        self.stdout.write('  Directeur études    de_escep          de123')
        self.stdout.write('  Direction générale  dg_escep          dg123')
        self.stdout.write('  Bibliothécaire      biblio_escep      biblio123')
        self.stdout.write(self.style.WARNING('\n  CHEFS DE DÉPARTEMENT'))
        self.stdout.write('  Département         Identifiant       Mot de passe')
        self.stdout.write('  ─────────────────────────────────────────────────')
        self.stdout.write('  Informatique        chef_info         chef123')
        self.stdout.write('  Télécommunications  chef_telecom      chef123')
        self.stdout.write('  Poste               chef_poste        chef123')
        self.stdout.write(self.style.WARNING('\n  JURYS'))
        self.stdout.write('  Département         Identifiant       Mot de passe')
        self.stdout.write('  ─────────────────────────────────────────────────')
        self.stdout.write('  INFO (président)    jury_ali          jury123')
        self.stdout.write('  INFO                jury_sani         jury123')
        self.stdout.write('  INFO                jury_zara         jury123')
        self.stdout.write('  TELECOM (président) jury_issa         jury123')
        self.stdout.write('  TELECOM             jury_halima       jury123')
        self.stdout.write('  POSTE (président)   jury_boube        jury123')
        self.stdout.write(self.style.WARNING('\n  ÉTUDIANTS  (matricule → à saisir pour lier le compte)'))
        self.stdout.write('  Identifiant              Matricule         Spécialité')
        self.stdout.write('  ─────────────────────────────────────────────────────')
        self.stdout.write('  saidou.mahamadou         2021INFO001       L3-GL')
        self.stdout.write('  hadiza.abdoulaye         2021INFO002       L3-GL')
        self.stdout.write('  moussa.sountalma         2021INFO003       L3-GL')
        self.stdout.write('  aissatou.oumarou         2022INFO010       M2-GL')
        self.stdout.write('  alhassane.garba          2022INFO011       M2-GL')
        self.stdout.write('  rachidatou.hamidou       2021TELECOM001    L3-RDS')
        self.stdout.write('  illiassou.moutari        2021TELECOM002    L3-RDS')
        self.stdout.write('  nafissa.salifou          2022TELECOM010    M2-RDS')
        self.stdout.write('  balkissa.issaka          2021POSTE001      L3-SP')
        self.stdout.write('  adamou.chaibou           2021POSTE002      L3-SP')
        self.stdout.write(self.style.WARNING('\n  Mot de passe de tous les étudiants : etud123'))
        self.stdout.write('='*55 + '\n')

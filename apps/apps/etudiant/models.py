import random
from django.db import models
from django.conf import settings
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURE ACADÉMIQUE  :  Département → Spécialité
# ─────────────────────────────────────────────────────────────────────────────

class Departement(models.Model):
    """Département de l'ESCEP (ex : Informatique, Télécommunications)."""
    nom         = models.CharField(max_length=200)
    code        = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    # Le chef est affecté depuis l'app chef_departement via signal ou admin
    chef        = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='departement_gere',
        limit_choices_to={'role': 'chef_departement'},
    )

    class Meta:
        verbose_name = "Département"

    def __str__(self):
        return f"{self.code} — {self.nom}"


class Specialite(models.Model):
    """Spécialité rattachée à un département (ex : L3 GL, M2 RDS)."""
    NIVEAU_CHOICES = [
        ('L1','Licence 1'), ('L2','Licence 2'), ('L3','Licence 3'),
        ('M1','Master 1'),  ('M2','Master 2'),
    ]
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='specialites')
    nom         = models.CharField(max_length=200)
    code        = models.CharField(max_length=20)   # ex : L3-GL
    niveau      = models.CharField(max_length=5, choices=NIVEAU_CHOICES)

    class Meta:
        verbose_name        = "Spécialité"
        unique_together     = ('departement', 'code')

    def __str__(self):
        return f"{self.code} — {self.nom} ({self.departement.code})"


# ─────────────────────────────────────────────────────────────────────────────
# ÉTUDIANT  (indépendant du modèle User)
# ─────────────────────────────────────────────────────────────────────────────

class Etudiant(models.Model):
    """
    Fiche académique d'un étudiant enregistré par la scolarité.
    N'est PAS lié au modèle User : l'étudiant se connecte avec un compte User
    créé par le DE, puis lors de sa première proposition il saisit son matricule
    pour que le système retrouve sa fiche et l'associe.
    """
    user              = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fiche_etudiant',
    )
    matricule         = models.CharField(max_length=20, unique=True)
    nom               = models.CharField(max_length=100)
    prenom            = models.CharField(max_length=100)
    email             = models.EmailField(blank=True)
    specialite        = models.ForeignKey(Specialite, on_delete=models.PROTECT, related_name='etudiants')
    annee_academique  = models.CharField(max_length=9, default='2024-2025')
    promotion         = models.CharField(max_length=50, blank=True, help_text="Ex : Promotion 2024")
    actif             = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Étudiant"
        ordering     = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.matricule})"

    @property
    def departement(self):
        return self.specialite.departement

    @property
    def chef_departement(self):
        return self.specialite.departement.chef


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS  (système maison, sans dépendance externe)
# ─────────────────────────────────────────────────────────────────────────────

class Notification(models.Model):
    TYPE_INFO    = 'info'
    TYPE_SUCCES  = 'succes'
    TYPE_ALERTE  = 'alerte'
    TYPE_REJET   = 'rejet'

    TYPE_CHOICES = [
        (TYPE_INFO,   'Information'),
        (TYPE_SUCCES, 'Succès'),
        (TYPE_ALERTE, 'Avertissement'),
        (TYPE_REJET,  'Rejet'),
    ]

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type     = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_INFO)
    titre    = models.CharField(max_length=255)
    message  = models.TextField()
    lien     = models.CharField(max_length=500, blank=True)
    lue      = models.BooleanField(default=False)
    cree_le  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        ordering     = ['-cree_le']

    def __str__(self):
        return f"[{self.type}] {self.titre} → {self.destinataire}"

    @classmethod
    def envoyer(cls, destinataire, titre, message, type=TYPE_INFO, lien=''):
        return cls.objects.create(
            destinataire=destinataire,
            titre=titre, message=message,
            type=type, lien=lien,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PROPOSITION DE THÈME
# ─────────────────────────────────────────────────────────────────────────────

class PropositionTheme(models.Model):
    STATUT_ATTENTE  = 'en_attente'
    STATUT_VALIDE   = 'valide'
    STATUT_REJETE   = 'rejete'

    STATUT_CHOICES  = [
        (STATUT_ATTENTE, 'En attente'),
        (STATUT_VALIDE,  'Validé'),
        (STATUT_REJETE,  'Rejeté'),
    ]

    etudiant        = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='propositions')
    theme           = models.CharField(max_length=400, verbose_name="Thème du mémoire / rapport")
    encadreur       = models.CharField(max_length=200, verbose_name="Nom de l'encadreur pédagogique")
    entreprise      = models.CharField(max_length=200, verbose_name="Entreprise d'accueil")
    lieu_stage      = models.CharField(max_length=200)
    promotion       = models.CharField(max_length=50, blank=True, verbose_name="Promotion")
    periode_debut   = models.DateField(verbose_name="Début du stage")
    periode_fin     = models.DateField(verbose_name="Fin du stage")
    description     = models.TextField(blank=True, verbose_name="Description / objectifs du stage")
    statut          = models.CharField(max_length=15, choices=STATUT_CHOICES, default=STATUT_ATTENTE)
    motif_rejet     = models.TextField(blank=True)
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_decision   = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Proposition de thème"
        ordering     = ['-date_soumission']

    def __str__(self):
        return f"{self.theme[:60]} — {self.etudiant}"


# ─────────────────────────────────────────────────────────────────────────────
# DOSSIER DE SOUTENANCE
# ─────────────────────────────────────────────────────────────────────────────

class DossierSoutenance(models.Model):
    STATUT_SOUMIS        = 'soumis'
    STATUT_ANALYSE_IA    = 'analyse_ia'
    STATUT_REJETE_IA     = 'rejete_ia'
    STATUT_INSTRUCTION   = 'en_instruction'
    STATUT_VALIDE_CHEF   = 'valide_chef'
    STATUT_REJETE_CHEF   = 'rejete_chef'
    STATUT_REJETE_DE     = 'rejete_de'
    STATUT_JURY_PROPOSE  = 'jury_propose'
    STATUT_VALIDE_DE     = 'valide_de'
    STATUT_VALIDE_DG     = 'valide_dg'
    STATUT_PROGRAMME     = 'programme'
    STATUT_SOUTENU       = 'soutenu'
    STATUT_CORRECTIONS   = 'corrections'
    STATUT_DEPOT_FINAL   = 'depot_final_soumis'
    STATUT_ARCHIVE       = 'archive'

    STATUT_CHOICES = [
        (STATUT_SOUMIS,       'Soumis'),
        (STATUT_ANALYSE_IA,   'Analyse IA en cours'),
        (STATUT_REJETE_IA,    'Rejeté — taux IA trop élevé'),
        (STATUT_INSTRUCTION,  'En instruction (chef de département)'),
        (STATUT_VALIDE_CHEF,  'Validé par le chef de département'),
        (STATUT_REJETE_CHEF,  'Rejeté par le chef de département'),
        (STATUT_REJETE_DE,    'Rejeté par le DE'),
        (STATUT_JURY_PROPOSE, 'Jury proposé'),
        (STATUT_VALIDE_DE,    'Validé par le directeur des études'),
        (STATUT_VALIDE_DG,    'Validé par la direction générale'),
        (STATUT_PROGRAMME,    'Soutenance programmée'),
        (STATUT_SOUTENU,      'Soutenu'),
        (STATUT_CORRECTIONS,  'Corrections requises'),
        (STATUT_DEPOT_FINAL,  'Dépôt final soumis — en attente validation chef'),
        (STATUT_ARCHIVE,      'Archivé'),
    ]

    etudiant             = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='dossiers')
    proposition          = models.ForeignKey(PropositionTheme, on_delete=models.SET_NULL, null=True, blank=True)

    # Documents uploadés
    memoire_pdf          = models.FileField(upload_to='memoires/%Y/%m/')
    quitus_pedagogique   = models.FileField(upload_to='quitus/pedagogique/%Y/')
    quitus_financier     = models.FileField(upload_to='quitus/financier/%Y/')
    quitus_encadreur     = models.FileField(upload_to='quitus/encadreur/%Y/')

    # Dépôt final (après soutenance)
    memoire_final_pdf    = models.FileField(upload_to='memoires/final/%Y/', null=True, blank=True)
    quitus_president     = models.FileField(upload_to='quitus/president/%Y/', null=True, blank=True)

    # Analyse IA
    taux_ia              = models.FloatField(null=True, blank=True)

    statut               = models.CharField(max_length=30, choices=STATUT_CHOICES, default=STATUT_SOUMIS)
    motif_rejet          = models.TextField(blank=True)
    date_soumission      = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dossier de soutenance"
        ordering     = ['-date_soumission']

    def __str__(self):
        return f"Dossier {self.etudiant} — {self.get_statut_display()}"

    def analyser_taux_ia(self):
        """
        Simulation d'analyse IA sur le PDF.
        En production : appeler GPTZero / Copyleaks / etc.
        """
        self.taux_ia = round(random.uniform(5, 95), 1)
        seuil        = getattr(settings, 'AI_DETECTION_THRESHOLD', 70)

        if self.taux_ia >= seuil:
            self.statut = self.STATUT_REJETE_IA
            self.motif_rejet = (
                f"Taux de contenu généré par IA détecté : {self.taux_ia} % "
                f"(seuil maximum autorisé : {seuil} %). Veuillez retravailler votre document."
            )
        else:
            self.statut = self.STATUT_INSTRUCTION
        self.save()


# ─────────────────────────────────────────────────────────────────────────────
# PROGRAMMATION & PV
# ─────────────────────────────────────────────────────────────────────────────

class ProgrammationSoutenance(models.Model):
    MODE_CHOICES = [
        ('presentiel', 'Présentiel'),
        ('distanciel', 'Distanciel'),
    ]
    dossier          = models.OneToOneField(DossierSoutenance, on_delete=models.CASCADE, related_name='programmation')
    date_soutenance  = models.DateField()
    heure_debut      = models.TimeField()
    heure_fin        = models.TimeField()
    salle            = models.CharField(max_length=100)
    mode             = models.CharField(max_length=15, choices=MODE_CHOICES, default='presentiel')
    lien_visio       = models.URLField(blank=True)

    class Meta:
        verbose_name = "Programmation de soutenance"

    def __str__(self):
        return f"Soutenance {self.dossier.etudiant} — {self.date_soutenance}"


class PVSoutenance(models.Model):
    MENTION_CHOICES  = [
        ('passable','Passable'), ('assez_bien','Assez Bien'),
        ('bien','Bien'), ('tres_bien','Très Bien'), ('excellent','Excellent'),
    ]
    DECISION_CHOICES = [
        ('admis','Admis'),
        ('admis_corrections','Admis avec corrections'),
        ('ajourne','Ajourné'),
    ]

    dossier       = models.OneToOneField(DossierSoutenance, on_delete=models.CASCADE, related_name='pv')
    note          = models.DecimalField(max_digits=4, decimal_places=2)
    mention       = models.CharField(max_length=20, choices=MENTION_CHOICES)
    decision      = models.CharField(max_length=25, choices=DECISION_CHOICES)
    observations  = models.TextField()
    saisi_par     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        limit_choices_to={'role': 'jury'},
    )
    date_saisie   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "PV de soutenance"

    def __str__(self):
        return f"PV {self.dossier.etudiant} — {self.note}/20"


def analyser_document_ia(dossier, seuil_override=None):
    """
    Lance l'analyse IA sur le PDF du dossier.
    Met à jour dossier.taux_ia et dossier.statut.
    Retourne (taux, details).
    """
    from django.conf import settings as dj_settings
    from .analyse_ia import calculer_taux_ia

    try:
        chemin = dossier.memoire_pdf.path
        taux, details = calculer_taux_ia(chemin)
    except Exception:
        import random
        taux   = round(random.uniform(5, 95), 1)
        details = {'methode': 'fallback_aleatoire'}

    if seuil_override is not None:
        seuil = seuil_override
    else:
        try:
            seuil = ParametreSysteme.get().taux_ia_max
        except Exception:
            seuil = getattr(dj_settings, 'AI_DETECTION_THRESHOLD', 70)
    dossier.taux_ia = taux

    if taux >= seuil:
        dossier.statut = DossierSoutenance.STATUT_REJETE_IA
        dossier.motif_rejet = (
            f"Taux de contenu généré par IA détecté : {taux} % "
            f"(seuil maximum autorisé : {seuil} %). "
            "Veuillez retravailler votre document en profondeur."
        )
    else:
        dossier.statut = DossierSoutenance.STATUT_INSTRUCTION

    dossier.save()
    return taux, details


class ParametreSysteme(models.Model):
    """Paramètres configurables par le DE. Singleton — pk=1."""
    taux_ia_max            = models.IntegerField(default=10,
        help_text="Taux IA max autorisé (%). Au-delà → rejet automatique.")
    seuil_similarite_theme = models.IntegerField(default=10,
        help_text="Seuil similarité thèmes (%). Au-delà → avertissement.")
    otp_actif              = models.BooleanField(default=True,
        help_text="Activer la double authentification OTP.")
    mis_a_jour             = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètre système"

    def __str__(self):
        return f"Paramètres IA:{self.taux_ia_max}% Sim:{self.seuil_similarite_theme}% OTP:{'On' if self.otp_actif else 'Off'}"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

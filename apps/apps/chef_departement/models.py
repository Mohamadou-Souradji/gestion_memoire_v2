from django.db import models
from django.conf import settings


class MembreJury(models.Model):
    """Jury géré par un chef de département."""
    STATUT_CHOICES = [
        ('permanent',  'Permanent'),
        ('vacataire',  'Vacataire'),
    ]
    chef       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jurys_geres',
        limit_choices_to={'role': 'chef_departement'},
    )
    # Compte User associé (optionnel — créé lors de la création du jury)
    user       = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='profil_jury',
    )
    nom        = models.CharField(max_length=100)
    prenom     = models.CharField(max_length=100)
    telephone  = models.CharField(max_length=20)
    email      = models.EmailField()
    specialite = models.CharField(max_length=200)
    statut     = models.CharField(max_length=15, choices=STATUT_CHOICES)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Membre du jury"
        verbose_name_plural = "Membres du jury"

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_statut_display()})"


class PropositionJury(models.Model):
    """Proposition de jury + calendrier soumise par le chef de département."""
    STATUT_CHOICES = [
        ('soumise',     'Soumise au directeur des études'),
        ('validee_de',  'Validée par le DE'),
        ('rejetee_de',  'Rejetée par le DE'),
        ('validee_dg',  'Validée par la DG'),
        ('rejetee_dg',  'Rejetée par la DG'),
    ]
    MODE_CHOICES = [
        ('presentiel', 'Présentiel'),
        ('distanciel', 'Distanciel'),
    ]

    chef              = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='propositions_jury',
        limit_choices_to={'role': 'chef_departement'},
    )
    dossier           = models.OneToOneField(
        'etudiant.DossierSoutenance',
        on_delete=models.CASCADE,
        related_name='proposition_jury',
    )
    membres           = models.ManyToManyField(MembreJury, related_name='propositions')
    president         = models.ForeignKey(
        MembreJury,
        on_delete=models.SET_NULL, null=True,
        related_name='presidences',
    )
    date_proposee     = models.DateField()
    heure_debut       = models.TimeField()
    heure_fin         = models.TimeField()
    salle             = models.CharField(max_length=100)
    mode              = models.CharField(max_length=15, choices=MODE_CHOICES, default='presentiel')
    lien_visio        = models.URLField(blank=True)
    statut            = models.CharField(max_length=15, choices=STATUT_CHOICES, default='soumise')
    motif_rejet       = models.TextField(blank=True)
    date_soumission   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proposition de jury"

    def __str__(self):
        return f"Jury pour {self.dossier.etudiant} — {self.get_statut_display()}"

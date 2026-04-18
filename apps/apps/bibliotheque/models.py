from django.db import models
from apps.etudiant.models import DossierSoutenance


class DocumentBibliotheque(models.Model):
    """Document indexé dans la bibliothèque numérique ESCEP."""
    dossier          = models.OneToOneField(
        DossierSoutenance,
        on_delete=models.CASCADE,
        related_name='document_bibliotheque',
    )
    # Métadonnées pré-remplies depuis le dossier — modifiables par la bibliothécaire
    titre            = models.CharField(max_length=400)
    auteur           = models.CharField(max_length=200)
    encadreur        = models.CharField(max_length=200)
    departement      = models.CharField(max_length=200)
    specialite       = models.CharField(max_length=200)
    niveau           = models.CharField(max_length=20)
    promotion        = models.CharField(max_length=50, blank=True)
    annee_academique = models.CharField(max_length=9)
    entreprise_stage = models.CharField(max_length=200, blank=True)
    note             = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    mention          = models.CharField(max_length=20, blank=True)
    mots_cles        = models.TextField(blank=True, help_text="Mots-clés séparés par des virgules")
    date_publication = models.DateTimeField(auto_now_add=True)
    est_publie       = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Document bibliothèque"
        ordering     = ['-annee_academique', 'auteur']

    def __str__(self):
        return f"{self.titre} — {self.auteur} ({self.annee_academique})"

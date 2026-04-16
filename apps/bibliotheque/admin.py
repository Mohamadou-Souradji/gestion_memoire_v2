from django.contrib import admin
from .models import DocumentBibliotheque

@admin.register(DocumentBibliotheque)
class DocumentBibliothequeAdmin(admin.ModelAdmin):
    list_display  = ('titre', 'auteur', 'specialite', 'annee_academique', 'est_publie')
    list_filter   = ('est_publie', 'annee_academique', 'departement')
    search_fields = ('titre', 'auteur', 'mots_cles')

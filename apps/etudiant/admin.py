from django.contrib import admin
from .models import Departement, Specialite, Etudiant, PropositionTheme, DossierSoutenance, Notification

@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display  = ('code', 'nom', 'chef')
    search_fields = ('nom', 'code')

@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display  = ('code', 'nom', 'niveau', 'departement')
    list_filter   = ('departement', 'niveau')

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display  = ('matricule', 'nom', 'prenom', 'specialite', 'annee_academique', 'user')
    list_filter   = ('specialite__departement', 'annee_academique')
    search_fields = ('matricule', 'nom', 'prenom')

@admin.register(PropositionTheme)
class PropositionThemeAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'theme', 'statut', 'date_soumission')
    list_filter  = ('statut',)

@admin.register(DossierSoutenance)
class DossierSoutenanceAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'statut', 'taux_ia', 'date_soumission')
    list_filter  = ('statut',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'titre', 'type', 'lue', 'cree_le')
    list_filter  = ('type', 'lue')

from .models import ParametreSysteme
admin.site.register(ParametreSysteme)

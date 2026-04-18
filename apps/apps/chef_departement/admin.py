from django.contrib import admin
from .models import MembreJury, PropositionJury

@admin.register(MembreJury)
class MembreJuryAdmin(admin.ModelAdmin):
    list_display  = ('prenom', 'nom', 'statut', 'specialite', 'chef')
    list_filter   = ('statut',)
    search_fields = ('nom', 'prenom', 'email')

@admin.register(PropositionJury)
class PropositionJuryAdmin(admin.ModelAdmin):
    list_display  = ('dossier', 'chef', 'statut', 'date_proposee')
    list_filter   = ('statut',)

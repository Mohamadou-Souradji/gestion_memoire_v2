from django import forms
from .models import DocumentBibliotheque


class FormulaireIndexation(forms.ModelForm):
    class Meta:
        model  = DocumentBibliotheque
        fields = ['titre','auteur','encadreur','departement','specialite','niveau',
                  'promotion','annee_academique','entreprise_stage','note','mention','mots_cles']
        widgets = {
            'titre':     forms.TextInput(attrs={'placeholder': 'Titre complet du mémoire'}),
            'mots_cles': forms.TextInput(attrs={'placeholder': 'réseau, sécurité, cloud, ...'}),
        }


class FormulaireRecherche(forms.Form):
    q           = forms.CharField(label='Recherche', required=False,
                    widget=forms.TextInput(attrs={'placeholder': 'Titre, auteur, mots-clés...'}))
    departement = forms.CharField(label='Département', required=False)
    specialite  = forms.CharField(label='Spécialité',  required=False)
    annee       = forms.CharField(label='Année académique', required=False,
                    widget=forms.TextInput(attrs={'placeholder': '2024-2025'}))

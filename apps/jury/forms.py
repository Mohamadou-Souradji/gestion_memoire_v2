from django import forms
from apps.etudiant.models import PVSoutenance


class FormulairePVSoutenance(forms.ModelForm):
    class Meta:
        model  = PVSoutenance
        fields = ['note', 'mention', 'decision', 'observations']
        widgets = {
            'note':         forms.NumberInput(attrs={'min': 0, 'max': 20, 'step': 0.25}),
            'observations': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Observations et recommandations du jury...'}),
        }

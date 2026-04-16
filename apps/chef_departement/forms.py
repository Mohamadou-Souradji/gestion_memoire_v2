from django import forms
from .models import MembreJury, PropositionJury


class FormulaireMembreJury(forms.ModelForm):
    username_jury = forms.CharField(label='Identifiant de connexion',
        widget=forms.TextInput(attrs={'placeholder': 'Ex : jury_ali'}))
    password_jury = forms.CharField(label='Mot de passe',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}))

    class Meta:
        model  = MembreJury
        fields = ['nom','prenom','email','telephone','specialite','statut']
        widgets = {
            'nom':        forms.TextInput(attrs={'placeholder': 'Nom'}),
            'prenom':     forms.TextInput(attrs={'placeholder': 'Prénom'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'email@exemple.com'}),
            'telephone':  forms.TextInput(attrs={'placeholder': '+227 XX XX XX XX'}),
            'specialite': forms.TextInput(attrs={'placeholder': 'Ex : Réseaux, Génie Logiciel...'}),
        }


class FormulairePropositionJury(forms.ModelForm):
    class Meta:
        model  = PropositionJury
        fields = ['membres','president','date_proposee','heure_debut','heure_fin','salle','mode','lien_visio']
        widgets = {
            'membres':       forms.CheckboxSelectMultiple(),
            'date_proposee': forms.DateInput(attrs={'type':'date'}),
            'heure_debut':   forms.TimeInput(attrs={'type':'time'}),
            'heure_fin':     forms.TimeInput(attrs={'type':'time'}),
            'salle':         forms.TextInput(attrs={'placeholder':'Ex : Salle A101'}),
            'lien_visio':    forms.URLInput(attrs={'placeholder':'https://meet.google.com/...'}),
        }

    def __init__(self, *args, chef=None, **kwargs):
        super().__init__(*args, **kwargs)
        if chef:
            jurys = MembreJury.objects.filter(chef=chef)
            self.fields['membres'].queryset   = jurys
            self.fields['president'].queryset = jurys


class FormulaireValidationDossier(forms.Form):
    action = forms.ChoiceField(choices=[('valider','Valider'),('rejeter','Rejeter')],
                               widget=forms.HiddenInput())
    motif  = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows':3,'placeholder':'Motif de rejet obligatoire...'}))

    def clean(self):
        d = super().clean()
        if d.get('action') == 'rejeter' and not d.get('motif','').strip():
            raise forms.ValidationError("Un motif est obligatoire en cas de rejet.")
        return d

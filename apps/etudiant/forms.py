from django import forms
from .models import PropositionTheme, DossierSoutenance, Etudiant


class FormulaireVerificationMatricule(forms.Form):
    matricule        = forms.CharField(
        label='Numéro de matricule',
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Ex : 2021INFO001'})
    )
    annee_academique = forms.CharField(
        label='Année académique',
        max_length=9,
        widget=forms.TextInput(attrs={'placeholder': 'Ex : 2024-2025'})
    )


class FormulairePropositionTheme(forms.ModelForm):
    class Meta:
        model  = PropositionTheme
        fields = ['theme','promotion','encadreur','entreprise','lieu_stage','periode_debut','periode_fin','description']
        widgets = {
            'theme':         forms.Textarea(attrs={'rows':3,'placeholder':'Intitulé complet et précis du thème'}),
            'promotion':     forms.TextInput(attrs={'placeholder':'Ex : Promotion 2025'}),
            'encadreur':     forms.TextInput(attrs={'placeholder':'Nom et prénom de l\'encadreur'}),
            'entreprise':    forms.TextInput(attrs={'placeholder':'Nom de l\'entreprise d\'accueil'}),
            'lieu_stage':    forms.TextInput(attrs={'placeholder':'Ville, quartier'}),
            'periode_debut': forms.DateInput(attrs={'type':'date'}),
            'periode_fin':   forms.DateInput(attrs={'type':'date'}),
            'description':   forms.Textarea(attrs={'rows':4,'placeholder':'Objectifs, problématique, démarche...'}),
        }


class FormulaireDossierSoutenance(forms.ModelForm):
    class Meta:
        model  = DossierSoutenance
        fields = ['memoire_pdf', 'quitus_pedagogique', 'quitus_financier', 'quitus_encadreur']
        labels = {
            'memoire_pdf':         'Mémoire / rapport (PDF)',
            'quitus_pedagogique':  'Quitus pédagogique (signé par la scolarité)',
            'quitus_financier':    'Quitus financier (signé par la direction financière)',
            'quitus_encadreur':    'Quitus de l\'encadreur (signé)',
        }

    def clean(self):
        donnees = super().clean()
        PDF_CHAMPS = ['memoire_pdf']
        TOUS_CHAMPS = ['memoire_pdf','quitus_pedagogique','quitus_financier','quitus_encadreur']
        EXT_PDF = ('.pdf',)
        EXT_OK  = ('.pdf','.jpg','.jpeg','.png')
        for champ in TOUS_CHAMPS:
            fichier = donnees.get(champ)
            if fichier:
                ext = fichier.name.lower()
                if champ in PDF_CHAMPS and not ext.endswith(EXT_PDF):
                    self.add_error(champ, "Le mémoire doit être un fichier PDF.")
                elif champ not in PDF_CHAMPS and not any(ext.endswith(e) for e in EXT_OK):
                    self.add_error(champ, "Formats acceptés : PDF, JPG, PNG.")
                if fichier.size > 20 * 1024 * 1024:
                    self.add_error(champ, "Le fichier ne doit pas dépasser 20 Mo.")
        return donnees


class FormulaireDepotFinal(forms.ModelForm):
    class Meta:
        model  = DossierSoutenance
        fields = ['memoire_final_pdf', 'quitus_president']
        labels = {
            'memoire_final_pdf': 'Mémoire final corrigé (PDF)',
            'quitus_president':  'Quitus du président du jury',
        }


class FormulaireEtudiantDE(forms.ModelForm):
    class Meta:
        model  = Etudiant
        fields = ['matricule','nom','prenom','email','specialite','annee_academique','promotion']
        widgets = {
            'matricule':        forms.TextInput(attrs={'placeholder':'Ex : 2024INFO001'}),
            'nom':              forms.TextInput(attrs={'placeholder':'Nom'}),
            'prenom':           forms.TextInput(attrs={'placeholder':'Prénom'}),
            'email':            forms.EmailInput(attrs={'placeholder':'email@etudiant.escep.ne'}),
            'annee_academique': forms.TextInput(attrs={'placeholder':'2024-2025'}),
            'promotion':        forms.TextInput(attrs={'placeholder':'Promotion 2025'}),
        }

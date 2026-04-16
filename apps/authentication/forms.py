from django import forms
from .models import User


class FormulaireConnexion(forms.Form):
    identifiant = forms.CharField(
        label='Identifiant',
        widget=forms.TextInput(attrs={'placeholder': 'Votre identifiant', 'autocomplete': 'username'})
    )
    mot_de_passe = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )
    def clean_identifiant(self):
        return self.cleaned_data['identifiant'].strip()


class FormulaireOTP(forms.Form):
    code = forms.CharField(
        label='Code de vérification',
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '000000',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'autocomplete': 'one-time-code',
            'autofocus': True,
        })
    )
    def clean_code(self):
        c = self.cleaned_data['code'].strip()
        if not c.isdigit():
            raise forms.ValidationError("Le code doit contenir uniquement des chiffres.")
        return c


class FormulaireCreationCompte(forms.ModelForm):
    mot_de_passe  = forms.CharField(label='Mot de passe',   widget=forms.PasswordInput())
    confirmation  = forms.CharField(label='Confirmation',   widget=forms.PasswordInput())

    class Meta:
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'telephone', 'role')

    def clean(self):
        donnees = super().clean()
        if donnees.get('mot_de_passe') != donnees.get('confirmation'):
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return donnees

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.set_password(self.cleaned_data['mot_de_passe'])
        if commit:
            utilisateur.save()
        return utilisateur

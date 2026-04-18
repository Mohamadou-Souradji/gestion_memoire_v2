from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, CodeOTP
from .forms import FormulaireConnexion, FormulaireOTP
from .utils import envoyer_otp_par_email, masquer_email


def _otp_actif():
    """Lit le paramètre OTP depuis la BDD (ParametreSysteme)."""
    try:
        from apps.etudiant.models import ParametreSysteme
        return ParametreSysteme.get().otp_actif
    except Exception:
        return True  # Actif par défaut si BDD pas encore migrée


def connexion(request):
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())

    formulaire = FormulaireConnexion(request.POST or None)

    if request.method == 'POST' and formulaire.is_valid():
        utilisateur = authenticate(
            request,
            username=formulaire.cleaned_data['identifiant'],
            password=formulaire.cleaned_data['mot_de_passe'],
        )
        if utilisateur:
            if not utilisateur.is_active:
                messages.error(request, "Ce compte est bloqué. Contactez l'administration.")
                return render(request, 'authentication/connexion.html', {'formulaire': formulaire})

            # OTP conditionnel
            if _otp_actif() and utilisateur.email:
                otp = CodeOTP.generer_pour(utilisateur)
                try:
                    envoyer_otp_par_email(utilisateur, otp.code)
                    request.session['otp_user_id'] = utilisateur.pk
                    return redirect('auth:verification_otp')
                except Exception:
                    # Email non configuré → connexion directe
                    pass

            # Connexion directe (OTP désactivé ou email absent)
            login(request, utilisateur)
            messages.success(request, f"Bienvenue, {utilisateur.get_full_name() or utilisateur.username} !")
            return redirect(utilisateur.get_dashboard_url())
        else:
            messages.error(request, "Identifiant ou mot de passe incorrect.")

    return render(request, 'authentication/connexion.html', {'formulaire': formulaire})


def verification_otp(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('auth:connexion')

    try:
        utilisateur = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('auth:connexion')

    formulaire = FormulaireOTP(request.POST or None)

    if request.method == 'POST':
        if request.POST.get('renvoyer'):
            otp = CodeOTP.generer_pour(utilisateur)
            try:
                envoyer_otp_par_email(utilisateur, otp.code)
                messages.success(request, "Nouveau code envoyé.")
            except Exception:
                messages.error(request, "Erreur lors de l'envoi.")
            return redirect('auth:verification_otp')

        if formulaire.is_valid():
            code_saisi = formulaire.cleaned_data['code']
            otp_valide = utilisateur.codes_otp.filter(utilise=False).order_by('-cree_le').first()
            if otp_valide and otp_valide.verifier(code_saisi):
                otp_valide.utilise = True
                otp_valide.save()
                utilisateur.codes_otp.filter(utilise=False).update(utilise=True)
                login(request, utilisateur)
                request.session.pop('otp_user_id', None)
                messages.success(request, f"Bienvenue, {utilisateur.get_full_name() or utilisateur.username} !")
                return redirect(utilisateur.get_dashboard_url())
            else:
                messages.error(request, "Code incorrect ou expiré.")

    from django.conf import settings as dj_settings
    return render(request, 'authentication/verification_otp.html', {
        'formulaire':   formulaire,
        'email_masque': masquer_email(utilisateur.email),
        'nom_affiche':  utilisateur.get_full_name() or utilisateur.username,
        'duree':        getattr(dj_settings, 'OTP_VALIDITY_MINUTES', 10),
    })


@login_required
def deconnexion(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('auth:connexion')

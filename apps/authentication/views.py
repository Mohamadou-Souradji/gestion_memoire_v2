from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User, CodeOTP
from .forms import FormulaireConnexion, FormulaireOTP
from .utils import envoyer_otp_par_email, masquer_email


def connexion(request):
    """Étape 1 : identifiant + mot de passe → envoie le code OTP par e-mail."""
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

            # Générer et envoyer OTP
            otp = CodeOTP.generer_pour(utilisateur)
            try:
                envoyer_otp_par_email(utilisateur, otp.code)
                # Stocker l'ID en session pour l'étape 2
                request.session['otp_user_id'] = utilisateur.pk
                request.session['otp_user_nom'] = utilisateur.get_full_name() or utilisateur.username
                return redirect('auth:verification_otp')
            except Exception:
                # Si l'e-mail échoue (ex: pas configuré), connexion directe en développement
                if utilisateur.email:
                    messages.error(request,
                        "Impossible d'envoyer le code OTP. Vérifiez la configuration e-mail.")
                    return render(request, 'authentication/connexion.html', {'formulaire': formulaire})
                else:
                    # Pas d'e-mail configuré → connexion directe (fallback dev)
                    login(request, utilisateur)
                    messages.warning(request, f"OTP non envoyé (pas d'e-mail). Connexion directe.")
                    return redirect(utilisateur.get_dashboard_url())
        else:
            messages.error(request, "Identifiant ou mot de passe incorrect.")

    return render(request, 'authentication/connexion.html', {'formulaire': formulaire})


def verification_otp(request):
    """Étape 2 : saisie du code OTP à 6 chiffres."""
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('auth:connexion')

    try:
        utilisateur = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        del request.session['otp_user_id']
        return redirect('auth:connexion')

    formulaire = FormulaireOTP(request.POST or None)

    if request.method == 'POST':
        # Renvoi du code
        if request.POST.get('renvoyer'):
            otp = CodeOTP.generer_pour(utilisateur)
            try:
                envoyer_otp_par_email(utilisateur, otp.code)
                messages.success(request, "Nouveau code envoyé.")
            except Exception:
                messages.error(request, "Erreur lors de l'envoi. Réessayez.")
            return redirect('auth:verification_otp')

        # Validation du code
        if formulaire.is_valid():
            code_saisi = formulaire.cleaned_data['code']
            otp_valide = (
                utilisateur.codes_otp
                .filter(utilise=False)
                .order_by('-cree_le')
                .first()
            )
            if otp_valide and otp_valide.verifier(code_saisi):
                otp_valide.utilise = True
                otp_valide.save()
                # Invalider les anciens codes
                utilisateur.codes_otp.filter(utilise=False).update(utilise=True)
                # Connecter
                login(request, utilisateur)
                del request.session['otp_user_id']
                if 'otp_user_nom' in request.session:
                    del request.session['otp_user_nom']
                messages.success(request, f"Bienvenue, {utilisateur.get_full_name() or utilisateur.username} !")
                return redirect(utilisateur.get_dashboard_url())
            else:
                messages.error(request, "Code incorrect ou expiré. Vérifiez votre e-mail.")

    from django.conf import settings as dj_settings
    return render(request, 'authentication/verification_otp.html', {
        'formulaire':   formulaire,
        'email_masque': masquer_email(utilisateur.email),
        'nom_affiche':  utilisateur.get_full_name() or utilisateur.username,
        'duree':        dj_settings.OTP_VALIDITY_MINUTES,
    })


@login_required
def deconnexion(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('auth:connexion')

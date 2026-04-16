from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_requis(*roles):
    """Décorateur qui restreint l'accès à un ou plusieurs rôles."""
    def decorateur(vue):
        @wraps(vue)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('auth:connexion')
            if request.user.role not in roles:
                messages.error(request, "Accès non autorisé pour votre rôle.")
                return redirect(request.user.get_dashboard_url())
            return vue(request, *args, **kwargs)
        return wrapper
    return decorateur


# Raccourcis pratiques
etudiant_requis         = role_requis('etudiant')
chef_requis             = role_requis('chef_departement')
directeur_requis        = role_requis('directeur_etudes')
dg_requis               = role_requis('direction_generale')
jury_requis             = role_requis('jury')
bibliothecaire_requis   = role_requis('bibliotheque')

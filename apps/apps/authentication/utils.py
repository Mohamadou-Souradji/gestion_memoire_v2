from django.core.mail import send_mail
from django.conf import settings


def envoyer_otp_par_email(utilisateur, code):
    """Envoie le code OTP à l'adresse e-mail de l'utilisateur."""
    sujet = f"[ESCEP Niger] Votre code de vérification : {code}"
    corps = (
        f"Bonjour {utilisateur.get_full_name() or utilisateur.username},\n\n"
        f"Votre code de vérification pour accéder à la plateforme ESCEP est :\n\n"
        f"        {code}\n\n"
        f"Ce code est valable {settings.OTP_VALIDITY_MINUTES} minutes.\n"
        f"Si vous n'êtes pas à l'origine de cette connexion, ignorez ce message.\n\n"
        f"— L'équipe ESCEP Niger"
    )
    send_mail(
        subject       = sujet,
        message       = corps,
        from_email    = settings.DEFAULT_FROM_EMAIL,
        recipient_list= [utilisateur.email],
        fail_silently = False,
    )


def masquer_email(email):
    """Masque partiellement l'adresse e-mail pour l'affichage. ex: so***@gmail.com"""
    if not email or '@' not in email:
        return '***'
    local, domaine = email.split('@', 1)
    visible = local[:2] if len(local) > 2 else local[0]
    return f"{visible}***@{domaine}"

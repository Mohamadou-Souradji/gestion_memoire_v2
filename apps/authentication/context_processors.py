def user_role_context(request):
    ctx = {'role_utilisateur': None, 'notifications_non_lues': 0, 'nb_notifs': 0}
    if not request.user.is_authenticated:
        return ctx
    ctx['role_utilisateur'] = request.user.role
    try:
        from apps.etudiant.models import Notification
        count = Notification.objects.filter(destinataire=request.user, lue=False).count()
        ctx['notifications_non_lues'] = count
        ctx['nb_notifs'] = count
    except Exception:
        pass
    return ctx

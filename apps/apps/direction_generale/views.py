from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from apps.authentication.decorators import dg_requis
from apps.etudiant.models import DossierSoutenance, ProgrammationSoutenance, Notification, Specialite
from apps.chef_departement.models import PropositionJury

User = get_user_model()


@login_required
@dg_requis
def tableau_de_bord(request):
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)
    return render(request, 'direction_generale/tableau_de_bord.html', {
        'nb_a_valider':  PropositionJury.objects.filter(statut='validee_de').count(),
        'nb_valide_dg':  PropositionJury.objects.filter(statut='validee_dg').count(),
        'nb_rejete_dg':  PropositionJury.objects.filter(statut='rejetee_dg').count(),
        'nb_total_traites': PropositionJury.objects.filter(statut__in=['validee_dg','rejetee_dg']).count(),
        'nb_programme':  DossierSoutenance.objects.filter(statut='programme').count(),
        'nb_soutenus':   DossierSoutenance.objects.filter(statut__in=['soutenu','archive']).count(),
        'notifications': notifs, 'nb_notifs': notifs.count(),
    })


@login_required
@dg_requis
def validation_finale(request):
    qs = PropositionJury.objects.filter(statut='validee_de').select_related(
        'dossier__etudiant__specialite__departement','chef','president')
    q, annee, spe = (request.GET.get(k,'') for k in ['q','annee','specialite'])
    if q: qs = qs.filter(Q(dossier__etudiant__nom__icontains=q)|Q(dossier__etudiant__prenom__icontains=q))
    if annee: qs = qs.filter(dossier__etudiant__annee_academique=annee)
    if spe:   qs = qs.filter(dossier__etudiant__specialite__code=spe)
    return render(request, 'direction_generale/validation_finale.html', {
        'propositions': qs, 'specialites': Specialite.objects.all(),
        'f': {'q':q,'annee':annee,'specialite':spe},
    })


@login_required
@dg_requis
def action_proposition(request, pk):
    prop = get_object_or_404(PropositionJury, pk=pk, statut='validee_de')
    if request.method == 'POST':
        action, motif = request.POST.get('action'), request.POST.get('motif','').strip()
        if action == 'valider':
            prop.statut = 'validee_dg'; prop.save()
            dossier = prop.dossier
            # Créer programmation officielle
            ProgrammationSoutenance.objects.update_or_create(dossier=dossier, defaults={
                'date_soutenance': prop.date_proposee, 'heure_debut': prop.heure_debut,
                'heure_fin': prop.heure_fin, 'salle': prop.salle, 'mode': prop.mode, 'lien_visio': prop.lien_visio or '',
            })
            dossier.statut = DossierSoutenance.STATUT_PROGRAMME; dossier.save()
            # Notifier tous
            notif_msg = (f"Soutenance programmée :\n"
                f"Date : {prop.date_proposee} — {prop.heure_debut}–{prop.heure_fin}\n"
                f"Salle : {prop.salle} ({prop.get_mode_display()})")
            if dossier.etudiant.user:
                Notification.envoyer(dossier.etudiant.user, "Soutenance programmée !", notif_msg, Notification.TYPE_SUCCES, '/etudiant/')
            Notification.envoyer(prop.chef, f"Soutenance validée — {dossier.etudiant}", notif_msg, Notification.TYPE_SUCCES)
            for de in User.objects.filter(role='directeur_etudes'):
                Notification.envoyer(de, f"Soutenance validée DG — {dossier.etudiant}", notif_msg, Notification.TYPE_INFO)
            for m in prop.membres.all():
                if m.user:
                    Notification.envoyer(m.user, f"Vous êtes convoqué — {dossier.etudiant}", notif_msg, Notification.TYPE_INFO, '/jury/')
            messages.success(request, "Validée. Toutes les parties notifiées.")
        elif action == 'rejeter' and motif:
            prop.statut = 'rejetee_dg'; prop.motif_rejet = motif; prop.save()
            prop.dossier.statut = DossierSoutenance.STATUT_REJETE_DE; prop.dossier.save()
            Notification.envoyer(prop.chef, "Proposition rejetée par la DG",
                f"Motif : {motif}. Corrigez et soumettez à nouveau.", Notification.TYPE_REJET, '/chef/instruire/')
            for de in User.objects.filter(role='directeur_etudes'):
                Notification.envoyer(de, "Rejet DG", f"Proposition de {prop.dossier.etudiant} rejetée. Motif : {motif}", Notification.TYPE_ALERTE)
            messages.warning(request, "Rejetée. Chef et DE notifiés.")
    return redirect('dg:validation_finale')


@login_required
@dg_requis
def notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'direction_generale/notifications.html', {'notifications': notifs})


@login_required
@dg_requis
def valider_tout(request):
    """Valide toutes les propositions validées par le DE."""
    if request.method == 'POST':
        props = PropositionJury.objects.filter(statut='validee_de')
        count = props.count()
        from apps.etudiant.models import ProgrammationSoutenance
        for prop in props:
            prop.statut = 'validee_dg'; prop.save()
            dossier = prop.dossier
            ProgrammationSoutenance.objects.update_or_create(dossier=dossier, defaults={
                'date_soutenance': prop.date_proposee, 'heure_debut': prop.heure_debut,
                'heure_fin': prop.heure_fin, 'salle': prop.salle, 'mode': prop.mode,
                'lien_visio': prop.lien_visio or '',
            })
            dossier.statut = DossierSoutenance.STATUT_PROGRAMME; dossier.save()
            notif_msg = (f"Soutenance programmée : {prop.date_proposee} "
                f"{prop.heure_debut}–{prop.heure_fin} — {prop.salle}")
            if dossier.etudiant.user:
                Notification.envoyer(dossier.etudiant.user, "Soutenance programmée !", notif_msg, Notification.TYPE_SUCCES, '/etudiant/')
            Notification.envoyer(prop.chef, f"Soutenance validée — {dossier.etudiant}", notif_msg, Notification.TYPE_SUCCES)
            for m in prop.membres.all():
                if m.user:
                    Notification.envoyer(m.user, f"Convocation soutenance — {dossier.etudiant}", notif_msg, Notification.TYPE_INFO, '/jury/')
        messages.success(request, f"{count} soutenance(s) officiellement programmée(s).")
    return redirect('dg:validation_finale')

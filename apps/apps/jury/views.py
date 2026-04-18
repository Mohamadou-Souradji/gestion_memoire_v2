from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.authentication.decorators import jury_requis
from apps.etudiant.models import DossierSoutenance, PVSoutenance, Notification
from apps.chef_departement.models import PropositionJury, MembreJury
from .forms import FormulairePVSoutenance


def _jury_profil(request):
    try: return request.user.profil_jury
    except: return None


@login_required
@jury_requis
def tableau_de_bord(request):
    profil = _jury_profil(request)
    soutenances = []
    if profil:
        props = PropositionJury.objects.filter(membres=profil, statut='validee_dg'
            ).select_related('dossier__etudiant__specialite','dossier__programmation')
        soutenances = [p.dossier for p in props if not hasattr(p.dossier,'pv')]
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)
    return render(request, 'jury/tableau_de_bord.html', {
        'soutenances': soutenances, 'notifications': notifs, 'nb_notifs': notifs.count(),
    })


@login_required
@jury_requis
def historique(request):
    profil = _jury_profil(request)
    soutenances = []
    if profil:
        props = PropositionJury.objects.filter(membres=profil
            ).select_related('dossier__etudiant__specialite')
        soutenances = [p.dossier for p in props if hasattr(p.dossier,'pv')]
    return render(request, 'jury/historique.html', {'soutenances': soutenances})


@login_required
@jury_requis
def saisir_pv(request, pk):
    profil = _jury_profil(request)
    prop   = get_object_or_404(PropositionJury, dossier__pk=pk, president=profil)
    dossier = prop.dossier
    if hasattr(dossier,'pv'):
        messages.info(request, "PV déjà saisi.")
        return redirect('jury:tableau_de_bord')
    form = FormulairePVSoutenance(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pv = form.save(commit=False); pv.dossier = dossier; pv.saisi_par = request.user; pv.save()
        dossier.statut = DossierSoutenance.STATUT_CORRECTIONS if pv.decision == 'admis_corrections' else DossierSoutenance.STATUT_SOUTENU
        dossier.save()
        notif_msg = f"Décision : {pv.get_decision_display()} | Note : {pv.note}/20 — {pv.get_mention_display()}\n{pv.observations}"
        if dossier.etudiant.user:
            Notification.envoyer(dossier.etudiant.user, "Résultat de votre soutenance",
                notif_msg, Notification.TYPE_SUCCES if pv.decision=='admis' else Notification.TYPE_ALERTE, '/etudiant/')
        Notification.envoyer(prop.chef, f"PV saisi — {dossier.etudiant}", notif_msg, Notification.TYPE_INFO)
        messages.success(request, "PV saisi. Étudiant et chef notifiés.")
        return redirect('jury:tableau_de_bord')
    return render(request, 'jury/saisir_pv.html', {'form': form, 'dossier': dossier, 'prop': prop})


@login_required
@jury_requis
def notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'jury/notifications.html', {'notifications': notifs})

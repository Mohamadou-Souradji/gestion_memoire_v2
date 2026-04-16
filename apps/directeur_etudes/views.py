from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from apps.authentication.decorators import directeur_requis
from apps.authentication.forms import FormulaireCreationCompte
from apps.etudiant.models import Departement, Etudiant, Specialite, DossierSoutenance, Notification
from apps.chef_departement.models import PropositionJury

User = get_user_model()


@login_required
@directeur_requis
def tableau_de_bord(request):
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)
    return render(request, 'directeur_etudes/tableau_de_bord.html', {
        # À traiter
        'props_a_valider':  PropositionJury.objects.filter(statut='soumise').count(),
        # En cours (transmis DG)
        'props_chez_dg':    PropositionJury.objects.filter(statut='validee_de').count(),
        # Traités par le DE (validés ou rejetés)
        'props_traites':    PropositionJury.objects.filter(statut__in=['validee_de','rejetee_de','validee_dg','rejetee_dg','validee_dg']).count(),
        # Rejetés par DE
        'props_rejetes':    PropositionJury.objects.filter(statut='rejetee_de').count(),
        # Soutenances programmées
        'nb_programes':     DossierSoutenance.objects.filter(statut='programme').count(),
        'nb_soutenus':      DossierSoutenance.objects.filter(statut__in=['soutenu','archive']).count(),
        'nb_etudiants':     Etudiant.objects.count(),
        'departements':     Departement.objects.prefetch_related('specialites').all(),
        'notifications':    notifs,
        'nb_notifs':        notifs.count(),
    })


@login_required
@directeur_requis
def propositions(request):
    qs = PropositionJury.objects.select_related(
        'dossier__etudiant__specialite__departement','chef').order_by('-date_soumission')
    q, annee, spe, statut = (request.GET.get(k,'') for k in ['q','annee','specialite','statut'])
    statut = statut or 'soumise'
    if q: qs = qs.filter(Q(dossier__etudiant__nom__icontains=q)|Q(dossier__etudiant__prenom__icontains=q)|Q(dossier__proposition__theme__icontains=q))
    if annee: qs = qs.filter(dossier__etudiant__annee_academique=annee)
    if spe:   qs = qs.filter(dossier__etudiant__specialite__code=spe)
    if statut != 'tous': qs = qs.filter(statut=statut)
    return render(request, 'directeur_etudes/propositions.html', {
        'propositions': qs, 'specialites': Specialite.objects.all(),
        'f': {'q':q,'annee':annee,'specialite':spe,'statut':statut},
    })


@login_required
@directeur_requis
def action_proposition(request, pk):
    prop = get_object_or_404(PropositionJury, pk=pk)
    if request.method == 'POST':
        action, motif = request.POST.get('action'), request.POST.get('motif','').strip()
        if action == 'valider':
            prop.statut = 'validee_de'; prop.save()
            for dg in User.objects.filter(role='direction_generale'):
                Notification.envoyer(dg, "Proposition de jury à valider",
                    f"{prop.dossier.etudiant} — soutenance le {prop.date_proposee}", Notification.TYPE_INFO, '/dg/')
            messages.success(request, "Validée. DG notifiée.")
        elif action == 'rejeter' and motif:
            prop.statut = 'rejetee_de'; prop.motif_rejet = motif; prop.save()
            # Remettre le dossier en statut rejete_de pour que le chef puisse corriger
            prop.dossier.statut = DossierSoutenance.STATUT_REJETE_DE; prop.dossier.save()
            Notification.envoyer(prop.chef, "Proposition rejetée par le DE",
                f"Motif : {motif}. Corrigez et soumettez à nouveau.", Notification.TYPE_REJET, '/chef/instruire/')
            messages.warning(request, "Rejetée. Chef notifié.")
    return redirect('directeur:propositions')


@login_required
@directeur_requis
def etudiants(request):
    qs = Etudiant.objects.select_related('specialite__departement','user').all()
    q, dept, spe, annee = (request.GET.get(k,'') for k in ['q','departement','specialite','annee'])
    if q: qs = qs.filter(Q(nom__icontains=q)|Q(prenom__icontains=q)|Q(matricule__icontains=q))
    if dept: qs = qs.filter(specialite__departement__code=dept)
    if spe:  qs = qs.filter(specialite__code=spe)
    if annee:qs = qs.filter(annee_academique=annee)
    return render(request, 'directeur_etudes/etudiants.html', {
        'etudiants': qs, 'departements': Departement.objects.all(), 'specialites': Specialite.objects.all(),
        'f': {'q':q,'departement':dept,'specialite':spe,'annee':annee},
    })


@login_required
@directeur_requis
def creer_etudiant(request):
    if request.method == 'POST':
        from apps.etudiant.forms import FormulaireEtudiantDE
        form = FormulaireEtudiantDE(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, "Étudiant ajouté.")
        else:
            for e in form.errors.values(): messages.error(request, e.as_text())
    return redirect('directeur:etudiants')


@login_required
@directeur_requis
def modifier_etudiant(request, pk):
    etudiant = get_object_or_404(Etudiant, pk=pk)
    if request.method == 'POST':
        from apps.etudiant.forms import FormulaireEtudiantDE
        form = FormulaireEtudiantDE(request.POST, instance=etudiant)
        if form.is_valid(): form.save(); messages.success(request, "Étudiant mis à jour.")
    return redirect('directeur:etudiants')


@login_required
@directeur_requis
def supprimer_etudiant(request, pk):
    etudiant = get_object_or_404(Etudiant, pk=pk)
    if request.method == 'POST': etudiant.delete(); messages.success(request, "Étudiant supprimé.")
    return redirect('directeur:etudiants')


@login_required
@directeur_requis
def utilisateurs(request):
    qs = User.objects.all().order_by('role','last_name')
    role = request.GET.get('role','')
    if role: qs = qs.filter(role=role)
    return render(request, 'directeur_etudes/utilisateurs.html', {
        'utilisateurs': qs, 'roles': User.ROLE_CHOICES, 'f': {'role':role},
        'departements': Departement.objects.all(),
    })


@login_required
@directeur_requis
def creer_utilisateur(request):
    if request.method == 'POST':
        form = FormulaireCreationCompte(request.POST)
        if form.is_valid():
            user = form.save()
            # Si chef, affecter au département
            if user.role == 'chef_departement':
                dept_id = request.POST.get('departement_id')
                if dept_id:
                    try:
                        dept = Departement.objects.get(pk=dept_id)
                        dept.chef = user; dept.save()
                    except: pass
            messages.success(request, f"Compte créé : {user.get_full_name()}")
        else:
            for e in form.errors.values(): messages.error(request, e.as_text())
    return redirect('directeur:utilisateurs')


@login_required
@directeur_requis
def supprimer_utilisateur(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user.pk != request.user.pk: user.delete(); messages.success(request, "Compte supprimé.")
        else: messages.error(request, "Impossible de supprimer votre propre compte.")
    return redirect('directeur:utilisateurs')


@login_required
@directeur_requis
def toggle_compte(request, pk):
    """Bloquer ou débloquer un compte utilisateur."""
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST' and user.pk != request.user.pk:
        user.is_active = not user.is_active
        user.save()
        etat = "activé" if user.is_active else "bloqué"
        messages.success(request, f"Compte {user.get_full_name()} {etat}.")
    return redirect('directeur:utilisateurs')


@login_required
@directeur_requis
def notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'directeur_etudes/notifications.html', {'notifications': notifs})


@login_required
@directeur_requis
def valider_tout(request):
    """Valide toutes les propositions soumises au DE."""
    if request.method == 'POST':
        props = PropositionJury.objects.filter(statut='soumise')
        count = props.count()
        for prop in props:
            prop.statut = 'validee_de'; prop.save()
            for dg in User.objects.filter(role='direction_generale'):
                Notification.envoyer(dg,
                    "Propositions jury validées en lot",
                    f"Le DE a validé {count} proposition(s) — transmission à la DG.",
                    Notification.TYPE_INFO, '/dg/validation/')
        messages.success(request, f"{count} proposition(s) validées et transmises à la DG.")
    return redirect('directeur:propositions')

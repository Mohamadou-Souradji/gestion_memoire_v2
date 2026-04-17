from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from apps.authentication.decorators import chef_requis
from apps.etudiant.models import (Etudiant, PropositionTheme, DossierSoutenance,
                                   ProgrammationSoutenance, Notification)
from .models import MembreJury, PropositionJury
from .forms import FormulaireMembreJury, FormulairePropositionJury

User = get_user_model()


def _dept(request):
    try: return request.user.departement_gere
    except: return None


@login_required
@chef_requis
def tableau_de_bord(request):
    dept = _dept(request)
    qs_e = Etudiant.objects.filter(specialite__departement=dept) if dept else Etudiant.objects.none()
    qs_p = PropositionTheme.objects.filter(etudiant__specialite__departement=dept, statut='en_attente') if dept else PropositionTheme.objects.none()
    qs_d = DossierSoutenance.objects.filter(
        etudiant__specialite__departement=dept,
        statut__in=['en_instruction', 'depot_final_soumis']
    ) if dept else DossierSoutenance.objects.none()
    qs_j = MembreJury.objects.filter(chef=request.user)
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)
    return render(request, 'chef_departement/tableau_de_bord.html', {
        'dept': dept, 'nb_e': qs_e.count(), 'nb_p': qs_p.count(),
        'nb_d': qs_d.count(), 'nb_j': qs_j.count(),
        'propositions': qs_p[:5], 'dossiers': qs_d[:5],
        'nb_notifs': notifs.count(), 'notifications': notifs,
    })


# ── PROPOSITIONS ──────────────────────────────────────────
@login_required
@chef_requis
def propositions(request):
    dept = _dept(request)
    qs = PropositionTheme.objects.filter(etudiant__specialite__departement=dept
        ).select_related('etudiant__specialite') if dept else PropositionTheme.objects.none()
    q, annee, spe, statut = (request.GET.get(k,'') for k in ['q','annee','specialite','statut'])
    statut = statut or 'en_attente'   # Par défaut : en attente seulement
    if q:     qs = qs.filter(Q(etudiant__nom__icontains=q)|Q(etudiant__prenom__icontains=q)|Q(theme__icontains=q))
    if annee: qs = qs.filter(etudiant__annee_academique=annee)
    if spe:   qs = qs.filter(etudiant__specialite__code=spe)
    if statut != 'tous': qs = qs.filter(statut=statut)   # FILTRE STATUT APPLIQUÉ
    qs = qs.order_by('-date_soumission')
    return render(request, 'chef_departement/propositions.html', {
        'propositions': qs, 'specialites': dept.specialites.all() if dept else [],
        'f': {'q':q,'annee':annee,'specialite':spe,'statut':statut},
    })


@login_required
@chef_requis
def action_proposition(request, pk):
    dept = _dept(request)
    prop = get_object_or_404(PropositionTheme, pk=pk, etudiant__specialite__departement=dept)
    if request.method == 'POST':
        action, motif = request.POST.get('action'), request.POST.get('motif','').strip()
        if action == 'valider':
            prop.statut = 'valide'; prop.date_decision = timezone.now(); prop.save()
            if prop.etudiant.user:
                Notification.envoyer(prop.etudiant.user, "Thème validé ✓",
                    f"Votre thème « {prop.theme[:80]} » est validé. Vous pouvez déposer votre dossier.",
                    Notification.TYPE_SUCCES, '/etudiant/deposer-dossier/')
            messages.success(request, "Proposition validée.")
        elif action == 'rejeter' and motif:
            prop.statut = 'rejete'; prop.motif_rejet = motif; prop.date_decision = timezone.now(); prop.save()
            if prop.etudiant.user:
                Notification.envoyer(prop.etudiant.user, "Thème rejeté",
                    f"Motif : {motif}", Notification.TYPE_REJET, '/etudiant/proposer-theme/')
            messages.warning(request, "Proposition rejetée.")
    return redirect('chef:propositions')


# ── DOSSIERS ──────────────────────────────────────────────
@login_required
@chef_requis
def dossiers(request):
    dept = _dept(request)
    qs = DossierSoutenance.objects.filter(etudiant__specialite__departement=dept
        ).select_related('etudiant__specialite','proposition') if dept else DossierSoutenance.objects.none()
    q, annee, spe, statut = (request.GET.get(k,'') for k in ['q','annee','specialite','statut'])
    # Par défaut : en_instruction + rejete_ia + rejete_chef + depot_final_soumis
    if not statut:
        qs = qs.filter(statut__in=['en_instruction','rejete_ia','rejete_chef','depot_final_soumis'])
    elif statut != 'tous':
        qs = qs.filter(statut=statut)
    if q: qs = qs.filter(Q(etudiant__nom__icontains=q)|Q(etudiant__prenom__icontains=q))
    if annee: qs = qs.filter(etudiant__annee_academique=annee)
    if spe:   qs = qs.filter(etudiant__specialite__code=spe)
    qs = qs.order_by('-date_soumission')
    return render(request, 'chef_departement/dossiers.html', {
        'dossiers': qs, 'specialites': dept.specialites.all() if dept else [],
        'statuts': DossierSoutenance.STATUT_CHOICES,
        'f': {'q':q,'annee':annee,'specialite':spe,'statut':statut},
    })

@login_required
@chef_requis
def action_dossier(request, pk):
    dept = _dept(request)
    # On récupère le dossier sans filtrer trop strictement le statut ici
    # pour pouvoir gérer à la fois l'instruction et le dépôt final.
    dossier = get_object_or_404(
        DossierSoutenance, pk=pk,
        etudiant__specialite__departement=dept
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        motif = request.POST.get('motif', '').strip()

        if action == 'valider':
            # --- CAS DU DÉPÔT FINAL (Après soutenance) ---
            if dossier.statut == 'depot_final_soumis':
                dossier.statut = 'archive'
                dossier.save()
                
                if dossier.etudiant.user:
                    Notification.envoyer(
                        dossier.etudiant.user,
                        "✓ Processus terminé — Mémoire archivé",
                        "Félicitations ! Votre document final a été validé et archivé. Il est désormais disponible dans la bibliothèque numérique.",
                        Notification.TYPE_SUCCES,
                    )
                
                # Notification à la bibliothèque (Correction de la syntaxe ici)
                theme_titre = dossier.proposition.theme[:100] if dossier.proposition else '—'
                for biblio in User.objects.filter(role='bibliotheque'):
                    Notification.envoyer(
                        biblio,
                        f"Nouveau mémoire à indexer — {dossier.etudiant.nom}",
                        f"Étudiant : {dossier.etudiant.prenom} {dossier.etudiant.nom} | Thème : {theme_titre}",
                        Notification.TYPE_INFO, 
                        '/bibliotheque/memoires/'
                    )
                messages.success(request, "Dépôt final validé et archivé. Bibliothèque notifiée.")
            
            # --- CAS DU DOSSIER INITIAL (Avant soutenance) ---
            else:
                dossier.statut = 'valide_chef'
                dossier.save()
                if dossier.etudiant.user:
                    Notification.envoyer(
                        dossier.etudiant.user,
                        "Dossier de soutenance validé ✓",
                        "Votre dossier est conforme. Le chef de département va maintenant procéder à la proposition du jury.",
                        Notification.TYPE_SUCCES,
                    )
                messages.success(request, "Dossier de soutenance validé avec succès.")

        elif action == 'rejeter' and motif:
            # Rejet du dépôt final pour corrections
            if dossier.statut == 'depot_final_soumis':
                dossier.statut = 'corrections'
                dossier.motif_rejet = motif
                dossier.save()
                if dossier.etudiant.user:
                    Notification.envoyer(
                        dossier.etudiant.user,
                        "Dépôt final rejeté — Corrections requises",
                        f"Motif : {motif}. Veuillez corriger le document et le soumettre à nouveau.",
                        Notification.TYPE_REJET, 
                        '/etudiant/deposer-dossier/'
                    )
                messages.warning(request, "Dépôt final renvoyé pour corrections.")
            
            # Rejet du dossier de soutenance initial
            else:
                dossier.statut = 'rejete_chef'
                dossier.motif_rejet = motif
                dossier.save()
                if dossier.etudiant.user:
                    Notification.envoyer(
                        dossier.etudiant.user, 
                        "Dossier de soutenance rejeté",
                        f"Motif : {motif}", 
                        Notification.TYPE_REJET, 
                        '/etudiant/deposer-dossier/'
                    )
                messages.warning(request, "Dossier de soutenance rejeté.")

    return redirect('chef:dossiers')


# ── INSTRUIRE (jury + calendrier) ─────────────────────────
@login_required
@chef_requis
def instruire(request):
    dept = _dept(request)
    # Par défaut : valide_chef + rejete_de (DE a rejeté → chef doit corriger)
    statuts = [DossierSoutenance.STATUT_VALIDE_CHEF, DossierSoutenance.STATUT_REJETE_DE]
    if request.GET.get('tous'): statuts += [DossierSoutenance.STATUT_JURY_PROPOSE,
        DossierSoutenance.STATUT_VALIDE_DE, DossierSoutenance.STATUT_VALIDE_DG,
        DossierSoutenance.STATUT_PROGRAMME]
    qs = DossierSoutenance.objects.filter(etudiant__specialite__departement=dept, statut__in=statuts
        ).select_related('etudiant__specialite','proposition') if dept else DossierSoutenance.objects.none()
    q, annee, spe = (request.GET.get(k,'') for k in ['q','annee','specialite'])
    if q: qs = qs.filter(Q(etudiant__nom__icontains=q)|Q(etudiant__prenom__icontains=q))
    if annee: qs = qs.filter(etudiant__annee_academique=annee)
    if spe:   qs = qs.filter(etudiant__specialite__code=spe)
    return render(request, 'chef_departement/instruire.html', {
        'dossiers': qs, 'specialites': dept.specialites.all() if dept else [],
        'f': {'q':q,'annee':annee,'specialite':spe},
    })


@login_required
@chef_requis
def proposer_jury(request, pk):
    dept = _dept(request)
    dossier = get_object_or_404(DossierSoutenance, pk=pk, etudiant__specialite__departement=dept)
    # Chercher proposition existante pour modification
    try: prop_existante = dossier.proposition_jury
    except: prop_existante = None

    formulaire = FormulairePropositionJury(request.POST or None, instance=prop_existante, chef=request.user)
    if request.method == 'POST' and formulaire.is_valid():
        prop = formulaire.save(commit=False)
        prop.chef   = request.user
        prop.dossier = dossier
        prop.statut = 'soumise'   # Toujours remettre à 'soumise' lors d'une (re)soumission
        prop.motif_rejet = ''
        prop.save()
        formulaire.save_m2m()
        # Mettre à jour le statut du dossier
        if dossier.statut not in [DossierSoutenance.STATUT_VALIDE_DE, DossierSoutenance.STATUT_VALIDE_DG, DossierSoutenance.STATUT_PROGRAMME]:
            dossier.statut = DossierSoutenance.STATUT_JURY_PROPOSE; dossier.save()
        for de in User.objects.filter(role='directeur_etudes'):
            Notification.envoyer(de, "Proposition de jury soumise",
                f"{dossier.etudiant} — soutenance le {prop.date_proposee}", Notification.TYPE_INFO, '/directeur/propositions/')
        messages.success(request, "Proposition soumise au directeur des études.")
        return redirect('chef:instruire')
    return render(request, 'chef_departement/proposer_jury.html', {'formulaire': formulaire, 'dossier': dossier, 'modif': bool(prop_existante)})


# ── JURYS ──────────────────────────────────────────────────
@login_required
@chef_requis
def jurys(request):
    return render(request, 'chef_departement/jurys.html', {'jurys': MembreJury.objects.filter(chef=request.user)})


@login_required
@chef_requis
def creer_jury(request):
    if request.method == 'POST':
        form = FormulaireMembreJury(request.POST)
        if form.is_valid():
            jury = form.save(commit=False); jury.chef = request.user; jury.save()
            u, created = User.objects.get_or_create(username=form.cleaned_data['username_jury'],
                defaults=dict(email=jury.email, first_name=jury.prenom, last_name=jury.nom, role='jury', telephone=jury.telephone))
            if created or form.cleaned_data.get('password_jury'):
                u.set_password(form.cleaned_data['password_jury']); u.save()
            jury.user = u; jury.save()
            messages.success(request, f"Jury {jury.prenom} {jury.nom} créé. ID : {u.username}")
    return redirect('chef:jurys')


@login_required
@chef_requis
def modifier_jury(request, pk):
    jury = get_object_or_404(MembreJury, pk=pk, chef=request.user)
    if request.method == 'POST':
        form = FormulaireMembreJury(request.POST, instance=jury)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get('password_jury') and jury.user:
                jury.user.set_password(form.cleaned_data['password_jury']); jury.user.save()
            messages.success(request, "Jury mis à jour.")
    return redirect('chef:jurys')


@login_required
@chef_requis
def supprimer_jury(request, pk):
    jury = get_object_or_404(MembreJury, pk=pk, chef=request.user)
    if request.method == 'POST':
        jury.delete(); messages.success(request, "Jury supprimé.")
    return redirect('chef:jurys')


# ── NOTIFICATIONS ──────────────────────────────────────────
@login_required
@chef_requis
def notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    if request.GET.get('marquer'):
        notifs.filter(lue=False).update(lue=True)
        return redirect('chef:notifications')
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'chef_departement/notifications.html', {'notifications': notifs})

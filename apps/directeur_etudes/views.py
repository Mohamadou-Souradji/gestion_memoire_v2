from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from apps.authentication.decorators import directeur_requis
from apps.authentication.forms import FormulaireCreationCompte
from apps.etudiant.models import (Departement, Etudiant, Specialite,
                                   DossierSoutenance, Notification, ParametreSysteme)
from apps.chef_departement.models import PropositionJury
from apps.etudiant.forms import FormulaireEtudiantDE
import logging


User = get_user_model()


@login_required
@directeur_requis
def tableau_de_bord(request):
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)
    return render(request, 'directeur_etudes/tableau_de_bord.html', {
        'props_a_valider':  PropositionJury.objects.filter(statut='soumise').count(),
        'props_chez_dg':    PropositionJury.objects.filter(statut='validee_de').count(),
        'props_traites':    PropositionJury.objects.filter(statut__in=['validee_de','rejetee_de','validee_dg','rejetee_dg']).count(),
        'props_rejetes':    PropositionJury.objects.filter(statut='rejetee_de').count(),
        'nb_programes':     DossierSoutenance.objects.filter(statut='programme').count(),
        'nb_soutenus':      DossierSoutenance.objects.filter(statut__in=['soutenu','archive']).count(),
        'nb_etudiants':     Etudiant.objects.count(),
        'departements':     Departement.objects.prefetch_related('specialites').all(),
        'notifications':    notifs,
        'nb_notifs':        notifs.count(),
    })


# ── PROPOSITIONS JURY ────────────────────────────────────────
@login_required
@directeur_requis
def propositions(request):
    qs = PropositionJury.objects.select_related(
        'dossier__etudiant__specialite__departement','chef').order_by('-date_soumission')
    q, annee, spe, statut = (request.GET.get(k,'') for k in ['q','annee','specialite','statut'])
    statut = statut or 'soumise'
    if q:     qs = qs.filter(Q(dossier__etudiant__nom__icontains=q)|Q(dossier__etudiant__prenom__icontains=q)|Q(dossier__proposition__theme__icontains=q))
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
                Notification.envoyer(dg,
                    "Proposition de jury à valider",
                    f"Le DE a validé une proposition.\nÉtudiant : {prop.dossier.etudiant}\nSoutenance prévue le : {prop.date_proposee}",
                    Notification.TYPE_INFO, '/dg/validation/')
            messages.success(request, "Validée. DG notifiée.")
        elif action == 'rejeter' and motif:
            prop.statut = 'rejetee_de'; prop.motif_rejet = motif; prop.save()
            prop.dossier.statut = DossierSoutenance.STATUT_REJETE_DE; prop.dossier.save()
            Notification.envoyer(prop.chef, "Proposition rejetée par le DE",
                f"Motif : {motif}. Corrigez et soumettez à nouveau.", Notification.TYPE_REJET, '/chef/instruire/')
            messages.warning(request, "Rejetée. Chef notifié.")
    return redirect('directeur:propositions')


@login_required
@directeur_requis
def valider_tout(request):
    if request.method == 'POST':
        props = PropositionJury.objects.filter(statut='soumise')
        count = props.count()
        for prop in props:
            prop.statut = 'validee_de'; prop.save()
            for dg in User.objects.filter(role='direction_generale'):
                Notification.envoyer(dg,
                    "Propositions jury validées en lot",
                    f"Le DE a validé {count} proposition(s) — en attente de votre validation finale.",
                    Notification.TYPE_INFO, '/dg/validation/')
        messages.success(request, f"{count} proposition(s) transmises à la DG.")
    return redirect('directeur:propositions')


# ── ÉTUDIANTS ────────────────────────────────────────────────
@login_required
@directeur_requis
def etudiants(request):
    qs = Etudiant.objects.select_related('specialite__departement','user').all()
    q, dept, spe, annee = (request.GET.get(k,'') for k in ['q','departement','specialite','annee'])
    if q:    qs = qs.filter(Q(nom__icontains=q)|Q(prenom__icontains=q)|Q(matricule__icontains=q))
    if dept: qs = qs.filter(specialite__departement__code=dept)
    if spe:  qs = qs.filter(specialite__code=spe)
    if annee:qs = qs.filter(annee_academique=annee)
    return render(request, 'directeur_etudes/etudiants.html', {
        'etudiants': qs, 'departements': Departement.objects.all(),
        'specialites': Specialite.objects.all(),
        'f': {'q':q,'departement':dept,'specialite':spe,'annee':annee},
    })
import logging
logger = logging.getLogger(__name__)

from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
@directeur_requis
def creer_etudiant(request):
    from apps.etudiant.forms import FormulaireEtudiantDE

    if request.method == 'POST':
        form = FormulaireEtudiantDE(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            # =========================
            # 1. Vérifier email unique
            # =========================
            if User.objects.filter(email=data['email']).exists():
                messages.error(request, "Cet email est déjà utilisé par un autre compte.")
                return redirect('directeur:etudiants')

            # =========================
            # 2. Création ou mise à jour étudiant
            # =========================
            etudiant, created = Etudiant.objects.get_or_create(
                matricule=data['matricule'],
                defaults={
                    'nom': data['nom'],
                    'prenom': data['prenom'],
                    'email': data['email'],
                    'specialite': data['specialite'],
                    'annee_academique': data['annee_academique'],
                    'promotion': data['promotion'],
                }
            )

            if not created:
                etudiant.nom = data['nom']
                etudiant.prenom = data['prenom']
                etudiant.email = data['email']
                etudiant.specialite = data['specialite']
                etudiant.annee_academique = data['annee_academique']
                etudiant.promotion = data['promotion']
                etudiant.save()

            # =========================
            # 3. Création user si inexistant
            # =========================
            if not etudiant.user:
                username = etudiant.matricule
                password = "Student1234"

                # sécurité : éviter doublon username
                if User.objects.filter(username=username).exists():
                    messages.error(request, "Un compte utilisateur existe déjà pour ce matricule.")
                    return redirect('directeur:etudiants')

                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=etudiant.prenom,
                    last_name=etudiant.nom,
                    email=etudiant.email,
                    role='etudiant'
                )

                etudiant.user = user
                etudiant.save()

                logger.warning(f"[USER CREATED] {username} / Student1234")

            else:
                logger.warning(f"[USER EXISTS] {etudiant.matricule}")

            messages.success(
                request,
                f"Étudiant enregistré : {etudiant.nom} {etudiant.prenom} | login = {etudiant.matricule}"
            )

        else:
            for e in form.errors.values():
                messages.error(request, e)

    return redirect('directeur:etudiants')
@login_required
@directeur_requis
def modifier_etudiant(request, pk):
    etudiant = get_object_or_404(Etudiant, pk=pk)
    if request.method == 'POST':
        from apps.etudiant.forms import FormulaireEtudiantDE
        form = FormulaireEtudiantDE(request.POST, instance=etudiant)
        if form.is_valid(): form.save(); messages.success(request, "Étudiant mis à jour.")
        else:
            for e in form.errors.values(): messages.error(request, e.as_text())
    return redirect('directeur:etudiants')


@login_required
@directeur_requis
def supprimer_etudiant(request, pk):
    etudiant = get_object_or_404(Etudiant, pk=pk)
    if request.method == 'POST':
        etudiant.delete(); messages.success(request, "Étudiant supprimé.")
    return redirect('directeur:etudiants')


# ── UTILISATEURS ─────────────────────────────────────────────
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
            if user.role == 'chef_departement':
                dept_id = request.POST.get('departement_id')
                if dept_id:
                    try:
                        dept = Departement.objects.get(pk=dept_id)
                        dept.chef = user; dept.save()
                    except Exception:
                        pass
            messages.success(request, f"Compte créé : {user.get_full_name()}")
        else:
            for e in form.errors.values(): messages.error(request, e.as_text())
    return redirect('directeur:utilisateurs')


@login_required
@directeur_requis
def modifier_utilisateur(request, pk):
    """Modifier un compte utilisateur existant."""
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        # Mise à jour des champs modifiables
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name  = request.POST.get('last_name',  user.last_name).strip()
        user.email      = request.POST.get('email',      user.email).strip()
        user.telephone  = request.POST.get('telephone',  getattr(user, 'telephone', '')).strip()
        nouveau_role    = request.POST.get('role', user.role)
        if nouveau_role in dict(User.ROLE_CHOICES):
            user.role = nouveau_role
        # Changer le mot de passe si fourni
        mdp = request.POST.get('mot_de_passe', '').strip()
        if mdp:
            user.set_password(mdp)
        try:
            user.save()
            # Réaffecter département si chef
            if user.role == 'chef_departement':
                dept_id = request.POST.get('departement_id')
                if dept_id:
                    try:
                        dept = Departement.objects.get(pk=dept_id)
                        dept.chef = user; dept.save()
                    except Exception:
                        pass
            messages.success(request, f"Compte de {user.get_full_name()} mis à jour.")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    return redirect('directeur:utilisateurs')


@login_required
@directeur_requis
def supprimer_utilisateur(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user.pk != request.user.pk:
            user.delete(); messages.success(request, "Compte supprimé.")
        else:
            messages.error(request, "Impossible de supprimer votre propre compte.")
    return redirect('directeur:utilisateurs')


@login_required
@directeur_requis
def toggle_compte(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST' and user.pk != request.user.pk:
        user.is_active = not user.is_active
        user.save()
        messages.success(request, f"Compte {'activé' if user.is_active else 'bloqué'}.")
    return redirect('directeur:utilisateurs')


# ── PARAMÈTRES SYSTÈME ───────────────────────────────────────
@login_required
@directeur_requis
def parametres(request):
    """Configure les taux IA, similarité et OTP."""
    params = ParametreSysteme.get()
    if request.method == 'POST':
        try:
            taux_ia = int(request.POST.get('taux_ia_max', params.taux_ia_max))
            seuil   = int(request.POST.get('seuil_similarite_theme', params.seuil_similarite_theme))
            otp     = request.POST.get('otp_actif') == '1'
            # Validation
            if not (1 <= taux_ia <= 100):
                raise ValueError("Le taux IA doit être entre 1 et 100.")
            if not (1 <= seuil <= 100):
                raise ValueError("Le seuil de similarité doit être entre 1 et 100.")
            params.taux_ia_max            = taux_ia
            params.seuil_similarite_theme = seuil
            params.otp_actif              = otp
            params.save()
            messages.success(request,
                f"Paramètres mis à jour — Taux IA : {taux_ia}% | Similarité : {seuil}% | OTP : {'Activé' if otp else 'Désactivé'}")
        except ValueError as e:
            messages.error(request, str(e))
    return render(request, 'directeur_etudes/parametres.html', {'params': params})


# ── NOTIFICATIONS ────────────────────────────────────────────
@login_required
@directeur_requis
def notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'directeur_etudes/notifications.html', {'notifications': notifs})

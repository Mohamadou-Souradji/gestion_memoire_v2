from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from difflib import SequenceMatcher
import re
from apps.authentication.decorators import etudiant_requis
from .models import (Etudiant, PropositionTheme, DossierSoutenance,
                     Notification, analyser_document_ia)
from .forms import (FormulaireVerificationMatricule, FormulairePropositionTheme,
                    FormulaireDossierSoutenance, FormulaireDepotFinal)


# Mots vides à ignorer dans la comparaison de thèmes
_MOTS_VIDES = {'le','la','les','de','du','des','un','une','et','ou','en','au','aux',
               'pour','par','sur','dans','avec','que','qui','une','est','sont',
               'the','of','and','or','in','a','an','to','for','by','on','with'}


def _mots_significatifs(texte):
    """Extrait les mots significatifs (longueur > 3, pas mot vide)."""
    mots = re.findall(r'[a-zàâéèêëîïôùûüç]{4,}', texte.lower())
    return [m for m in mots if m not in _MOTS_VIDES]


def _similarite(a, b):
    """Similarité globale entre deux chaînes (0-1)."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _similarite_mots_cles(a, b):
    """Similarité basée sur les mots significatifs communs."""
    mots_a = set(_mots_significatifs(a))
    mots_b = set(_mots_significatifs(b))
    if not mots_a or not mots_b:
        return 0.0
    communs = mots_a & mots_b
    # Jaccard : intersection / union
    return len(communs) / len(mots_a | mots_b)


def _theme_similaire_existant(theme_saisi, seuil=0.60):
    """
    Cherche un thème similaire parmi les thèmes déjà traités.
    Seuil par défaut : 20% — combinaison SequenceMatcher + mots-clés.
    2-3 mots communs anodins ne déclenchent pas de rejet.
    """
    if len(theme_saisi.strip()) < 10:
        return None, 0

    themes_existants = PropositionTheme.objects.exclude(
        statut=PropositionTheme.STATUT_REJETE
    ).select_related('etudiant__specialite')

    meilleur, meilleur_score = None, 0
    for prop in themes_existants:
        # Score combiné : 60% SequenceMatcher + 40% mots-clés
        s_global = _similarite(theme_saisi, prop.theme)
        s_mots   = _similarite_mots_cles(theme_saisi, prop.theme)
        score    = 0.6 * s_global + 0.4 * s_mots
        if score > meilleur_score:
            meilleur_score = score
            meilleur = prop

    if meilleur and meilleur_score >= seuil:
        return meilleur, meilleur_score
    return None, 0


@login_required
@etudiant_requis
def tableau_de_bord(request):
    try:
        etudiant = request.user.fiche_etudiant
    except Exception:
        etudiant = None
    ctx = {'etudiant': etudiant}
    if etudiant:
        propositions  = etudiant.propositions.all()
        dossiers      = etudiant.dossiers.select_related('proposition','programmation').all()
        dossier_actif = dossiers.first()
        programmation = pv = None
        if dossier_actif:
            try: programmation = dossier_actif.programmation
            except: pass
            try: pv = dossier_actif.pv
            except: pass
        ctx.update({
            'propositions': propositions,
            'dossiers': dossiers,
            'dossier_actif': dossier_actif,
            'programmation': programmation,
            'pv': pv,
        })
    ctx['notifications'] = Notification.objects.filter(destinataire=request.user, lue=False)[:5]
    return render(request, 'etudiant/tableau_de_bord.html', ctx)


@login_required
@etudiant_requis
def verifier_matricule(request):
    try:
        if request.user.fiche_etudiant:
            return redirect('etudiant:proposer_theme')
    except Exception:
        pass
    formulaire = FormulaireVerificationMatricule(request.POST or None)
    if request.method == 'POST' and formulaire.is_valid():
        mat   = formulaire.cleaned_data['matricule']
        annee = formulaire.cleaned_data['annee_academique']
        try:
            etudiant = Etudiant.objects.get(matricule=mat, annee_academique=annee, user__isnull=True)
            etudiant.user = request.user; etudiant.save()
            messages.success(request, f"Bienvenue {etudiant.prenom} {etudiant.nom} ! Fiche trouvée — {etudiant.specialite}.")
            return redirect('etudiant:proposer_theme')
        except Etudiant.DoesNotExist:
            if Etudiant.objects.filter(matricule=mat, annee_academique=annee).exists():
                messages.error(request, "Ce matricule est déjà associé à un autre compte.")
            else:
                messages.error(request, "Aucun étudiant trouvé. Vérifiez votre matricule et l'année académique.")
    return render(request, 'etudiant/verifier_matricule.html', {'formulaire': formulaire})


@login_required
@etudiant_requis
def proposer_theme(request):
    try:
        etudiant = request.user.fiche_etudiant
    except Exception:
        messages.warning(request, "Veuillez d'abord vérifier votre matricule.")
        return redirect('etudiant:verifier_matricule')

    # Vérifier si une proposition active existe déjà
    prop_active = etudiant.propositions.filter(statut__in=['en_attente', 'valide']).first()
    if prop_active:
        messages.info(request, "Vous avez déjà une proposition en cours ou validée.")
        return redirect('etudiant:tableau_de_bord')

    formulaire = FormulairePropositionTheme(request.POST or None)
    doublon = None
    score_similitude = 0

    if request.method == 'POST' and formulaire.is_valid():
        theme_saisi = formulaire.cleaned_data['theme']

        # Vérification similarité (75% de seuil)
        similaire, score = _theme_similaire_existant(theme_saisi, seuil=0.60)
        if similaire:
            doublon = similaire
            score_similitude = round(score * 100, 1)
            messages.warning(request,
                f"Thème similaire à {score_similitude}% avec celui de "
                f"{similaire.etudiant.prenom} {similaire.etudiant.nom} "
                f"({similaire.etudiant.specialite}, {similaire.etudiant.annee_academique}). "
                "Proposez un thème différent. Si votre sujet est proche mais distinct, le chef de département jugera lors de la validation.")
            return render(request, 'etudiant/proposer_theme.html',
                          {'formulaire': formulaire, 'etudiant': etudiant,
                           'doublon': doublon, 'score': score_similitude})

        prop = formulaire.save(commit=False)
        prop.etudiant = etudiant
        prop.save()

        chef = etudiant.chef_departement
        if chef:
            Notification.envoyer(chef,
                "Nouvelle proposition de thème",
                f"{etudiant.prenom} {etudiant.nom} ({etudiant.matricule}) — "
                f"{etudiant.specialite} — a soumis : « {prop.theme[:80]} »\n"
                f"Promotion : {prop.promotion}",
                Notification.TYPE_INFO, '/chef/propositions/')
        messages.success(request, "Proposition soumise. Le chef de département sera notifié.")
        return redirect('etudiant:tableau_de_bord')

    return render(request, 'etudiant/proposer_theme.html',
                  {'formulaire': formulaire, 'etudiant': etudiant})


@login_required
@etudiant_requis
def deposer_dossier(request):
    """Dépôt avant soutenance ET dépôt final après PV — même page."""
    try:
        etudiant = request.user.fiche_etudiant
    except Exception:
        return redirect('etudiant:verifier_matricule')

    prop_validee = etudiant.propositions.filter(statut='valide').first()
    if not prop_validee:
        messages.warning(request, "Vous devez avoir une proposition validée avant de déposer un dossier.")
        return redirect('etudiant:tableau_de_bord')

    # Chercher dossier existant
    dossier_actif = etudiant.dossiers.order_by('-date_soumission').first()
    pv = None
    if dossier_actif:
        try: pv = dossier_actif.pv
        except: pass

    # Si PV saisi → mode dépôt final
    # Inclure STATUT_REJETE_IA ici car si le PDF final est rejeté par IA,
    # le statut repasse à rejete_ia mais le PV existe → on reste en mode final
    if dossier_actif and pv and dossier_actif.statut in [
            DossierSoutenance.STATUT_SOUTENU,
            DossierSoutenance.STATUT_CORRECTIONS,
            DossierSoutenance.STATUT_REJETE_IA,
            'depot_final_soumis']:

        formulaire_final = FormulaireDepotFinal(
            request.POST or None, request.FILES or None, instance=dossier_actif)

        if request.method == 'POST' and request.POST.get('mode') == 'final':
            if formulaire_final.is_valid():
                # Analyse IA du document final
                dossier_tmp = formulaire_final.save(commit=False)
                dossier_tmp.statut = 'depot_final_soumis'
                dossier_tmp.save()

                from django.conf import settings as dj_settings
                seuil = getattr(dj_settings, 'AI_DETECTION_THRESHOLD', 70)
                taux, _ = analyser_document_ia(dossier_tmp)

                if dossier_tmp.statut == DossierSoutenance.STATUT_REJETE_IA:
                    # Rejet IA dépôt final : remettre en CORRECTIONS pour re-dépôt
                    dossier_tmp.statut = DossierSoutenance.STATUT_CORRECTIONS
                    dossier_tmp.save()
                    messages.error(request,
                        f"Document final rejeté automatiquement — taux IA : {taux}% "
                        f"(seuil autorisé : {seuil}%). Corrigez votre document et re-déposez.")
                    return redirect('etudiant:deposer_dossier')
                else:
                    # Notifier le chef pour validation
                    chef = etudiant.chef_departement
                    if chef:
                        Notification.envoyer(chef,
                            "Dépôt final à valider",
                            f"{etudiant.prenom} {etudiant.nom} a déposé son document final "
                            f"(taux IA : {taux}%). Validation requise avant indexation.",
                            Notification.TYPE_INFO, '/chef/dossiers/')
                    messages.success(request, f"Document final soumis (taux IA : {taux}%). En attente de validation du chef.")
                    return redirect('etudiant:deposer_dossier')

        from django.conf import settings as dj_settings
        return render(request, 'etudiant/deposer_dossier.html', {
            'mode': 'final',
            'formulaire_final': formulaire_final,
            'dossier': dossier_actif,
            'pv': pv,
            'seuil_ia': getattr(dj_settings, 'AI_DETECTION_THRESHOLD', 70),
        })

    # Vérifier qu'un dossier actif n'existe pas déjà (hors rejeté/archivé)
    if dossier_actif and dossier_actif.statut not in [
            DossierSoutenance.STATUT_REJETE_IA,
            DossierSoutenance.STATUT_REJETE_CHEF,
            DossierSoutenance.STATUT_ARCHIVE,
            DossierSoutenance.STATUT_CORRECTIONS,  # rejet dépôt final → re-déposer
            DossierSoutenance.STATUT_SOUTENU,       # soutenu → dépôt final
            'depot_final_soumis',                   # déjà soumis → informer
            ]:
        messages.info(request, "Vous avez déjà un dossier en cours.")
        return redirect('etudiant:tableau_de_bord')

    # Si archivé, vérifier qu'une nouvelle fiche étudiant existe pour une nouvelle année
    if dossier_actif and dossier_actif.statut == DossierSoutenance.STATUT_ARCHIVE:
        # Permettre seulement si l'étudiant a une fiche avec une année académique différente
        if dossier_actif.etudiant.annee_academique == etudiant.annee_academique:
            messages.warning(request,
                "Vous avez déjà complété le processus pour l'année "
                f"{etudiant.annee_academique}. Pour recommencer, votre fiche "
                "doit être mise à jour avec une nouvelle année académique par l'administration.")
            return redirect('etudiant:tableau_de_bord')

    from django.conf import settings as dj_settings
    seuil = getattr(dj_settings, 'AI_DETECTION_THRESHOLD', 70)
    formulaire = FormulaireDossierSoutenance(request.POST or None, request.FILES or None)

    if request.method == 'POST' and request.POST.get('mode') == 'initial' and formulaire.is_valid():
        dossier = formulaire.save(commit=False)
        dossier.etudiant    = etudiant
        dossier.proposition = prop_validee
        dossier.statut      = DossierSoutenance.STATUT_ANALYSE_IA
        dossier.save()

        taux, _ = analyser_document_ia(dossier)

        if dossier.statut == DossierSoutenance.STATUT_REJETE_IA:
            Notification.envoyer(request.user,
                "Dossier rejeté — taux IA trop élevé",
                dossier.motif_rejet, Notification.TYPE_REJET, '/etudiant/deposer-dossier/')
            messages.error(request, f"Dossier rejeté. Taux IA : {taux}% (seuil : {seuil}%).")
        else:
            chef = etudiant.chef_departement
            if chef:
                Notification.envoyer(chef,
                    "Nouveau dossier à instruire",
                    f"{etudiant.prenom} {etudiant.nom} — {etudiant.specialite} — "
                    f"taux IA : {taux}%.",
                    Notification.TYPE_INFO, '/chef/dossiers/')
            messages.success(request, f"Dossier soumis. Taux IA : {taux}%. En attente de validation.")
        return redirect('etudiant:tableau_de_bord')

    return render(request, 'etudiant/deposer_dossier.html', {
        'mode': 'initial',
        'formulaire': formulaire,
        'proposition': prop_validee,
        'seuil_ia': seuil,
    })


@login_required
@etudiant_requis
def bibliotheque(request):
    """Consultation de la bibliothèque par l'étudiant."""
    from apps.bibliotheque.models import DocumentBibliotheque
    from apps.etudiant.models import Specialite
    qs = DocumentBibliotheque.objects.filter(est_publie=True)
    q      = request.GET.get('q', '')
    annee  = request.GET.get('annee', '')
    spe    = request.GET.get('specialite', '')
    promo  = request.GET.get('promotion', '')
    if q:     qs = qs.filter(Q(titre__icontains=q)|Q(auteur__icontains=q)|Q(encadreur__icontains=q))
    if annee: qs = qs.filter(annee_academique=annee)
    if spe:   qs = qs.filter(specialite__icontains=spe)
    if promo: qs = qs.filter(promotion__icontains=promo)
    return render(request, 'etudiant/bibliotheque.html', {
        'documents': qs, 'total': qs.count(),
        'specialites': Specialite.objects.values_list('nom', flat=True).distinct(),
        'f': {'q': q, 'annee': annee, 'specialite': spe, 'promotion': promo},
    })


@login_required
@etudiant_requis
def mes_notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'etudiant/notifications.html', {'notifications': notifs})


@login_required
def marquer_notification_lue(request, pk):
    """Marque une notification comme lue et redirige vers son lien."""
    from apps.etudiant.models import Notification
    try:
        notif = Notification.objects.get(pk=pk, destinataire=request.user)
        notif.lue = True
        notif.save()
        lien = notif.lien or request.META.get('HTTP_REFERER', '/')
    except Notification.DoesNotExist:
        lien = '/'
    return redirect(lien)

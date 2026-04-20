from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import ParametreSysteme as PS
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


def _theme_similaire_existant(theme_saisi, seuil=None):
    if seuil is None:
        try:
            from .models import ParametreSysteme
            seuil = ParametreSysteme.get().seuil_similarite_theme / 100.0
        except Exception:
            seuil = 0.60
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
        etudiant = request.user.fiche_etudiant

        # 🔴 SI CYCLE TERMINÉ → ON RESTE ICI (PAS DE REDIRECT)
        dernier_dossier = etudiant.dossiers.order_by('-date_soumission').first()

        if dernier_dossier and dernier_dossier.statut == DossierSoutenance.STATUT_ARCHIVE:
            messages.info(
                request,
                "Votre ancien cycle est terminé. Veuillez revérifier votre matricule pour démarrer un nouveau cycle."
            )
            # on laisse accès à la page
        else:
            # sinon on redirige normalement
            return redirect('etudiant:proposer_theme')

    except Exception:
        pass

    formulaire = FormulaireVerificationMatricule(request.POST or None)

    if request.method == 'POST' and formulaire.is_valid():

        mat = formulaire.cleaned_data['matricule']
        annee = formulaire.cleaned_data['annee_academique']

        try:
            etudiant = Etudiant.objects.get(
                matricule=mat,
                annee_academique=annee,
                user__isnull=True
            )

            etudiant.user = request.user
            etudiant.save()

            messages.success(
                request,
                f"Bienvenue {etudiant.prenom} {etudiant.nom} !"
            )

            return redirect('etudiant:proposer_theme')

        except Etudiant.DoesNotExist:

            if Etudiant.objects.filter(matricule=mat, annee_academique=annee).exists():
                messages.error(request, "Ce matricule est déjà utilisé.")
            else:
                messages.error(request, "Aucun étudiant trouvé.")

    return render(request, 'etudiant/verifier_matricule.html', {
        'formulaire': formulaire
    })

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
        similaire, score = _theme_similaire_existant(theme_saisi)
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
import logging
logger = logging.getLogger(__name__)

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
@etudiant_requis
def deposer_dossier(request):
    from .models import ParametreSysteme as PS

    # =========================
    # ETUDIANT
    # =========================
    try:
        etudiant = request.user.fiche_etudiant
        logger.warning(f"[ETUDIANT] id={etudiant.id} nom={etudiant.nom}")
    except Exception:
        logger.error("[ERREUR] fiche_etudiant introuvable")
        return redirect('etudiant:verifier_matricule')

    # =========================
    # PROPOSITION VALIDÉE
    # =========================
    prop_validee = etudiant.propositions.filter(statut='valide').first()

    if not prop_validee:
        messages.warning(request, "Proposition non validée.")
        return redirect('etudiant:tableau_de_bord')

    # =========================
    # DOSSIER ACTIF
    # =========================
    dossier_actif = etudiant.dossiers.order_by('-date_soumission').first()
    pv = getattr(dossier_actif, 'pv', None) if dossier_actif else None

    # =========================
    # BLOQUAGE ARCHIVE (IMPORTANT)
    # =========================
    if dossier_actif and dossier_actif.statut == DossierSoutenance.STATUT_ARCHIVE:
        messages.error(
            request,
            "Votre cycle est terminé. Veuillez revérifier votre matricule pour commencer un nouveau cycle."
        )
        return redirect('etudiant:verifier_matricule')

    # =========================
    # BLOQUAGE GLOBAL
    # =========================
    if dossier_actif and dossier_actif.statut not in [
        DossierSoutenance.STATUT_REJETE_IA,
        DossierSoutenance.STATUT_REJETE_CHEF,
        DossierSoutenance.STATUT_CORRECTIONS,
    ]:
        messages.info(request, "Vous avez déjà un dossier en cours.")
        return redirect('etudiant:tableau_de_bord')

    # =========================
    # MODE FINAL
    # =========================
    if dossier_actif and pv and dossier_actif.statut in [
        DossierSoutenance.STATUT_SOUTENU,
        DossierSoutenance.STATUT_CORRECTIONS,
        DossierSoutenance.STATUT_DEPOT_FINAL,
    ]:

        formulaire_final = FormulaireDepotFinal(
            request.POST or None,
            request.FILES or None,
            instance=dossier_actif
        )

        if request.method == 'POST' and request.POST.get('mode') == 'final':

            if formulaire_final.is_valid():
                dossier = formulaire_final.save(commit=False)
                dossier.statut = DossierSoutenance.STATUT_DEPOT_FINAL
                dossier.save()

                seuil = PS.get().taux_ia_max

                taux, _ = analyser_document_ia(
                    dossier,
                    seuil_override=seuil,
                    mode='final'
                )

                logger.warning(f"[IA FINAL] taux={taux}")

                # REJET IA FINAL
                if dossier.statut == DossierSoutenance.STATUT_REJETE_IA:
                    dossier.statut = DossierSoutenance.STATUT_CORRECTIONS
                    dossier.save()

                    messages.error(
                        request,
                        "Document rejeté par l’IA. "
                        f"Taux détecté : {taux}% (seuil max : {seuil}%). "
                        "Veuillez corriger votre document."
                    )

                    return redirect('etudiant:deposer_dossier')

                messages.success(request, "Document final soumis.")
                return redirect('etudiant:tableau_de_bord')

        return render(request, 'etudiant/deposer_dossier.html', {
            'mode': 'final',
            'formulaire_final': formulaire_final,
            'dossier': dossier_actif,
            'pv': pv,
            'seuil_ia': PS.get().taux_ia_max,
        })

    # =========================
    # MODE INITIAL
    # =========================
    formulaire = FormulaireDossierSoutenance(
        request.POST or None,
        request.FILES or None
    )

    if request.method == 'POST' and request.POST.get('mode') == 'initial':

        if formulaire.is_valid():

            dossier = formulaire.save(commit=False)
            dossier.etudiant = etudiant
            dossier.proposition = prop_validee
            dossier.statut = DossierSoutenance.STATUT_ANALYSE_IA
            dossier.save()

            seuil = PS.get().taux_ia_max

            taux, _ = analyser_document_ia(
                dossier,
                seuil_override=seuil,
                mode='initial'
            )

            logger.warning(f"[IA INITIAL] taux={taux}")

            # REJET IA INITIAL
            if dossier.statut == DossierSoutenance.STATUT_REJETE_IA:
                dossier.statut = DossierSoutenance.STATUT_CORRECTIONS
                dossier.save()

                messages.error(
                    request,
                    "Dossier rejeté par l’IA. "
                    f"Taux détecté : {taux}% (seuil max : {seuil}%). "
                    "Veuillez corriger votre fichier."
                )

                return redirect('etudiant:deposer_dossier')

            messages.success(request, "Dossier soumis avec succès.")
            return redirect('etudiant:tableau_de_bord')

    return render(request, 'etudiant/deposer_dossier.html', {
        'mode': 'initial',
        'formulaire': formulaire,
        'proposition': prop_validee,
        'seuil_ia': PS.get().taux_ia_max,
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

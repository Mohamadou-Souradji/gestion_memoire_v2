from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.authentication.decorators import bibliothecaire_requis
from apps.etudiant.models import DossierSoutenance, Notification, Specialite
from .models import DocumentBibliotheque
from .forms import FormulaireIndexation


@login_required
@bibliothecaire_requis
def tableau_de_bord(request):
    a_indexer = DossierSoutenance.objects.filter(statut='archive', document_bibliotheque__isnull=True).count()
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)
    return render(request, 'bibliotheque/tableau_de_bord.html', {
        'a_indexer': a_indexer, 'nb_publies': DocumentBibliotheque.objects.filter(est_publie=True).count(),
        'nb_total': DocumentBibliotheque.objects.count(), 'notifications': notifs, 'nb_notifs': notifs.count(),
    })


@login_required
@bibliothecaire_requis
def memoires(request):
    qs = DocumentBibliotheque.objects.all()
    # Dossiers non encore indexés
    # Dossiers archivés sans document bibliothèque associé
    a_traiter = DossierSoutenance.objects.filter(
        statut='archive'
    ).filter(
        document_bibliotheque__isnull=True  # Pas encore indexés
    ).select_related('etudiant__specialite','proposition')
    q, spe, annee, promo, publie = (request.GET.get(k,'') for k in ['q','specialite','annee','promotion','publie'])
    if q: qs = qs.filter(Q(titre__icontains=q)|Q(auteur__icontains=q)|Q(mots_cles__icontains=q))
    if spe:   qs = qs.filter(specialite__icontains=spe)
    if annee: qs = qs.filter(annee_academique=annee)
    if promo: qs = qs.filter(promotion__icontains=promo)
    if publie == '1': qs = qs.filter(est_publie=True)
    elif publie == '0': qs = qs.filter(est_publie=False)
    return render(request, 'bibliotheque/memoires.html', {
        'documents': qs, 'a_traiter': a_traiter, 'specialites': Specialite.objects.all(),
        'f': {'q':q,'specialite':spe,'annee':annee,'promotion':promo,'publie':publie},
    })


@login_required
@bibliothecaire_requis
def indexer(request, pk):
    dossier = get_object_or_404(DossierSoutenance, pk=pk, statut='archive')
    etudiant = dossier.etudiant
    initial = {
        'titre': dossier.proposition.theme if dossier.proposition else '',
        'auteur': f"{etudiant.nom} {etudiant.prenom}",
        'encadreur': dossier.proposition.encadreur if dossier.proposition else '',
        'departement': etudiant.departement.nom, 'specialite': etudiant.specialite.nom,
        'niveau': etudiant.specialite.niveau, 'promotion': etudiant.promotion,
        'annee_academique': etudiant.annee_academique,
        'entreprise_stage': dossier.proposition.entreprise if dossier.proposition else '',
        'note': dossier.pv.note if hasattr(dossier,'pv') else None,
        'mention': dossier.pv.mention if hasattr(dossier,'pv') else '',
    }
    form = FormulaireIndexation(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False); doc.dossier = dossier; doc.est_publie = True; doc.save()
        messages.success(request, f"« {doc.titre} » indexé et publié.")
        return redirect('bibliotheque:memoires')
    return render(request, 'bibliotheque/indexer.html', {'form': form, 'dossier': dossier})


@login_required
@bibliothecaire_requis
def toggle_publication(request, pk):
    doc = get_object_or_404(DocumentBibliotheque, pk=pk)
    if request.method == 'POST':
        doc.est_publie = not doc.est_publie; doc.save()
        messages.success(request, "Publié." if doc.est_publie else "Dépublié.")
    return redirect('bibliotheque:memoires')


@login_required
@bibliothecaire_requis
def notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'bibliotheque/notifications.html', {'notifications': notifs})


def catalogue(request):
    from django.db.models import Q
    docs = DocumentBibliotheque.objects.filter(est_publie=True)
    q = request.GET.get('q','')
    if q: docs = docs.filter(Q(titre__icontains=q)|Q(auteur__icontains=q)|Q(mots_cles__icontains=q))
    return render(request, 'bibliotheque/catalogue.html', {'documents': docs, 'q': q})

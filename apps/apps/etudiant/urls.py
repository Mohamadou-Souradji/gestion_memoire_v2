from django.urls import path
from . import views
app_name = 'etudiant'
urlpatterns = [
    path('',                    views.tableau_de_bord,   name='tableau_de_bord'),
    path('verifier-matricule/', views.verifier_matricule,name='verifier_matricule'),
    path('proposer-theme/',     views.proposer_theme,    name='proposer_theme'),
    path('deposer-dossier/',    views.deposer_dossier,   name='deposer_dossier'),
    path('bibliotheque/',       views.bibliotheque,      name='bibliotheque'),
    path('notifications/',      views.mes_notifications, name='notifications'),
    path('notifications/<int:pk>/lue/', views.marquer_notification_lue, name='marquer_lue'),
]
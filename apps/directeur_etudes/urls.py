from django.urls import path
from . import views
app_name = 'directeur'
urlpatterns = [
    path('',                              views.tableau_de_bord,   name='tableau_de_bord'),
    path('propositions/',                 views.propositions,      name='propositions'),
    path('propositions/<int:pk>/action/', views.action_proposition, name='action_proposition'),
    path('etudiants/',                    views.etudiants,         name='etudiants'),
    path('etudiants/creer/',              views.creer_etudiant,    name='creer_etudiant'),
    path('etudiants/<int:pk>/modifier/',  views.modifier_etudiant, name='modifier_etudiant'),
    path('etudiants/<int:pk>/supprimer/', views.supprimer_etudiant,name='supprimer_etudiant'),
    path('utilisateurs/',                 views.utilisateurs,      name='utilisateurs'),
    path('utilisateurs/creer/',           views.creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/<int:pk>/supprimer/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('notifications/',                views.notifications,     name='notifications'),
    path('propositions/valider-tout/', views.valider_tout, name='valider_tout'),
    path('utilisateurs/<int:pk>/toggle/', views.toggle_compte, name='toggle_compte'),
]
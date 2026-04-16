from django.urls import path
from . import views
app_name = 'chef'
urlpatterns = [
    path('',                             views.tableau_de_bord,  name='tableau_de_bord'),
    path('propositions/',                views.propositions,     name='propositions'),
    path('propositions/<int:pk>/action/',views.action_proposition,name='action_proposition'),
    path('dossiers/',                    views.dossiers,         name='dossiers'),
    path('dossiers/<int:pk>/action/',    views.action_dossier,   name='action_dossier'),
    path('instruire/',                   views.instruire,        name='instruire'),
    path('instruire/<int:pk>/jury/',     views.proposer_jury,    name='proposer_jury'),
    path('jurys/',                       views.jurys,            name='jurys'),
    path('jurys/creer/',                 views.creer_jury,       name='creer_jury'),
    path('jurys/<int:pk>/modifier/',     views.modifier_jury,    name='modifier_jury'),
    path('jurys/<int:pk>/supprimer/',    views.supprimer_jury,   name='supprimer_jury'),
    path('notifications/',               views.notifications,    name='notifications'),
]

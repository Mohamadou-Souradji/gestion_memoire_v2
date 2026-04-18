from django.urls import path
from . import views
app_name = 'jury'
urlpatterns = [
    path('',                     views.tableau_de_bord, name='tableau_de_bord'),
    path('historique/',          views.historique,      name='historique'),
    path('pv/<int:pk>/',         views.saisir_pv,       name='saisir_pv'),
    path('notifications/',       views.notifications,   name='notifications'),
]

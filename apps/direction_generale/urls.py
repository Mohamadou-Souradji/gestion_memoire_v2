from django.urls import path
from . import views
app_name = 'dg'
urlpatterns = [
    path('',                              views.tableau_de_bord,   name='tableau_de_bord'),
    path('validation/',                   views.validation_finale, name='validation_finale'),
    path('validation/<int:pk>/action/',   views.action_proposition, name='action_proposition'),
    path('notifications/',                views.notifications,     name='notifications'),
    path('validation/valider-tout/', views.valider_tout, name='valider_tout'),
]
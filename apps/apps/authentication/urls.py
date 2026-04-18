from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('connexion/',        views.connexion,         name='connexion'),
    path('verification-otp/', views.verification_otp,  name='verification_otp'),
    path('deconnexion/',      views.deconnexion,       name='deconnexion'),
]

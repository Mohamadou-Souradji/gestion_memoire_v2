from django.urls import path
from . import views
app_name = 'bibliotheque'
urlpatterns = [
    path('',                           views.tableau_de_bord, name='tableau_de_bord'),
    path('memoires/',                  views.memoires,        name='memoires'),
    path('memoires/indexer/<int:pk>/', views.indexer,         name='indexer'),
    path('memoires/<int:pk>/toggle/',  views.toggle_publication, name='toggle'),
    path('catalogue/',                 views.catalogue,       name='catalogue'),
    path('notifications/',             views.notifications,   name='notifications'),
]

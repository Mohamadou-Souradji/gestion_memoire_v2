from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def accueil(request):
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())
    return redirect('auth:connexion')


urlpatterns = [
    path('admin/',       admin.site.urls),
    path('',             accueil,                                                name='accueil'),
    path('auth/',        include('apps.authentication.urls',  namespace='auth')),
    path('etudiant/',    include('apps.etudiant.urls',        namespace='etudiant')),
    path('chef/',        include('apps.chef_departement.urls',namespace='chef')),
    path('directeur/',   include('apps.directeur_etudes.urls',namespace='directeur')),
    path('dg/',          include('apps.direction_generale.urls', namespace='dg')),
    path('jury/',        include('apps.jury.urls',            namespace='jury')),
    path('notifications/<int:pk>/lue/', __import__('apps.etudiant.views', fromlist=['marquer_notification_lue']).marquer_notification_lue, name='notif_lue'),
    path('bibliotheque/',include('apps.bibliotheque.urls',    namespace='bibliotheque')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

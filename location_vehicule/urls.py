from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from gestion.admin import custom_admin_site

urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('', include('gestion.urls')),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
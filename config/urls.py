from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from usuarios.views import DashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", DashboardView.as_view(), name="dashboard"),
    path("home/", DashboardView.as_view(), name="home"),
    path("usuarios/", include("usuarios.urls")),
    path("clientes/", include("clientes.urls")),
    path("solicitudes/", include("solicitudes.urls")),
    path("evaluacion/", include("evaluacion.urls")),
    path("creditos/", include("creditos.urls")),
    path("pagos/", include("pagos.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns = [path("__debug__/", include("debug_toolbar.urls"))] + urlpatterns

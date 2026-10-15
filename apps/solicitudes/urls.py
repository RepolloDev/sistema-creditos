from django.urls import path

from . import views

app_name = "solicitudes"

urlpatterns = [
    path("", views.SolicitudListView.as_view(), name="listado"),
    path("nueva/", views.SolicitudCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.SolicitudDetailView.as_view(), name="detalle"),
    path("<int:pk>/garantias/nueva/", views.GarantiaCreateView.as_view(), name="garantia_crear"),
]

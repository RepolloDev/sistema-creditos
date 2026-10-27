from django.urls import path
from . import views

app_name = "solicitudes"

urlpatterns = [
    path("", views.SolicitudListView.as_view(), name="listado"),
    path("nueva/", views.SolicitudCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.SolicitudDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.SolicitudUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.SolicitudDeleteView.as_view(), name="eliminar"),
    path("<int:pk>/garantias/nueva/", views.GarantiaCreateView.as_view(), name="garantia_crear"),
    path("garantias/<int:pk>/editar/", views.GarantiaUpdateView.as_view(), name="garantia_editar"),
    path("garantias/<int:pk>/eliminar/", views.GarantiaDeleteView.as_view(), name="garantia_eliminar"),
]

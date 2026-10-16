from django.urls import path
from . import views

app_name = "pagos"

urlpatterns = [
    path("", views.PagoListView.as_view(), name="listado"),
    path("nuevo/", views.RegistrarPagoView.as_view(), name="registrar"),
    path("<int:pk>/comprobante/", views.ComprobantePagoView.as_view(), name="comprobante"),
    path("<int:pk>/eliminar/", views.PagoDeleteView.as_view(), name="eliminar"),
    path("control-mora/", views.ControlMoraView.as_view(), name="control_mora"),
]

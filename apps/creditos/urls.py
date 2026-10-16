from django.urls import path
from . import views

app_name = "creditos"

urlpatterns = [
    path("", views.CreditoListView.as_view(), name="listado"),
    path("<int:pk>/", views.CreditoDetailView.as_view(), name="detalle"),
    path("<int:pk>/eliminar/", views.CreditoDeleteView.as_view(), name="eliminar"),
    path(
        "solicitud/<int:solicitud_id>/aprobar/", views.AprobarCreditoView.as_view(), name="aprobar"
    ),
    path(
        "solicitud/<int:solicitud_id>/rechazar/",
        views.RechazarCreditoView.as_view(),
        name="rechazar",
    ),
    path("<int:pk>/cronograma/", views.CronogramaView.as_view(), name="cronograma"),
    path("<int:pk>/firmar-contrato/", views.FirmarContratoView.as_view(), name="firmar_contrato"),
    path("<int:pk>/desembolsar/", views.DesembolsarCreditoView.as_view(), name="desembolsar"),
    path("reportes/", views.ReportesView.as_view(), name="reportes"),
]

from django.urls import path
from . import views

app_name = "evaluacion"

urlpatterns = [
    path("", views.EvaluacionListView.as_view(), name="listado"),
    path("nueva/", views.EvaluacionCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.EvaluacionDetailView.as_view(), name="detalle"),
    path("<int:pk>/riesgo/", views.ConsultarRiesgoExternoView.as_view(), name="consultar_riesgo"),
    path("<int:pk>/eliminar/", views.EvaluacionDeleteView.as_view(), name="eliminar"),
]

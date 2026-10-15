from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .forms import EvaluacionCreditoForm
from .models import EvaluacionCredito


class EvaluacionListView(LoginRequiredMixin, ListView):
    """
    Vista stub: Lista de evaluaciones de crédito realizadas.
    """

    model = EvaluacionCredito
    template_name = "evaluacion/evaluacion_list.html"
    context_object_name = "evaluaciones"


class EvaluacionDetailView(LoginRequiredMixin, DetailView):
    """
    Vista stub: Detalle de dictamen técnico, scoring y capacidad de pago.
    """

    model = EvaluacionCredito
    template_name = "evaluacion/evaluacion_detail.html"
    context_object_name = "evaluacion"


class EvaluacionCreateView(LoginRequiredMixin, CreateView):
    """
    Vista stub: CU04 / CU05 / RF05 / RF06 Registro de evaluación de una solicitud.
    """

    model = EvaluacionCredito
    form_class = EvaluacionCreditoForm
    template_name = "evaluacion/evaluacion_form.html"
    success_url = reverse_lazy("evaluacion:listado")


class ConsultarRiesgoExternoView(LoginRequiredMixin, DetailView):
    """
    Vista stub: CU03 / RF04 Consulta interactiva al buró de riesgo externo simulado.
    """

    model = EvaluacionCredito
    template_name = "evaluacion/evaluacion_detail.html"

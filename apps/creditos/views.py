from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView

from .forms import AprobacionCreditoForm, RechazoCreditoForm
from .models import Credito


class CreditoListView(LoginRequiredMixin, ListView):
    """
    Vista stub: Lista general de créditos en cartera.
    """

    model = Credito
    template_name = "creditos/credito_list.html"
    context_object_name = "creditos"


class CreditoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista stub: Detalle del crédito, contrato y estado de desembolso.
    """

    model = Credito
    template_name = "creditos/credito_detail.html"
    context_object_name = "credito"


class AprobarCreditoView(LoginRequiredMixin, FormView):
    """
    Vista stub: CU07 / RF08 Aprobación formal por Jefe de Créditos.
    """

    form_class = AprobacionCreditoForm
    template_name = "creditos/credito_aprobar.html"
    success_url = reverse_lazy("creditos:listado")


class RechazarCreditoView(LoginRequiredMixin, FormView):
    """
    Vista stub: CU08 / RF09 Rechazo justificado de solicitud.
    """

    form_class = RechazoCreditoForm
    template_name = "creditos/credito_rechazar.html"
    success_url = reverse_lazy("creditos:listado")


class CronogramaView(LoginRequiredMixin, DetailView):
    """
    Vista stub: CU10 / RF11 Visualización de la tabla de amortización (cuotas).
    """

    model = Credito
    template_name = "creditos/cronograma.html"
    context_object_name = "credito"


class DesembolsarCreditoView(LoginRequiredMixin, TemplateView):
    """
    Vista stub: CU11 / RF12 Ejecución y confirmación de desembolso bancario.
    """

    template_name = "creditos/credito_detail.html"


class ReportesView(LoginRequiredMixin, TemplateView):
    """
    Vista stub: CU14 / RF15 Dashboard gerencial de reportes y cartera.
    """

    template_name = "creditos/reportes.html"

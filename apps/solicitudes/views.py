from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .forms import GarantiaForm, SolicitudCreditoForm
from .models import Garantia, SolicitudCredito


class SolicitudListView(LoginRequiredMixin, ListView):
    """
    Vista stub: Lista de solicitudes de financiamiento.
    """

    model = SolicitudCredito
    template_name = "solicitudes/solicitud_list.html"
    context_object_name = "solicitudes"


class SolicitudDetailView(LoginRequiredMixin, DetailView):
    """
    Vista stub: Detalle de una solicitud, sus garantías y estado actual.
    """

    model = SolicitudCredito
    template_name = "solicitudes/solicitud_detail.html"
    context_object_name = "solicitud"


class SolicitudCreateView(LoginRequiredMixin, CreateView):
    """
    Vista stub: CU02 / RF03 Registrar nueva solicitud de crédito.
    """

    model = SolicitudCredito
    form_class = SolicitudCreditoForm
    template_name = "solicitudes/solicitud_form.html"
    success_url = reverse_lazy("solicitudes:listado")


class GarantiaCreateView(LoginRequiredMixin, CreateView):
    """
    Vista stub: CU06 / RF07 Registrar garantía asociada a una solicitud.
    """

    model = Garantia
    form_class = GarantiaForm
    template_name = "solicitudes/garantia_form.html"
    success_url = reverse_lazy("solicitudes:listado")

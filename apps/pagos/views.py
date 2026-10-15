from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import PagoForm
from .models import Pago


class PagoListView(LoginRequiredMixin, ListView):
    """
    Vista stub: Registro de pagos / transacciones en ventanilla.
    """

    model = Pago
    template_name = "pagos/pago_list.html"
    context_object_name = "pagos"


class ComprobantePagoView(LoginRequiredMixin, DetailView):
    """
    Vista stub: CU12 / RF13 Emisión de comprobante oficial de pago para cliente.
    """

    model = Pago
    template_name = "pagos/comprobante.html"
    context_object_name = "pago"


class RegistrarPagoView(LoginRequiredMixin, CreateView):
    """
    Vista stub: CU12 / RF13 Registro de abono de cuota por ventanilla.
    """

    model = Pago
    form_class = PagoForm
    template_name = "pagos/pago_form.html"
    success_url = reverse_lazy("pagos:listado")


class ControlMoraView(LoginRequiredMixin, TemplateView):
    """
    Vista stub: CU13 / RF14 Panel de monitoreo de cartera en mora y cuotas vencidas.
    """

    template_name = "pagos/control_mora.html"

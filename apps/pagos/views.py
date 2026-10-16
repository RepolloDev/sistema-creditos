from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView

from creditos.models import Credito, Cuota
from usuarios.models import Usuario
from usuarios.views import RolRequiredMixin
from .forms import PagoForm
from .models import Pago
from .services import calcular_interes_penal, ejecutar_control_mora, registrar_pago_cuota


class PagoListView(RolRequiredMixin, ListView):
    """
    Registro histórico de pagos / transacciones en ventanilla de caja.
    """

    roles_permitidos = [Usuario.Rol.CAJERO, Usuario.Rol.JEFE, Usuario.Rol.GERENTE]
    model = Pago
    template_name = "pagos/pago_list.html"
    context_object_name = "pagos"
    paginate_by = 15

    def get_queryset(self):
        qs = Pago.objects.select_related(
            "cuota", "cuota__credito", "cuota__credito__solicitud__cliente"
        ).order_by("-fecha_pago", "-id")
        q = self.request.GET.get("q", "").strip()
        forma = self.request.GET.get("forma_pago", "").strip()
        if q:
            qs = qs.filter(
                Q(numero_recibo__icontains=q)
                | Q(cuota__credito__numero_credito__icontains=q)
                | Q(cuota__credito__solicitud__cliente__ci__icontains=q)
                | Q(cuota__credito__solicitud__cliente__apellidos__icontains=q)
            )
        if forma:
            qs = qs.filter(forma_pago=forma)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["selected_forma"] = self.request.GET.get("forma_pago", "")
        context["formas_pago"] = Pago.FormaPago.choices
        context["total_recaudado"] = (
            Pago.objects.aggregate(s=Sum("monto"))["s"] or Decimal("0.00")
        )
        return context


class ComprobantePagoView(RolRequiredMixin, DetailView):
    """
    CU12 / RF13: Emisión de comprobante oficial de pago para el cliente.
    """

    roles_permitidos = [Usuario.Rol.CAJERO, Usuario.Rol.JEFE, Usuario.Rol.GERENTE]
    model = Pago
    template_name = "pagos/comprobante.html"
    context_object_name = "pago"

    def get_queryset(self):
        return Pago.objects.select_related(
            "cuota",
            "cuota__credito",
            "cuota__credito__solicitud",
            "cuota__credito__solicitud__cliente",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cuota"] = self.object.cuota
        context["credito"] = self.object.cuota.credito
        context["cliente"] = self.object.cuota.credito.solicitud.cliente
        return context


class RegistrarPagoView(RolRequiredMixin, CreateView):
    """
    CU12 / RF13 / RN08: Registro de abono de cuota en ventanilla por Cajero.
    """

    roles_permitidos = [Usuario.Rol.CAJERO]
    model = Pago
    form_class = PagoForm
    template_name = "pagos/pago_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        credito_id = self.request.GET.get("credito") or self.request.GET.get("credito_id")
        if credito_id:
            kwargs["credito_id"] = credito_id
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        cuota_id = self.request.GET.get("cuota")
        credito_id = self.request.GET.get("credito") or self.request.GET.get("credito_id")
        if cuota_id:
            cuota = Cuota.objects.filter(pk=cuota_id).first()
            if cuota:
                initial["cuota"] = cuota.pk
                initial["monto"] = cuota.saldo_cuota
        elif credito_id:
            cuota = (
                Cuota.objects.filter(credito_id=credito_id)
                .exclude(estado="PAGADA")
                .order_by("numero_cuota")
                .first()
            )
            if cuota:
                initial["cuota"] = cuota.pk
                initial["monto"] = cuota.saldo_cuota
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q_ci = self.request.GET.get("q_ci", "").strip()
        context["q_ci"] = q_ci
        context["titulo"] = "Cobro de Cuota en Ventanilla (CU12)"
        context["boton_texto"] = "Procesar Pago y Emitir Recibo"
        if q_ci:
            context["creditos_encontrados"] = (
                Credito.objects.filter(
                    Q(solicitud__cliente__ci__icontains=q_ci)
                    | Q(numero_credito__icontains=q_ci)
                    | Q(solicitud__cliente__apellidos__icontains=q_ci)
                )
                .exclude(estado="CANCELADO")
                .select_related("solicitud__cliente")
            )
        return context

    def form_valid(self, form):
        cuota = form.cleaned_data["cuota"]
        monto = form.cleaned_data["monto"]
        forma_pago = form.cleaned_data["forma_pago"]
        try:
            pago = registrar_pago_cuota(
                cuota_id=cuota.pk,
                monto=monto,
                forma_pago=forma_pago,
                usuario=self.request.user,
            )
            messages.success(
                self.request,
                f"Pago procesado exitosamente. Recibo Oficial #{pago.numero_recibo} por Bs. {pago.monto}.",
            )
            return redirect("pagos:comprobante", pk=pago.pk)
        except ValidationError as e:
            messages.error(self.request, e.message if hasattr(e, "message") else str(e))
            return self.form_invalid(form)


class ControlMoraView(RolRequiredMixin, TemplateView):
    """
    CU13 / RF14 / RN09: Panel de monitoreo y ejecución de control de mora.
    """

    roles_permitidos = [Usuario.Rol.CAJERO, Usuario.Rol.JEFE, Usuario.Rol.GERENTE]
    template_name = "pagos/control_mora.html"

    def post(self, request, *args, **kwargs):
        resultado = ejecutar_control_mora(usuario=request.user)
        messages.warning(
            request,
            f"Barrido de mora completado: {resultado['cuotas_marcadas_vencidas']} nuevas cuotas marcadas VENCIDAS y {resultado['creditos_pasados_a_mora']} créditos actualizados a EN_MORA (RN09).",
        )
        return redirect("pagos:control_mora")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        cuotas_vencidas_qs = (
            Cuota.objects.filter(Q(estado="VENCIDA") | Q(fecha_vencimiento__lt=hoy, saldo_cuota__gt=0))
            .exclude(estado="PAGADA")
            .select_related("credito", "credito__solicitud__cliente")
            .order_by("fecha_vencimiento")
        )
        lista_mora = []
        for c in cuotas_vencidas_qs:
            dias = max(0, (hoy - c.fecha_vencimiento).days)
            interes_penal = calcular_interes_penal(c.saldo_cuota, dias)
            lista_mora.append(
                {
                    "cuota": c,
                    "credito": c.credito,
                    "cliente": c.credito.solicitud.cliente,
                    "dias_atraso": dias,
                    "interes_penal": interes_penal,
                    "total_exigible": c.saldo_cuota + interes_penal,
                }
            )
        context["lista_mora"] = lista_mora
        context["total_creditos_mora"] = Credito.objects.filter(estado="EN_MORA").count()
        context["total_cuotas_vencidas"] = len(lista_mora)
        return context


class PagoDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.CAJERO]
    model = Pago
    template_name = "pagos/pago_confirm_delete.html"
    success_url = reverse_lazy("pagos:listado")


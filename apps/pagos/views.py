from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView

from creditos.models import Credito, Cuota
from usuarios.models import Usuario
from usuarios.views import RolRequiredMixin
from .forms import PagoForm
from .models import Pago
from .services import (
    aplicar_imputacion_cascada,
    calcular_interes_penal,
    ejecutar_control_mora,
    registrar_pago_cuota,
)


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
        q = self.request.GET.get("q", "").strip()
        forma = self.request.GET.get("forma_pago", "").strip()
        q_cobro = self.request.GET.get("q_cobro", "").strip()
        context["q"] = q
        context["q_cobro"] = q_cobro
        context["selected_forma"] = forma
        context["forma_filtro"] = forma
        context["formas_pago"] = Pago.FormaPago.choices
        context["total_recaudado"] = (
            Pago.objects.aggregate(s=Sum("monto"))["s"] or Decimal("0.00")
        )

        user = self.request.user
        if user.is_superuser or user.rol in [Usuario.Rol.ADMINISTRADOR, Usuario.Rol.CAJERO]:
            cobros_qs = (
                Credito.objects.filter(
                    estado__in=["VIGENTE", "EN_MORA"],
                    cuotas__estado__in=["PENDIENTE", "VENCIDA"],
                    cuotas__saldo_cuota__gt=0,
                )
                .select_related("solicitud__cliente")
                .annotate(
                    cuotas_impagas=Count(
                        "cuotas",
                        filter=Q(
                            cuotas__estado__in=["PENDIENTE", "VENCIDA"],
                            cuotas__saldo_cuota__gt=0,
                        ),
                    )
                )
                .distinct()
                .order_by("-id")
            )
            if q_cobro:
                cobros_qs = cobros_qs.filter(
                    Q(numero_credito__icontains=q_cobro)
                    | Q(solicitud__cliente__ci__icontains=q_cobro)
                    | Q(solicitud__cliente__nombres__icontains=q_cobro)
                    | Q(solicitud__cliente__apellidos__icontains=q_cobro)
                )
            context["creditos_por_cobrar"] = cobros_qs[:10]
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

    def _resolver_seleccion(self):
        cuota_id = self.request.GET.get("cuota") or self.request.POST.get("cuota")
        credito_id = self.request.GET.get("credito") or self.request.GET.get("credito_id")
        cuota_obj = None
        credito_obj = None
        if cuota_id:
            try:
                cuota_obj = (
                    Cuota.objects.select_related("credito", "credito__solicitud__cliente")
                    .filter(pk=int(cuota_id))
                    .first()
                )
                if cuota_obj:
                    credito_obj = cuota_obj.credito
            except (ValueError, TypeError):
                pass
        if not credito_obj and credito_id:
            try:
                credito_obj = (
                    Credito.objects.select_related("solicitud__cliente")
                    .filter(pk=int(credito_id))
                    .first()
                )
                if credito_obj and not cuota_obj:
                    cuota_obj = (
                        Cuota.objects.filter(
                            credito=credito_obj,
                            estado__in=["PENDIENTE", "VENCIDA"],
                            saldo_cuota__gt=0,
                        )
                        .order_by("numero_cuota")
                        .first()
                    )
            except (ValueError, TypeError):
                pass
        return credito_obj, cuota_obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        credito_obj, _ = self._resolver_seleccion()
        if credito_obj:
            kwargs["credito_id"] = credito_obj.pk
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        _, cuota_obj = self._resolver_seleccion()
        if cuota_obj:
            initial["cuota"] = cuota_obj.pk
            initial["monto"] = cuota_obj.saldo_cuota
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q_ci = self.request.GET.get("q_ci", "").strip()
        context["q_ci"] = q_ci
        context["titulo"] = "Cobro de Cuota en Ventanilla"
        context["boton_texto"] = "Procesar Pago y Emitir Recibo"

        credito_obj, cuota_obj = self._resolver_seleccion()
        context["credito_seleccionado"] = credito_obj
        context["cuota_seleccionada"] = cuota_obj
        if credito_obj:
            context["total_pendiente_credito"] = (
                credito_obj.cuotas.filter(
                    estado__in=["PENDIENTE", "VENCIDA"], saldo_cuota__gt=0
                ).aggregate(s=Sum("saldo_cuota"))["s"]
                or Decimal("0.00")
            )
        else:
            activos_qs = (
                Credito.objects.filter(
                    estado__in=["VIGENTE", "EN_MORA"],
                    cuotas__estado__in=["PENDIENTE", "VENCIDA"],
                    cuotas__saldo_cuota__gt=0,
                )
                .distinct()
                .select_related("solicitud__cliente")
                .order_by("-id")
            )
            if q_ci:
                activos_qs = activos_qs.filter(
                    Q(solicitud__cliente__ci__icontains=q_ci)
                    | Q(numero_credito__icontains=q_ci)
                    | Q(solicitud__cliente__nombres__icontains=q_ci)
                    | Q(solicitud__cliente__apellidos__icontains=q_ci)
                )
            context["creditos_encontrados"] = activos_qs[:10]
        return context

    def form_valid(self, form):
        cuota = form.cleaned_data["cuota"]
        monto = form.cleaned_data["monto"]
        forma_pago = form.cleaned_data["forma_pago"]
        try:
            pagos = aplicar_imputacion_cascada(
                credito_id=cuota.credito_id,
                monto_total=monto,
                forma_pago=forma_pago,
                usuario=self.request.user,
                cuota_inicial_id=cuota.pk,
            )
            primer_pago = pagos[0]
            if len(pagos) == 1:
                messages.success(
                    self.request,
                    f"Pago procesado exitosamente. Recibo Oficial #{primer_pago.numero_recibo} por Bs. {primer_pago.monto}.",
                )
            else:
                detalle_recibos = ", ".join(
                    f"#{p.numero_recibo} (Cuota #{p.cuota.numero_cuota}: Bs. {p.monto})"
                    for p in pagos
                )
                messages.success(
                    self.request,
                    f"Pago en cascada aplicado a {len(pagos)} cuotas. Recibos emitidos: {detalle_recibos}.",
                )
            return redirect("pagos:comprobante", pk=primer_pago.pk)
        except ValidationError as e:
            messages.error(self.request, e.message if hasattr(e, "message") else str(e))
            return self.form_invalid(form)


class ControlMoraView(RolRequiredMixin, TemplateView):
    """
    Panel de monitoreo y ejecución de control de mora.
    """

    roles_permitidos = [Usuario.Rol.CAJERO, Usuario.Rol.JEFE, Usuario.Rol.GERENTE]
    template_name = "pagos/control_mora.html"

    def post(self, request, *args, **kwargs):
        resultado = ejecutar_control_mora(usuario=request.user)
        messages.warning(
            request,
            f"Barrido de mora completado: {resultado['cuotas_marcadas_vencidas']} nuevas cuotas marcadas VENCIDAS y {resultado['creditos_pasados_a_mora']} créditos actualizados a EN_MORA.",
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
    roles_permitidos = [Usuario.Rol.ADMINISTRADOR]
    model = Pago
    template_name = "pagos/pago_confirm_delete.html"
    success_url = reverse_lazy("pagos:listado")


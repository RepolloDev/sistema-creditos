from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, FormView, ListView, TemplateView, View

from integraciones.models import TransaccionCoreBancario
from solicitudes.models import SolicitudCredito
from usuarios.models import Usuario
from usuarios.views import RolRequiredMixin
from .forms import AprobacionCreditoForm, RechazoCreditoForm
from .models import Credito
from .services import (
    aprobar_solicitud_credito,
    desembolsar_credito,
    firmar_contrato_credito,
    generar_reporte_cartera,
    rechazar_solicitud_credito,
)


class CreditoListView(RolRequiredMixin, ListView):
    """
    Lista general de créditos en cartera con filtros por estado y buscador.
    """

    roles_permitidos = [
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.CAJERO,
        Usuario.Rol.GERENTE,
    ]
    model = Credito
    template_name = "creditos/credito_list.html"
    context_object_name = "creditos"
    paginate_by = 15

    def get_queryset(self):
        qs = Credito.objects.select_related(
            "solicitud", "solicitud__cliente", "contrato"
        ).order_by("-id")
        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        if q:
            qs = qs.filter(
                Q(numero_credito__icontains=q)
                | Q(solicitud__cliente__ci__icontains=q)
                | Q(solicitud__cliente__nombres__icontains=q)
                | Q(solicitud__cliente__apellidos__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        context["q"] = q
        context["selected_estado"] = estado
        context["estado_filtro"] = estado
        context["estados"] = Credito.Estado.choices

        context["count_todos"] = Credito.objects.count()
        context["count_aprobado"] = Credito.objects.filter(estado=Credito.Estado.APROBADO).count()
        context["count_vigente"] = Credito.objects.filter(estado=Credito.Estado.VIGENTE).count()
        context["count_en_mora"] = Credito.objects.filter(estado=Credito.Estado.EN_MORA).count()
        context["count_cancelado"] = Credito.objects.filter(estado=Credito.Estado.CANCELADO).count()

        user = self.request.user
        if user.is_superuser or user.rol in [Usuario.Rol.ADMINISTRADOR, Usuario.Rol.JEFE]:
            context["solicitudes_evaluadas"] = (
                SolicitudCredito.objects.filter(estado=SolicitudCredito.Estado.EN_EVALUACION)
                .select_related("cliente", "evaluacion")
                .annotate(
                    num_garantias=Count("garantias"),
                    suma_garantias=Sum("garantias__valor"),
                )
                .order_by("-fecha_solicitud", "-id")
            )
        return context


class CreditoDetailView(RolRequiredMixin, DetailView):
    """
    Detalle del crédito, contrato, resumen de cuotas y estado de desembolso.
    """

    roles_permitidos = [
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.CAJERO,
        Usuario.Rol.GERENTE,
    ]
    model = Credito
    template_name = "creditos/credito_detail.html"
    context_object_name = "credito"

    def get_queryset(self):
        return Credito.objects.select_related(
            "solicitud", "solicitud__cliente", "solicitud__evaluacion", "contrato"
        ).prefetch_related("cuotas", "cuotas__pagos", "solicitud__garantias")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cuotas = self.object.cuotas.all().order_by("numero_cuota")
        context["cuotas"] = cuotas
        context["total_cuotas"] = cuotas.count()
        context["cuotas_pagadas"] = cuotas.filter(estado="PAGADA").count()
        context["cuotas_pendientes"] = cuotas.filter(estado="PENDIENTE").count()
        context["cuotas_vencidas"] = cuotas.filter(estado="VENCIDA").count()
        context["contrato"] = getattr(self.object, "contrato", None)
        context["transacciones_core"] = TransaccionCoreBancario.objects.filter(
            numero_credito=self.object.numero_credito
        ).order_by("-fecha_procesamiento")
        return context


class AprobarCreditoView(RolRequiredMixin, FormView):
    """
    CU07 / RF08: Aprobación formal por Jefe de Créditos.
    """

    roles_permitidos = [Usuario.Rol.JEFE]
    form_class = AprobacionCreditoForm
    template_name = "creditos/credito_aprobar.html"

    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(
            SolicitudCredito.objects.select_related("cliente", "evaluacion"),
            pk=self.kwargs["solicitud_id"],
        )
        if self.solicitud.estado != SolicitudCredito.Estado.EN_EVALUACION:
            messages.warning(
                request,
                f"La solicitud #{self.solicitud.pk} no puede aprobarse porque no está en estado En Evaluación.",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        if not hasattr(self.solicitud, "evaluacion") or self.solicitud.evaluacion.resultado != "FAVORABLE":
            messages.error(
                request,
                "No se puede aprobar una solicitud sin evaluación técnica previa o con dictamen desfavorable.",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["monto_aprobado"] = self.solicitud.monto_solicitado
        initial["plazo_meses"] = self.solicitud.plazo_meses
        initial["tasa_interes_anual"] = Decimal("14.00")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solicitud"] = self.solicitud
        context["evaluacion"] = getattr(self.solicitud, "evaluacion", None)
        return context

    def form_valid(self, form):
        try:
            credito = aprobar_solicitud_credito(
                solicitud_id=self.solicitud.pk,
                usuario_id=self.request.user.pk,
                tasa_anual=form.cleaned_data["tasa_interes_anual"],
                plazo_meses=form.cleaned_data["plazo_meses"],
                monto_aprobado=form.cleaned_data["monto_aprobado"],
            )
            messages.success(
                self.request,
                f"Crédito {credito.numero_credito} aprobado. Contrato y cronograma generados.",
            )
            return redirect("creditos:detalle", pk=credito.pk)
        except ValidationError as e:
            messages.error(self.request, e.message if hasattr(e, "message") else str(e))
            return self.form_invalid(form)


class RechazarCreditoView(RolRequiredMixin, FormView):
    """
    CU08 / RF09 / RN11: Rechazo justificado de solicitud de crédito (Actor: Jefe de Créditos).
    """

    roles_permitidos = [Usuario.Rol.JEFE]
    form_class = RechazoCreditoForm
    template_name = "creditos/credito_rechazar.html"

    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(
            SolicitudCredito.objects.select_related("cliente", "evaluacion"),
            pk=self.kwargs["solicitud_id"],
        )
        if self.solicitud.estado != SolicitudCredito.Estado.EN_EVALUACION:
            messages.warning(
                request,
                f"La solicitud #{self.solicitud.pk} no puede rechazarse sin previa revisión del analista.",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        if not hasattr(self.solicitud, "evaluacion"):
            messages.error(
                request,
                "La solicitud debe contar con evaluación previa del analista antes de ser resuelta por el Jefe.",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solicitud"] = self.solicitud
        return context

    def form_valid(self, form):
        try:
            rechazar_solicitud_credito(
                solicitud_id=self.solicitud.pk,
                motivo_rechazo=form.cleaned_data["motivo_rechazo"],
                usuario=self.request.user,
            )
            messages.warning(
                self.request,
                f"Solicitud #{self.solicitud.pk} marcada como RECHAZADA con motivo documentado.",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class ResolverSolicitudView(RolRequiredMixin, View):
    """
    Resolución unificada de solicitudes evaluadas para el Jefe de Créditos.
    Permite examinar antecedentes, garantías, buró y dictamen técnico para aprobar o rechazar.
    """

    roles_permitidos = [Usuario.Rol.JEFE]
    template_name = "creditos/credito_resolver.html"

    def get_solicitud(self, sol_id):
        if not sol_id:
            return None
        try:
            return (
                SolicitudCredito.objects.select_related("cliente", "evaluacion")
                .prefetch_related("garantias")
                .filter(pk=int(sol_id), estado=SolicitudCredito.Estado.EN_EVALUACION)
                .first()
            )
        except (ValueError, TypeError):
            return None

    def get(self, request, *args, **kwargs):
        sol_id = request.GET.get("solicitud_id")
        solicitud = self.get_solicitud(sol_id)
        if sol_id and not solicitud:
            messages.warning(
                request,
                "La solicitud indicada no existe, no está en estado En Evaluación o ya fue resuelta.",
            )
            return redirect("creditos:resolver")

        solicitudes_pendientes = (
            SolicitudCredito.objects.filter(estado=SolicitudCredito.Estado.EN_EVALUACION)
            .select_related("cliente", "evaluacion")
            .order_by("-fecha_solicitud")
        )

        form_aprobar = None
        form_rechazar = RechazoCreditoForm()
        buro = None
        cuota_estimada = None

        if solicitud:
            if hasattr(solicitud, "evaluacion") and solicitud.evaluacion.resultado == "FAVORABLE":
                form_aprobar = AprobacionCreditoForm(
                    initial={
                        "monto_aprobado": solicitud.monto_solicitado,
                        "plazo_meses": solicitud.plazo_meses,
                        "tasa_interes_anual": Decimal("14.00"),
                    }
                )
            cli = solicitud.cliente
            from evaluacion.services import consultar_historial_externo, estimar_cuota_francesa

            buro = consultar_historial_externo(ci=cli.ci, nombres=cli.nombres, apellidos=cli.apellidos)
            cuota_estimada = estimar_cuota_francesa(solicitud.monto_solicitado, solicitud.plazo_meses)

        context = {
            "solicitudes_pendientes": solicitudes_pendientes,
            "solicitud_obj": solicitud,
            "form_aprobar": form_aprobar,
            "form_rechazar": form_rechazar,
            "buro": buro,
            "cuota_estimada": cuota_estimada,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        sol_id = request.POST.get("solicitud_id")
        solicitud = self.get_solicitud(sol_id)
        if not solicitud:
            messages.error(request, "Debe seleccionar una solicitud válida en estado En Evaluación.")
            return redirect("creditos:resolver")

        action = request.POST.get("action")

        if action == "aprobar":
            form = AprobacionCreditoForm(request.POST)
            if form.is_valid():
                try:
                    credito = aprobar_solicitud_credito(
                        solicitud_id=solicitud.pk,
                        usuario_id=request.user.pk,
                        tasa_anual=form.cleaned_data["tasa_interes_anual"],
                        plazo_meses=form.cleaned_data["plazo_meses"],
                        monto_aprobado=form.cleaned_data["monto_aprobado"],
                    )
                    messages.success(
                        request,
                        f"Crédito {credito.numero_credito} aprobado exitosamente para {solicitud.cliente.nombres} {solicitud.cliente.apellidos}. Contrato y cronograma generados.",
                    )
                    return redirect("creditos:detalle", pk=credito.pk)
                except ValidationError as e:
                    messages.error(request, e.message if hasattr(e, "message") else str(e))
            else:
                for err in form.errors.values():
                    messages.error(request, err.as_text())
            return redirect(f"{reverse_lazy('creditos:resolver')}?solicitud_id={solicitud.pk}")

        elif action == "rechazar":
            form = RechazoCreditoForm(request.POST)
            if form.is_valid():
                try:
                    rechazar_solicitud_credito(
                        solicitud_id=solicitud.pk,
                        motivo_rechazo=form.cleaned_data["motivo_rechazo"],
                        usuario=request.user,
                    )
                    messages.warning(
                        request,
                        f"Solicitud #{solicitud.pk} rechazada correctamente con motivo documentado.",
                    )
                    return redirect("creditos:resolver")
                except ValidationError as e:
                    messages.error(request, str(e))
            else:
                for err in form.errors.values():
                    messages.error(request, err.as_text())
            return redirect(f"{reverse_lazy('creditos:resolver')}?solicitud_id={solicitud.pk}")

        messages.error(request, "Acción no reconocida.")
        return redirect("creditos:resolver")


class CronogramaView(RolRequiredMixin, DetailView):
    """
    CU10 / RF11: Tabla completa de amortización fija bajo el Sistema Francés.
    """

    roles_permitidos = [
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.CAJERO,
        Usuario.Rol.GERENTE,
    ]
    model = Credito
    template_name = "creditos/cronograma.html"
    context_object_name = "credito"

    def get_queryset(self):
        return Credito.objects.select_related("solicitud__cliente", "contrato").prefetch_related(
            "cuotas"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cuotas = self.object.cuotas.all().order_by("numero_cuota")
        context["cuotas"] = cuotas
        totales = cuotas.aggregate(
            total_capital=Sum("capital"),
            total_interes=Sum("interes"),
            total_cuotas=Sum("monto_cuota"),
            total_saldo=Sum("saldo_cuota"),
        )
        context["totales"] = totales
        return context


class ContratoImpresionView(RolRequiredMixin, DetailView):
    """
    CU09 / RF10: Emisión e impresión del contrato legal de crédito.
    """

    roles_permitidos = [
        Usuario.Rol.ADMINISTRADOR,
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.CAJERO,
        Usuario.Rol.GERENTE,
    ]
    model = Credito
    template_name = "creditos/contrato_impresion.html"
    context_object_name = "credito"

    def get_queryset(self):
        return Credito.objects.select_related(
            "solicitud__cliente", "solicitud__evaluacion", "contrato"
        ).prefetch_related("solicitud__garantias", "cuotas")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contrato = getattr(self.object, "contrato", None)
        context["contrato"] = contrato
        cuotas = self.object.cuotas.order_by("numero_cuota")
        context["primera_cuota"] = cuotas.first()
        context["ultima_cuota"] = cuotas.last()
        garantias = self.object.solicitud.garantias.all()
        context["garantias"] = garantias
        context["total_garantias"] = (
            sum(g.valor for g in garantias) if garantias else Decimal("0.00")
        )
        return context


class FirmarContratoView(RolRequiredMixin, View):
    """
    CU09 / RN05: Suscripción y firma del contrato previa al desembolso (Actor: Oficial / Jefe).
    """

    roles_permitidos = [Usuario.Rol.OFICIAL, Usuario.Rol.JEFE]

    def post(self, request, pk):
        credito = get_object_or_404(Credito, pk=pk)
        contrato = firmar_contrato_credito(credito.pk, usuario=request.user)
        messages.success(
            request,
            f"Contrato {contrato.numero_contrato} marcado como FIRMADO. El crédito está listo para desembolso.",
        )
        return redirect("creditos:detalle", pk=credito.pk)


class DesembolsarCreditoView(RolRequiredMixin, View):
    """
    CU11 / RF12: Ejecución y confirmación de desembolso con el Core Bancario (Actor: Oficial / Jefe).
    """

    roles_permitidos = [Usuario.Rol.OFICIAL, Usuario.Rol.JEFE]

    def post(self, request, pk):
        credito = get_object_or_404(Credito, pk=pk)
        cuenta_destino = request.POST.get("cuenta_destino", "")
        try:
            resultado = desembolsar_credito(
                credito_id=credito.pk,
                cuenta_destino=cuenta_destino,
                usuario=request.user,
            )
            messages.success(
                request,
                f"Desembolso ejecutado con éxito. Ref Core Bancario: {resultado['referencia']} ({resultado['codigo_autorizacion']}). Crédito en estado VIGENTE.",
            )
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect("creditos:detalle", pk=credito.pk)

    def get(self, request, pk):
        return redirect("creditos:detalle", pk=pk)


class ReportesView(RolRequiredMixin, TemplateView):
    """
    CU14 / RF15: Dashboard gerencial de reportes de cartera, recaudación y mora (Actor: Gerente).
    """

    roles_permitidos = [Usuario.Rol.GERENTE]
    template_name = "creditos/reportes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estado_filtro = self.request.GET.get("estado", "").strip()
        reporte = generar_reporte_cartera(estado_filtro=estado_filtro)
        context.update(reporte)
        context["reporte"] = reporte
        context["selected_estado"] = estado_filtro
        context["estado_filtro"] = estado_filtro
        context["estados"] = Credito.Estado.choices
        return context


class CreditoDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.ADMINISTRADOR]
    model = Credito
    template_name = "creditos/credito_confirm_delete.html"
    success_url = reverse_lazy("creditos:listado")


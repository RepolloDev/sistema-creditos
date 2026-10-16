from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, FormView, ListView, TemplateView, View

from integraciones.models import TransaccionCoreBancario
from solicitudes.models import SolicitudCredito
from usuarios.models import Auditoria
from .forms import AprobacionCreditoForm, RechazoCreditoForm
from .models import Credito
from .services import (
    aprobar_solicitud_credito,
    desembolsar_credito,
    firmar_contrato_credito,
    generar_reporte_cartera,
    rechazar_solicitud_credito,
)


class CreditoListView(LoginRequiredMixin, ListView):
    """
    Lista general de créditos en cartera con filtros por estado y buscador.
    """

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
        context["q"] = self.request.GET.get("q", "")
        context["selected_estado"] = self.request.GET.get("estado", "")
        context["estados"] = Credito.Estado.choices
        return context


class CreditoDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle del crédito, contrato, resumen de cuotas y estado de desembolso.
    """

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


class AprobarCreditoView(LoginRequiredMixin, FormView):
    """
    CU07 / RF08: Aprobación formal por Jefe de Créditos.
    """

    form_class = AprobacionCreditoForm
    template_name = "creditos/credito_aprobar.html"

    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(
            SolicitudCredito.objects.select_related("cliente", "evaluacion"),
            pk=self.kwargs["solicitud_id"],
        )
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
                f"Crédito {credito.numero_credito} aprobado. Contrato y cronograma generados (CU07, CU09, CU10).",
            )
            return redirect("creditos:detalle", pk=credito.pk)
        except ValidationError as e:
            messages.error(self.request, e.message if hasattr(e, "message") else str(e))
            return self.form_invalid(form)


class RechazarCreditoView(LoginRequiredMixin, FormView):
    """
    CU08 / RF09 / RN11: Rechazo justificado de solicitud de crédito.
    """

    form_class = RechazoCreditoForm
    template_name = "creditos/credito_rechazar.html"

    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(
            SolicitudCredito.objects.select_related("cliente"),
            pk=self.kwargs["solicitud_id"],
        )
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
                f"Solicitud #{self.solicitud.pk} marcada como RECHAZADA con motivo documentado (RN11).",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class CronogramaView(LoginRequiredMixin, DetailView):
    """
    CU10 / RF11: Tabla completa de amortización fija bajo el Sistema Francés.
    """

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


class FirmarContratoView(LoginRequiredMixin, View):
    """
    CU09 / RN05: Suscripción y firma del contrato previa al desembolso.
    """

    def post(self, request, pk):
        credito = get_object_or_404(Credito, pk=pk)
        contrato = firmar_contrato_credito(credito.pk, usuario=request.user)
        messages.success(
            request,
            f"Contrato {contrato.numero_contrato} marcado como FIRMADO. El crédito está listo para desembolso.",
        )
        return redirect("creditos:detalle", pk=credito.pk)


class DesembolsarCreditoView(LoginRequiredMixin, View):
    """
    CU11 / RF12: Ejecución y confirmación de desembolso con el Core Bancario.
    """

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


class ReportesView(LoginRequiredMixin, TemplateView):
    """
    CU14 / RF15: Dashboard gerencial de reportes de cartera, recaudación y mora.
    """

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


class CreditoDeleteView(LoginRequiredMixin, DeleteView):
    model = Credito
    template_name = "creditos/credito_confirm_delete.html"
    success_url = reverse_lazy("creditos:listado")


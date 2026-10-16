from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, View

from solicitudes.models import SolicitudCredito
from usuarios.models import Auditoria
from .forms import EvaluacionCreditoForm
from .models import EvaluacionCredito
from .services import (
    calcular_capacidad_pago,
    consultar_historial_externo,
    estimar_cuota_francesa,
    registrar_dictamen_evaluacion,
)


class EvaluacionListView(LoginRequiredMixin, ListView):
    """
    Lista de evaluaciones de crédito realizadas y bandeja de solicitudes pendientes de evaluar.
    """

    model = EvaluacionCredito
    template_name = "evaluacion/evaluacion_list.html"
    context_object_name = "evaluaciones"
    paginate_by = 15

    def get_queryset(self):
        qs = EvaluacionCredito.objects.select_related(
            "solicitud", "solicitud__cliente"
        ).order_by("-fecha_evaluacion", "-id")
        q = self.request.GET.get("q", "").strip()
        riesgo = self.request.GET.get("riesgo", "").strip()
        resultado = self.request.GET.get("resultado", "").strip()
        if q:
            qs = qs.filter(
                Q(solicitud__cliente__ci__icontains=q)
                | Q(solicitud__cliente__nombres__icontains=q)
                | Q(solicitud__cliente__apellidos__icontains=q)
                | Q(solicitud__id__icontains=q)
            )
        if riesgo:
            qs = qs.filter(nivel_riesgo=riesgo)
        if resultado:
            qs = qs.filter(resultado=resultado)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["selected_riesgo"] = self.request.GET.get("riesgo", "")
        context["selected_resultado"] = self.request.GET.get("resultado", "")
        context["niveles_riesgo"] = EvaluacionCredito.NivelRiesgo.choices
        context["resultados"] = EvaluacionCredito.Resultado.choices
        # Solicitudes pendientes de dictamen técnico
        context["solicitudes_sin_evaluar"] = (
            SolicitudCredito.objects.filter(evaluacion__isnull=True, estado="REGISTRADA")
            .select_related("cliente")
            .order_by("-fecha_solicitud")[:10]
        )
        return context


class EvaluacionDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle de dictamen técnico, scoring del buró y capacidad de pago (CU03 / CU04 / CU05).
    """

    model = EvaluacionCredito
    template_name = "evaluacion/evaluacion_detail.html"
    context_object_name = "evaluacion"

    def get_queryset(self):
        return EvaluacionCredito.objects.select_related(
            "solicitud", "solicitud__cliente"
        ).prefetch_related("solicitud__garantias")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sol = self.object.solicitud
        cli = sol.cliente
        context["buro"] = consultar_historial_externo(
            ci=cli.ci, nombres=cli.nombres, apellidos=cli.apellidos
        )
        calculo = calcular_capacidad_pago(self.object.ingresos, self.object.gastos)
        context["cuota_maxima"] = calculo["cuota_maxima_admisible"]
        context["cuota_estimada"] = estimar_cuota_francesa(
            sol.monto_solicitado, sol.plazo_meses
        )
        context["cumple_margen"] = context["cuota_estimada"] <= context["cuota_maxima"]
        context["viable"] = context["cumple_margen"]
        return context


class EvaluacionCreateView(LoginRequiredMixin, CreateView):
    """
    CU04 / CU05 / RF05 / RF06: Registro o actualización de evaluación técnica.
    """

    model = EvaluacionCredito
    form_class = EvaluacionCreditoForm
    template_name = "evaluacion/evaluacion_form.html"

    def get_solicitud_preseleccionada(self):
        sol_id = (
            self.request.GET.get("solicitud")
            or self.request.GET.get("solicitud_id")
            or self.request.POST.get("solicitud")
        )
        if sol_id:
            return SolicitudCredito.objects.select_related("cliente").filter(pk=sol_id).first()
        return None

    def get_initial(self):
        initial = super().get_initial()
        sol = self.get_solicitud_preseleccionada()
        if sol:
            initial["solicitud"] = sol.pk
            initial["ingresos"] = sol.cliente.ingresos_mensuales
            buro = consultar_historial_externo(
                ci=sol.cliente.ci, nombres=sol.cliente.nombres, apellidos=sol.cliente.apellidos
            )
            initial["nivel_riesgo"] = buro["nivel_riesgo"]
            gastos_sugeridos = (sol.cliente.ingresos_mensuales * Decimal("0.35")).quantize(
                Decimal("0.01")
            )
            initial["gastos"] = gastos_sugeridos
            initial["capacidad_pago"] = sol.cliente.ingresos_mensuales - gastos_sugeridos
            initial["observaciones"] = buro["observaciones"]
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sol = self.get_solicitud_preseleccionada()
        context["solicitud_obj"] = sol
        context["solicitud_preseleccionada"] = sol
        context["titulo"] = "Emitir Dictamen de Evaluación Crediticia (CU04 / CU05)"
        context["boton_texto"] = "Guardar Dictamen"
        if sol:
            context["buro"] = consultar_historial_externo(
                ci=sol.cliente.ci, nombres=sol.cliente.nombres, apellidos=sol.cliente.apellidos
            )
            context["cuota_estimada"] = estimar_cuota_francesa(
                sol.monto_solicitado, sol.plazo_meses
            )
        return context

    def post(self, request, *args, **kwargs):
        sol_id = request.POST.get("solicitud")
        ingresos = Decimal(request.POST.get("ingresos") or "0.00")
        gastos = Decimal(request.POST.get("gastos") or "0.00")
        nivel_riesgo = request.POST.get("nivel_riesgo", "MEDIO")
        resultado = request.POST.get("resultado", "FAVORABLE")
        observaciones = request.POST.get("observaciones", "")

        if not sol_id:
            messages.error(request, "Debe seleccionar una solicitud válida para evaluar.")
            return redirect("evaluacion:crear")

        evaluacion = registrar_dictamen_evaluacion(
            solicitud_id=int(sol_id),
            ingresos=ingresos,
            gastos=gastos,
            nivel_riesgo=nivel_riesgo,
            resultado=resultado,
            observaciones=observaciones,
            usuario=request.user,
        )
        messages.success(
            request,
            f"Dictamen técnico ({evaluacion.get_resultado_display()}) registrado para Solicitud #{sol_id}.",
        )
        return redirect("evaluacion:detalle", pk=evaluacion.pk)


class ConsultarRiesgoExternoView(LoginRequiredMixin, View):
    """
    CU03 / RF04: Consulta interactiva al buró externo para una evaluación o solicitud.
    """

    def get(self, request, pk):
        evaluacion = get_object_or_404(EvaluacionCredito, pk=pk)
        cli = evaluacion.solicitud.cliente
        buro = consultar_historial_externo(
            ci=cli.ci, nombres=cli.nombres, apellidos=cli.apellidos
        )
        messages.info(
            request,
            f"Buró Externo verificado para CI {cli.ci}: Score {buro['score']} ({buro['nivel_riesgo']}) - {buro['observaciones']}",
        )
        return redirect("evaluacion:detalle", pk=evaluacion.pk)


class EvaluacionDeleteView(LoginRequiredMixin, DeleteView):
    model = EvaluacionCredito
    template_name = "evaluacion/evaluacion_confirm_delete.html"
    success_url = reverse_lazy("evaluacion:listado")


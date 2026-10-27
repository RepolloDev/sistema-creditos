from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, View

from solicitudes.models import SolicitudCredito
from usuarios.models import Usuario
from usuarios.views import RolRequiredMixin
from .forms import EvaluacionCreditoForm
from .models import EvaluacionCredito
from .services import (
    calcular_capacidad_pago,
    consultar_historial_externo,
    estimar_cuota_francesa,
    registrar_dictamen_evaluacion,
)


class EvaluacionListView(RolRequiredMixin, ListView):
    """
    Lista de evaluaciones de crédito realizadas y bandeja de solicitudes pendientes de evaluar.
    """

    roles_permitidos = [Usuario.Rol.ANALISTA, Usuario.Rol.JEFE, Usuario.Rol.GERENTE]
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
        q = self.request.GET.get("q", "").strip()
        riesgo = self.request.GET.get("riesgo", "").strip()
        resultado = self.request.GET.get("resultado", "").strip()

        context["q"] = q
        context["selected_riesgo"] = riesgo
        context["riesgo_filtro"] = riesgo
        context["selected_resultado"] = resultado
        context["resultado_filtro"] = resultado
        context["niveles_riesgo"] = EvaluacionCredito.NivelRiesgo.choices
        context["resultados"] = EvaluacionCredito.Resultado.choices
        return context


class EvaluacionDetailView(RolRequiredMixin, DetailView):
    """
    Detalle de dictamen técnico, scoring del buró y capacidad de pago.
    """

    roles_permitidos = [Usuario.Rol.ANALISTA, Usuario.Rol.JEFE, Usuario.Rol.GERENTE]
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


class EvaluacionCreateView(RolRequiredMixin, CreateView):
    """
    Registro o actualización de evaluación técnica (Actor: Analista).
    """

    roles_permitidos = [Usuario.Rol.ANALISTA]
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
            try:
                return (
                    SolicitudCredito.objects.select_related("cliente")
                    .prefetch_related("garantias")
                    .filter(
                        pk=int(sol_id),
                        estado=SolicitudCredito.Estado.REGISTRADA,
                        evaluacion__isnull=True,
                    )
                    .first()
                )
            except (ValueError, TypeError):
                return None
        return None

    def get(self, request, *args, **kwargs):
        sol_id = request.GET.get("solicitud") or request.GET.get("solicitud_id")
        if sol_id:
            sol = self.get_solicitud_preseleccionada()
            if not sol:
                messages.warning(
                    request,
                    "La solicitud no existe, ya fue evaluada o no se encuentra en estado REGISTRADA.",
                )
                return redirect("evaluacion:crear")
        return super().get(request, *args, **kwargs)

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
            initial["resultado"] = (
                EvaluacionCredito.Resultado.FAVORABLE
                if buro.get("es_favorable", True)
                else EvaluacionCredito.Resultado.DESFAVORABLE
            )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sol = self.get_solicitud_preseleccionada()
        context["solicitud_obj"] = sol
        context["solicitud_preseleccionada"] = sol
        context["titulo"] = "Emitir Dictamen de Evaluación Crediticia"
        context["boton_texto"] = "Guardar Dictamen"
        if sol:
            context["buro"] = consultar_historial_externo(
                ci=sol.cliente.ci, nombres=sol.cliente.nombres, apellidos=sol.cliente.apellidos
            )
            context["cuota_estimada"] = estimar_cuota_francesa(
                sol.monto_solicitado, sol.plazo_meses
            )
        else:
            q_pend = self.request.GET.get("q_pend", "").strip()
            pend_qs = (
                SolicitudCredito.objects.filter(
                    estado=SolicitudCredito.Estado.REGISTRADA,
                    evaluacion__isnull=True,
                )
                .select_related("cliente")
                .annotate(
                    num_garantias=Count("garantias"),
                    suma_garantias=Sum("garantias__valor"),
                )
                .order_by("-fecha_solicitud", "-id")
            )
            if q_pend:
                pend_qs = pend_qs.filter(
                    Q(cliente__ci__icontains=q_pend)
                    | Q(cliente__nombres__icontains=q_pend)
                    | Q(cliente__apellidos__icontains=q_pend)
                    | Q(id__icontains=q_pend)
                )
            context["solicitudes_pendientes"] = pend_qs
            context["q_pend"] = q_pend
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

        solicitud = (
            SolicitudCredito.objects.filter(
                pk=int(sol_id),
                estado=SolicitudCredito.Estado.REGISTRADA,
                evaluacion__isnull=True,
            )
            .first()
        )
        if not solicitud:
            messages.error(
                request,
                "Solo se pueden evaluar solicitudes en estado REGISTRADA que no tengan evaluación previa.",
            )
            return redirect("evaluacion:crear")

        try:
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
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, "messages") else str(e)
            messages.error(request, msg)
            return redirect(f"{reverse_lazy('evaluacion:crear')}?solicitud_id={sol_id}")


class ConsultarRiesgoExternoView(RolRequiredMixin, View):
    """
    Consulta interactiva al buró externo para una evaluación (Actor: Analista).
    """

    roles_permitidos = [Usuario.Rol.ANALISTA]

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


class EvaluacionDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.ADMINISTRADOR]
    model = EvaluacionCredito
    template_name = "evaluacion/evaluacion_confirm_delete.html"
    success_url = reverse_lazy("evaluacion:listado")


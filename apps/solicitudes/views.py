from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from usuarios.models import Auditoria, Usuario
from usuarios.views import RolRequiredMixin
from .forms import GarantiaForm, SolicitudCreditoForm
from .models import Garantia, SolicitudCredito


class SolicitudListView(RolRequiredMixin, ListView):
    """
    CU02: Bandeja general de solicitudes de financiamiento.
    """

    roles_permitidos = [
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.GERENTE,
    ]
    model = SolicitudCredito
    template_name = "solicitudes/solicitud_list.html"
    context_object_name = "solicitudes"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            SolicitudCredito.objects.select_related("cliente", "evaluacion", "credito")
            .prefetch_related("garantias")
            .order_by("-fecha_solicitud", "-id")
        )
        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        if q:
            qs = qs.filter(
                Q(cliente__ci__icontains=q)
                | Q(cliente__nombres__icontains=q)
                | Q(cliente__apellidos__icontains=q)
                | Q(destino__icontains=q)
                | Q(id__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["selected_estado"] = self.request.GET.get("estado", "")
        context["estados"] = SolicitudCredito.Estado.choices
        return context


class SolicitudCreateView(RolRequiredMixin, CreateView):
    """
    CU02 / RF03: Radicar una nueva solicitud de crédito en estado REGISTRADA (Actor: Oficial).
    """

    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = SolicitudCredito
    form_class = SolicitudCreditoForm
    template_name = "solicitudes/solicitud_form.html"

    def get_initial(self):
        initial = super().get_initial()
        cliente_id = self.request.GET.get("cliente") or self.request.GET.get("cliente_id")
        if cliente_id:
            initial["cliente"] = cliente_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Registrar Nueva Solicitud de Crédito"
        context["boton_texto"] = "Radicar Solicitud"
        return context

    def get_success_url(self):
        return reverse_lazy("solicitudes:detalle", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        form.instance.estado = SolicitudCredito.Estado.REGISTRADA
        response = super().form_valid(form)
        Auditoria.objects.create(
            usuario=self.request.user,
            operacion="REGISTRAR_SOLICITUD",
            entidad="SOLICITUD_CREDITO",
            id_entidad=self.object.pk,
            resultado=Auditoria.Resultado.EXITOSO,
        )
        messages.success(
            self.request,
            f"Solicitud #{self.object.pk} registrada en estado REGISTRADA.",
        )
        return response


class SolicitudUpdateView(RolRequiredMixin, UpdateView):
    """
    Edición de una solicitud de crédito.
    Reglas:
    - No editable si la solicitud fue aprobada o tiene un crédito vinculado.
    - Al editar, pasa a estado REGISTRADA para re-evaluación del analista de riesgos.
    - Se reinicia cualquier dictamen de evaluación previo y motivo de rechazo.
    """

    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = SolicitudCredito
    form_class = SolicitudCreditoForm
    template_name = "solicitudes/solicitud_form.html"

    def dispatch(self, request, *args, **kwargs):
        solicitud = self.get_object()
        if hasattr(solicitud, "credito") or solicitud.estado == SolicitudCredito.Estado.APROBADA:
            messages.error(
                request,
                f"La solicitud #{solicitud.pk} ya fue aprobada / tiene un crédito generado y no puede ser modificada.",
            )
            return redirect("solicitudes:detalle", pk=solicitud.pk)
        if solicitud.estado == SolicitudCredito.Estado.EN_EVALUACION:
            messages.error(
                request,
                f"La solicitud #{solicitud.pk} está En Evaluación por el comité y no puede modificarse.",
            )
            return redirect("solicitudes:detalle", pk=solicitud.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar Solicitud #{self.object.pk}"
        context["boton_texto"] = "Guardar Cambios y Reenviar a Evaluación"
        return context

    def get_success_url(self):
        return reverse_lazy("solicitudes:detalle", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        with transaction.atomic():
            solicitud = form.save(commit=False)
            solicitud.estado = SolicitudCredito.Estado.REGISTRADA
            solicitud.motivo_rechazo = None
            solicitud.save()

            # Si existía una evaluación técnica previa, eliminarla para obligar a nueva evaluación
            if hasattr(solicitud, "evaluacion"):
                solicitud.evaluacion.delete()

            Auditoria.objects.create(
                usuario=self.request.user,
                operacion="EDITAR_SOLICITUD",
                entidad="SOLICITUD_CREDITO",
                id_entidad=solicitud.pk,
                resultado=Auditoria.Resultado.EXITOSO,
            )

        messages.success(
            self.request,
            f"Solicitud #{solicitud.pk} actualizada correctamente. Estado restablecido a REGISTRADA para su re-evaluación por Riesgos.",
        )
        return redirect(self.get_success_url())


class SolicitudDetailView(RolRequiredMixin, DetailView):
    """
    Expediente completo de la solicitud, garantías vinculadas y dictamen.
    """

    roles_permitidos = [
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.GERENTE,
    ]
    model = SolicitudCredito
    template_name = "solicitudes/solicitud_detail.html"
    context_object_name = "solicitud"

    def get_queryset(self):
        return SolicitudCredito.objects.select_related(
            "cliente", "evaluacion", "credito", "credito__contrato"
        ).prefetch_related("garantias")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        garantias = self.object.garantias.all()
        context["garantias"] = garantias
        context["total_garantias"] = (
            garantias.aggregate(total=Sum("valor"))["total"] or 0
        )
        context["evaluacion"] = getattr(self.object, "evaluacion", None)
        context["credito"] = getattr(self.object, "credito", None)
        return context


class GarantiaCreateView(RolRequiredMixin, CreateView):
    """
    CU06 / RF07 / RN13: Registrar garantía y asociarla a la solicitud (Actor: Oficial).
    """

    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = Garantia
    form_class = GarantiaForm
    template_name = "solicitudes/garantia_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(SolicitudCredito, pk=self.kwargs["pk"])
        if hasattr(self.solicitud, "credito") or self.solicitud.estado in [
            SolicitudCredito.Estado.APROBADA,
            SolicitudCredito.Estado.EN_EVALUACION,
        ]:
            messages.error(
                request,
                f"No se pueden agregar garantías a una solicitud en estado {self.solicitud.get_estado_display()}.",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solicitud"] = self.solicitud
        context["titulo"] = f"Registrar Garantía (Solicitud #{self.solicitud.id})"
        context["boton_texto"] = "Guardar Garantía"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.solicitud = self.solicitud
            form.instance.estado = Garantia.Estado.REGISTRADA
            response = super().form_valid(form)

            # Si la solicitud estaba RECHAZADA, pasa a REGISTRADA y limpia evaluación
            if self.solicitud.estado == SolicitudCredito.Estado.RECHAZADA:
                self.solicitud.estado = SolicitudCredito.Estado.REGISTRADA
                self.solicitud.motivo_rechazo = None
                self.solicitud.save(update_fields=["estado", "motivo_rechazo"])

            if hasattr(self.solicitud, "evaluacion"):
                self.solicitud.evaluacion.delete()

            Auditoria.objects.create(
                usuario=self.request.user,
                operacion="REGISTRAR_GARANTIA",
                entidad="GARANTIA",
                id_entidad=self.object.pk,
                resultado=Auditoria.Resultado.EXITOSO,
            )
        messages.success(
            self.request,
            f"Garantía ({self.object.get_tipo_display()}) vinculada a la Solicitud #{self.solicitud.pk}.",
        )
        return response

    def get_success_url(self):
        return reverse_lazy("solicitudes:detalle", kwargs={"pk": self.solicitud.pk})


class GarantiaUpdateView(RolRequiredMixin, UpdateView):
    """
    Edición de una garantía vinculada.
    Solo permitida si la solicitud está en estado REGISTRADA o RECHAZADA.
    Al guardar, si la solicitud estaba rechazada, pasa a REGISTRADA y reinicia dictamen previo.
    """

    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = Garantia
    form_class = GarantiaForm
    template_name = "solicitudes/garantia_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.garantia = self.get_object()
        self.solicitud = self.garantia.solicitud
        if hasattr(self.solicitud, "credito") or self.solicitud.estado not in [
            SolicitudCredito.Estado.REGISTRADA,
            SolicitudCredito.Estado.RECHAZADA,
        ]:
            messages.error(
                request,
                f"Las garantías de la solicitud #{self.solicitud.pk} no pueden editarse en su estado actual ({self.solicitud.get_estado_display()}).",
            )
            return redirect("solicitudes:detalle", pk=self.solicitud.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solicitud"] = self.solicitud
        context["titulo"] = f"Editar Garantía (Solicitud #{self.solicitud.id})"
        context["boton_texto"] = "Guardar Cambios de Garantía"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            if self.solicitud.estado == SolicitudCredito.Estado.RECHAZADA:
                self.solicitud.estado = SolicitudCredito.Estado.REGISTRADA
                self.solicitud.motivo_rechazo = None
                self.solicitud.save(update_fields=["estado", "motivo_rechazo"])

            if hasattr(self.solicitud, "evaluacion"):
                self.solicitud.evaluacion.delete()

            Auditoria.objects.create(
                usuario=self.request.user,
                operacion="EDITAR_GARANTIA",
                entidad="GARANTIA",
                id_entidad=self.object.pk,
                resultado=Auditoria.Resultado.EXITOSO,
            )
        messages.success(
            self.request,
            f"Garantía #{self.object.pk} actualizada correctamente.",
        )
        return response

    def get_success_url(self):
        return reverse_lazy("solicitudes:detalle", kwargs={"pk": self.solicitud.pk})


class SolicitudDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.ADMINISTRADOR]
    model = SolicitudCredito
    template_name = "solicitudes/solicitud_confirm_delete.html"
    success_url = reverse_lazy("solicitudes:listado")


class GarantiaDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.ADMINISTRADOR, Usuario.Rol.OFICIAL]
    model = Garantia

    def dispatch(self, request, *args, **kwargs):
        garantia = self.get_object()
        sol = garantia.solicitud
        if hasattr(sol, "credito") or sol.estado not in [
            SolicitudCredito.Estado.REGISTRADA,
            SolicitudCredito.Estado.RECHAZADA,
        ]:
            messages.error(
                request,
                f"No se pueden eliminar garantías de una solicitud en estado {sol.get_estado_display()}.",
            )
            return redirect("solicitudes:detalle", pk=sol.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("solicitudes:detalle", kwargs={"pk": self.object.solicitud_id})


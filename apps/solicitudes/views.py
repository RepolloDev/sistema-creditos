from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView

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
        context["titulo"] = "Registrar Nueva Solicitud de Crédito (CU02)"
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
            f"Solicitud #{self.object.pk} registrada en estado REGISTRADA (RN02).",
        )
        return response


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
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["solicitud"] = self.solicitud
        return context

    def form_valid(self, form):
        form.instance.solicitud = self.solicitud
        form.instance.estado = Garantia.Estado.REGISTRADA
        response = super().form_valid(form)
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


class SolicitudDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.OFICIAL, Usuario.Rol.JEFE]
    model = SolicitudCredito
    template_name = "solicitudes/solicitud_confirm_delete.html"
    success_url = reverse_lazy("solicitudes:listado")


class GarantiaDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = Garantia

    def get_success_url(self):
        return reverse_lazy("solicitudes:detalle", kwargs={"pk": self.object.solicitud_id})


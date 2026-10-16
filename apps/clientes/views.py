from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from usuarios.models import Auditoria, Usuario
from usuarios.views import RolRequiredMixin
from .forms import ClienteForm
from .models import Cliente
from .services import obtener_perfil_financiero


class ClienteListView(RolRequiredMixin, ListView):
    roles_permitidos = [
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.CAJERO,
        Usuario.Rol.GERENTE,
    ]
    model = Cliente
    template_name = "clientes/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 15

    def get_queryset(self):
        qs = Cliente.objects.all().order_by("-id")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(ci__icontains=q)
                | Q(nombres__icontains=q)
                | Q(apellidos__icontains=q)
                | Q(telefono__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["total_registrados"] = Cliente.objects.count()
        context["total_clientes"] = context["total_registrados"]
        return context


class ClienteCreateView(RolRequiredMixin, CreateView):
    """CU01 / RF01: Registrar cliente (Actor: Oficial de Crédito)."""

    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/cliente_form.html"
    success_url = reverse_lazy("clientes:listado")

    def form_valid(self, form):
        response = super().form_valid(form)
        Auditoria.objects.create(
            usuario=self.request.user,
            operacion="REGISTRAR_CLIENTE",
            entidad="CLIENTE",
            id_entidad=self.object.pk,
            resultado=Auditoria.Resultado.EXITOSO,
        )
        messages.success(
            self.request,
            f"Cliente '{self.object.nombres} {self.object.apellidos}' (CI: {self.object.ci}) registrado exitosamente.",
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Registrar Nuevo Cliente (CU01)"
        context["boton_texto"] = "Guardar Cliente"
        return context


class ClienteDetailView(RolRequiredMixin, DetailView):
    roles_permitidos = [
        Usuario.Rol.OFICIAL,
        Usuario.Rol.ANALISTA,
        Usuario.Rol.JEFE,
        Usuario.Rol.CAJERO,
        Usuario.Rol.GERENTE,
    ]
    model = Cliente
    template_name = "clientes/cliente_detail.html"
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["perfil"] = obtener_perfil_financiero(self.object.pk)
        context["solicitudes"] = (
            self.object.solicitudes.select_related("evaluacion", "credito")
            .prefetch_related("garantias")
            .order_by("-fecha_solicitud")
        )
        return context


class ClienteUpdateView(RolRequiredMixin, UpdateView):
    """RF02: Actualizar cliente (Actor: Oficial de Crédito)."""

    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/cliente_form.html"

    def get_success_url(self):
        return reverse_lazy("clientes:detalle", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        Auditoria.objects.create(
            usuario=self.request.user,
            operacion="ACTUALIZAR_CLIENTE",
            entidad="CLIENTE",
            id_entidad=self.object.pk,
            resultado=Auditoria.Resultado.EXITOSO,
        )
        messages.success(
            self.request,
            f"Datos del cliente '{self.object.ci}' actualizados correctamente (RF02).",
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Actualizar Cliente: {self.object.ci} (RF02)"
        context["boton_texto"] = "Actualizar Datos"
        return context


class ClienteDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = [Usuario.Rol.OFICIAL]
    model = Cliente
    template_name = "clientes/cliente_confirm_delete.html"
    success_url = reverse_lazy("clientes:listado")


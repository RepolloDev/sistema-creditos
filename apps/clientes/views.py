from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from usuarios.models import Auditoria
from .forms import ClienteForm
from .models import Cliente
from .services import obtener_perfil_financiero


class ClienteListView(LoginRequiredMixin, ListView):
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


class ClienteCreateView(LoginRequiredMixin, CreateView):
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


class ClienteDetailView(LoginRequiredMixin, DetailView):
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


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
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


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = "clientes/cliente_confirm_delete.html"
    success_url = reverse_lazy("clientes:listado")


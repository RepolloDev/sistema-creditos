from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import LoginForm, UsuarioCreateForm, UsuarioUpdateForm
from .models import Usuario


class SoloAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restringe el acceso exclusivamente a usuarios con rol ADMINISTRADOR o superusuarios.
    """

    def test_func(self):
        usuario = self.request.user
        return usuario.is_authenticated and (
            usuario.rol == Usuario.Rol.ADMINISTRADOR or usuario.is_superuser
        )

    def handle_no_permission(self):
        messages.error(
            self.request, "Acceso restringido. Solo administradores pueden gestionar usuarios."
        )
        return redirect("usuarios:dashboard")


class UsuarioLoginView(LoginView):
    """
    Vista de autenticación / inicio de sesión.
    """

    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class UsuarioLogoutView(LogoutView):
    """
    Vista de cierre de sesión.
    """

    next_page = "usuarios:login"


class UsuarioListView(SoloAdminMixin, ListView):
    """
    CU15: Listar usuarios con filtros por rol y búsqueda.
    """

    model = Usuario
    template_name = "usuarios/usuario_list.html"
    context_object_name = "usuarios"
    paginate_by = 15

    def get_queryset(self):
        qs = Usuario.objects.all().order_by("-id")
        q = self.request.GET.get("q")
        rol = self.request.GET.get("rol")
        if q:
            qs = qs.filter(login__icontains=q) | qs.filter(nombre_completo__icontains=q)
        if rol:
            qs = qs.filter(rol=rol)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = Usuario.Rol.choices
        context["selected_rol"] = self.request.GET.get("rol", "")
        context["q"] = self.request.GET.get("q", "")
        return context


class UsuarioCreateView(SoloAdminMixin, CreateView):
    """
    CU15: Crear nuevo usuario con rol asignado y clave encriptada.
    """

    model = Usuario
    form_class = UsuarioCreateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:usuario_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Usuario '{self.object.login}' creado exitosamente.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Crear Nuevo Usuario"
        context["boton_texto"] = "Guardar Usuario"
        return context


class UsuarioUpdateView(SoloAdminMixin, UpdateView):
    """
    CU15: Modificar datos y rol de un usuario existente.
    """

    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:usuario_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Usuario '{self.object.login}' actualizado correctamente.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar Usuario: {self.object.login}"
        context["boton_texto"] = "Actualizar Cambios"
        return context


class UsuarioDeleteView(SoloAdminMixin, DeleteView):
    """
    CU15: Eliminar cuenta de usuario.
    """

    model = Usuario
    template_name = "usuarios/usuario_confirm_delete.html"
    success_url = reverse_lazy("usuarios:usuario_list")

    def delete(self, request, *args, **kwargs):
        usuario = self.get_object()
        if usuario == request.user:
            messages.error(request, "No puedes eliminar tu propia cuenta en sesión activa.")
            return redirect("usuarios:usuario_list")
        messages.success(request, f"Usuario '{usuario.login}' eliminado satisfactoriamente.")
        return super().delete(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista base del Dashboard Operativo (en blanco para implementación de equipo).
    """

    template_name = "dashboard.html"


@login_required
def dashboard_redirect_view(request):
    """
    Redirige al dashboard central general.
    """
    return redirect("home")

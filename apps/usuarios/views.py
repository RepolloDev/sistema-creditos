"""
================================================================================
MÓDULO: USUARIOS (apps/usuarios/views.py)
================================================================================
¿QUÉ HACE ESTE ARCHIVO?
Es el recepcionista y coordinador de la aplicación web.
Cuando un usuario hace clic en un enlace o envía un formulario con datos,
Django busca aquí la función o clase correspondiente para responder:
- Si alguien quiere entrar, procesa el login.
- Si alguien sale, cierra la sesión.
- Si un Administrador entra a gestionar usuarios, lista, crea, edita o elimina
  empleados, verificando siempre que nadie sin autorización pueda entrar.
================================================================================
"""

# ------------------------------------------------------------------------------
# IMPORTACIONES (Herramientas de Django y de nuestro proyecto)
# ------------------------------------------------------------------------------

# messages: Permite mostrar globitos o avisos verdes de éxito o rojos de error
# en la parte superior de la página web (ej: "Usuario guardado correctamente").
from django.contrib import messages

# login_required: Decorador que se pone encima de una función para exigir que
# la persona esté conectada antes de ver la página; si no, la manda al login.
from django.contrib.auth.decorators import login_required

# LoginRequiredMixin: Hace lo mismo que login_required pero para clases (CBV).
# UserPassesTestMixin: Permite escribir una pequeña prueba (función) para decidir
# si el usuario actual tiene o no permiso de ver esta pantalla.
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# LoginView y LogoutView: Pantallas ya programadas por Django para iniciar y cerrar sesión.
from django.contrib.auth.views import LoginView, LogoutView

# redirect: Para enviar al usuario a otra dirección web después de completar una acción.
from django.shortcuts import redirect

# reverse_lazy: Permite calcular la dirección URL hacia donde iremos cuando termine
# de guardarse un formulario (se evalúa solo cuando es necesario).
from django.urls import reverse_lazy

# Vistas genéricas de Django (CBV - Class Based Views):
# En vez de escribir 50 líneas de código para listar o crear cosas en una base de datos,
# Django ya tiene estas plantillas listas:
# - ListView: Para mostrar una tabla con listas de registros y paginación.
# - CreateView: Para mostrar un formulario y guardar un nuevo registro.
# - UpdateView: Para mostrar un formulario con datos ya existentes y editarlos.
# - DeleteView: Para mostrar una pantalla de "¿Está seguro?" y borrar un registro.
# - TemplateView: Para mostrar una página HTML sencilla sin lógica compleja.
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

# Importamos los formularios que creamos en forms.py y el modelo Usuario de models.py
from .forms import LoginForm, UsuarioCreateForm, UsuarioUpdateForm
from .models import Usuario


# ------------------------------------------------------------------------------
# REGLA DE SEGURIDAD (Mixin para permitir paso solo a Administradores)
# ------------------------------------------------------------------------------
class SoloAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Este es el guardia de seguridad interno.
    Cualquier pantalla que tenga este Mixin solo podrá ser vista si:
    1. La persona ha iniciado sesión.
    2. Su rol es exactamente 'ADMINISTRADOR' o es un superusuario.
    Si no cumple esto, se le expulsa de inmediato.
    """

    def test_func(self):
        # Esta función debe responder True (pasa) o False (bloqueado)
        usuario = self.request.user
        return usuario.is_authenticated and (
            usuario.rol == Usuario.Rol.ADMINISTRADOR or usuario.is_superuser
        )

    def handle_no_permission(self):
        # Qué hacer cuando la persona NO tiene permiso:
        # Mostramos un mensaje de error y la mandamos a la página de inicio.
        messages.error(
            self.request, "Acceso restringido. Solo administradores pueden gestionar usuarios."
        )
        return redirect("usuarios:dashboard")


# ------------------------------------------------------------------------------
# INICIO Y CIERRE DE SESIÓN
# ------------------------------------------------------------------------------
class UsuarioLoginView(LoginView):
    """
    Pantalla de inicio de sesión (/usuarios/login/).
    Usa nuestra plantilla 'usuarios/login.html' y nuestro formulario 'LoginForm'.
    """

    template_name = "usuarios/login.html"
    authentication_form = LoginForm

    # Si alguien que ya está conectado intenta entrar a /login/, lo redirige
    # automáticamente a su pantalla de trabajo para no pedirle clave otra vez.
    redirect_authenticated_user = True


class UsuarioLogoutView(LogoutView):
    """
    Cierra la sesión del empleado (/usuarios/logout/) y lo manda a la pantalla de login.
    """

    next_page = "usuarios:login"


# ------------------------------------------------------------------------------
# ADMINISTRACIÓN DE USUARIOS (CRUD - Solo Administrador)
# ------------------------------------------------------------------------------


class UsuarioListView(SoloAdminMixin, ListView):
    """
    CU15: Mostrar la lista de empleados del banco (/usuarios/).
    Permite buscar por texto (nombre o login) y filtrar por rol.
    """

    model = Usuario  # La tabla de donde saca la información
    template_name = "usuarios/usuario_list.html"  # La plantilla HTML que dibuja la tabla
    context_object_name = "usuarios"  # La variable que usaremos en el HTML para el bucle
    paginate_by = 15  # Muestra de 15 en 15 empleados por página

    def get_queryset(self):
        """
        Filtra qué usuarios mostrar según lo que el administrador haya escrito
        en la barra de búsqueda o seleccionado en el menú de roles.
        """
        qs = Usuario.objects.all().order_by("-id")  # Los más nuevos primero
        q = self.request.GET.get("q")  # Texto escrito en el buscador
        rol = self.request.GET.get("rol")  # Rol seleccionado en el filtro desplegable

        if q:
            # Busca si el texto coincide con el login O con el nombre completo
            qs = qs.filter(login__icontains=q) | qs.filter(nombre_completo__icontains=q)
        if rol:
            qs = qs.filter(rol=rol)
        return qs

    def get_context_data(self, **kwargs):
        """
        Pasa datos extra a la plantilla HTML (para llenar el selector de roles
        y recordar qué texto buscó el usuario).
        """
        context = super().get_context_data(**kwargs)
        context["roles"] = Usuario.Rol.choices
        context["selected_rol"] = self.request.GET.get("rol", "")
        context["q"] = self.request.GET.get("q", "")
        return context


class UsuarioCreateView(SoloAdminMixin, CreateView):
    """
    CU15: Crear un nuevo empleado en el sistema (/usuarios/nuevo/).
    """

    model = Usuario
    form_class = UsuarioCreateForm  # Usa el formulario que pide y valida dos veces la clave
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:usuario_list")  # Al guardar, regresa a la lista

    def form_valid(self, form):
        # Si todos los campos son válidos y la clave es correcta, se guarda el usuario
        response = super().form_valid(form)
        messages.success(self.request, f"Usuario '{self.object.login}' creado exitosamente.")
        return response

    def get_context_data(self, **kwargs):
        # Datos para los títulos y textos de los botones en la plantilla
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Crear Nuevo Usuario"
        context["boton_texto"] = "Guardar Usuario"
        return context


class UsuarioUpdateView(SoloAdminMixin, UpdateView):
    """
    CU15: Modificar datos y rol de un empleado existente (/usuarios/<id>/editar/).
    """

    model = Usuario
    form_class = UsuarioUpdateForm  # Permite cambiar datos y opcionalmente la clave
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
    CU15: Eliminar o dar de baja una cuenta (/usuarios/<id>/eliminar/).
    """

    model = Usuario
    template_name = "usuarios/usuario_confirm_delete.html"
    success_url = reverse_lazy("usuarios:usuario_list")

    def delete(self, request, *args, **kwargs):
        usuario = self.get_object()

        # Medida de seguridad vital: Nadie puede suicidar su propia cuenta activa
        if usuario == request.user:
            messages.error(request, "No puedes eliminar tu propia cuenta en sesión activa.")
            return redirect("usuarios:usuario_list")

        messages.success(request, f"Usuario '{usuario.login}' eliminado satisfactoriamente.")
        return super().delete(request, *args, **kwargs)


# ------------------------------------------------------------------------------
# VISTAS DE ENLACE AL DASHBOARD
# ------------------------------------------------------------------------------
class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista base del Dashboard Operativo.
    """

    template_name = "dashboard.html"


@login_required
def dashboard_redirect_view(request):
    """
    Función sencilla que recibe al usuario en /usuarios/dashboard/
    y lo redirige a la página principal del banco ('home' o '/').
    """
    return redirect("home")

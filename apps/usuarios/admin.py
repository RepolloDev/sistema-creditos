"""
================================================================================
MÓDULO: USUARIOS (apps/usuarios/admin.py)
================================================================================
¿QUÉ HACE ESTE ARCHIVO?
Configura el panel de control técnico integrado de Django (accesible en /admin/).
Le enseña a Django cómo mostrar los datos de los usuarios y de las auditorías
cuando un técnico o administrador de sistemas entra al panel de administración.

¿POR QUÉ ES NECESARIO?
Aunque tengamos pantallas bonitas para los usuarios normales del banco,
este panel sirve como herramienta de soporte técnico para el equipo de desarrollo:
- Permite revisar registros de auditoría si ocurre un problema.
- Permite desbloquear usuarios o cambiar permisos directamente.
================================================================================
"""

# admin: Módulo de Django que contiene todo el sistema del panel administrativo.
from django.contrib import admin

# BaseUserAdmin: Plantilla especial de Django para administrar usuarios en el panel.
# Sabe cómo mostrar los campos de contraseñas de forma segura y cómo organizar los permisos.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Importamos nuestros dos modelos
from .models import Auditoria, Usuario


# ------------------------------------------------------------------------------
# PANEL DE CONTROL: USUARIOS
# ------------------------------------------------------------------------------
@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """
    Configuración visual para la tabla Usuario en /admin/.
    """

    # Columnas que se verán en la tabla de resumen
    list_display = ("login", "nombre_completo", "rol", "activo", "is_staff")

    # Filtros laterales para hacer clic y filtrar usuarios rápidamente
    list_filter = ("rol", "activo", "is_staff")

    # Organización de los campos al entrar a editar un usuario:
    # Se agrupan en cajas con títulos para que sea ordenado.
    fieldsets = (
        (None, {"fields": ("login", "password")}),
        ("Información Personal", {"fields": ("nombre_completo", "rol")}),
        (
            "Permisos",
            {"fields": ("activo", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
    )

    # Barra de búsqueda: busca coincidencias en el login o en el nombre
    search_fields = ("login", "nombre_completo")

    # Orden predeterminado: por nombre de usuario alfabéticamente
    ordering = ("login",)


# ------------------------------------------------------------------------------
# PANEL DE CONTROL: AUDITORÍA
# ------------------------------------------------------------------------------
@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    """
    Configuración visual para consultar la bitácora histórica en /admin/.
    """

    # Columnas que se mostrarán en la lista de eventos
    list_display = ("fecha_hora", "usuario", "operacion", "entidad", "id_entidad", "resultado")

    # Filtros rápidos a la derecha de la pantalla
    list_filter = ("operacion", "entidad", "resultado", "fecha_hora")

    # Buscador por tipo de acción o módulo modificado
    search_fields = ("operacion", "entidad")

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Auditoria


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ("login", "nombre_completo", "rol", "activo", "is_staff")
    list_filter = ("rol", "activo", "is_staff")
    fieldsets = (
        (None, {"fields": ("login", "password")}),
        ("Información Personal", {"fields": ("nombre_completo", "rol")}),
        ("Permisos", {"fields": ("activo", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    search_fields = ("login", "nombre_completo")
    ordering = ("login",)


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha_hora", "usuario", "operacion", "entidad", "id_entidad", "resultado")
    list_filter = ("operacion", "entidad", "resultado", "fecha_hora")
    search_fields = ("operacion", "entidad")

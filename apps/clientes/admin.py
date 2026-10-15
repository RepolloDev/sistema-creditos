from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("ci", "apellidos", "nombres", "telefono", "ingresos_mensuales", "fecha_registro")
    search_fields = ("ci", "nombres", "apellidos", "telefono")
    list_filter = ("fecha_registro",)

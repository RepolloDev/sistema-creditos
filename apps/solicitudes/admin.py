from django.contrib import admin

from .models import Garantia, SolicitudCredito


class GarantiaInline(admin.TabularInline):
    model = Garantia
    extra = 1


@admin.register(SolicitudCredito)
class SolicitudCreditoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "monto_solicitado", "plazo_meses", "estado", "fecha_solicitud")
    list_filter = ("estado", "fecha_solicitud")
    search_fields = ("cliente__ci", "cliente__nombres", "cliente__apellidos", "destino")
    inlines = [GarantiaInline]


@admin.register(Garantia)
class GarantiaAdmin(admin.ModelAdmin):
    list_display = ("id", "solicitud", "tipo", "valor", "estado")
    list_filter = ("tipo", "estado")
    search_fields = ("descripcion", "solicitud__cliente__ci")

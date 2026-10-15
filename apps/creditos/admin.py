from django.contrib import admin

from .models import Contrato, Credito, Cuota


class CuotaInline(admin.TabularInline):
    model = Cuota
    extra = 0
    readonly_fields = ("numero_cuota", "fecha_vencimiento", "capital", "interes", "monto_cuota")


@admin.register(Credito)
class CreditoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_credito",
        "solicitud",
        "monto_aprobado",
        "saldo_capital",
        "estado",
        "fecha_desembolso",
    )
    list_filter = ("estado", "fecha_desembolso")
    search_fields = ("numero_credito", "solicitud__cliente__ci", "solicitud__cliente__apellidos")
    inlines = [CuotaInline]


@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = (
        "credito",
        "numero_cuota",
        "fecha_vencimiento",
        "monto_cuota",
        "saldo_cuota",
        "estado",
    )
    list_filter = ("estado", "fecha_vencimiento")
    search_fields = ("credito__numero_credito",)


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("numero_contrato", "credito", "estado", "fecha_generacion")
    list_filter = ("estado", "fecha_generacion")
    search_fields = ("numero_contrato", "credito__numero_credito")

from django.contrib import admin

from .models import RegistroRiesgoExterno, TransaccionCoreBancario


@admin.register(RegistroRiesgoExterno)
class RegistroRiesgoExternoAdmin(admin.ModelAdmin):
    list_display = (
        "ci",
        "nombres",
        "apellidos",
        "score_crediticio",
        "calificacion_riesgo",
        "deuda_sistema_financiero",
    )
    search_fields = ("ci", "nombres", "apellidos")
    list_filter = ("calificacion_riesgo", "tiene_mora_historica")


@admin.register(TransaccionCoreBancario)
class TransaccionCoreBancarioAdmin(admin.ModelAdmin):
    list_display = (
        "referencia_transaccion",
        "numero_credito",
        "monto",
        "estado",
        "fecha_procesamiento",
    )
    search_fields = ("referencia_transaccion", "numero_credito", "cuenta_destino")
    list_filter = ("estado",)

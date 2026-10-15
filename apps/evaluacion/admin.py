from django.contrib import admin
from .models import EvaluacionCredito


@admin.register(EvaluacionCredito)
class EvaluacionCreditoAdmin(admin.ModelAdmin):
    list_display = ("id", "solicitud", "capacidad_pago", "nivel_riesgo", "resultado", "fecha_evaluacion")
    list_filter = ("nivel_riesgo", "resultado", "fecha_evaluacion")
    search_fields = ("solicitud__cliente__ci", "solicitud__cliente__apellidos")

from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("numero_recibo", "cuota", "monto", "forma_pago", "fecha_pago")
    list_filter = ("forma_pago", "fecha_pago")
    search_fields = ("numero_recibo", "cuota__credito__numero_credito")

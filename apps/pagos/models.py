from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Pago(models.Model):
    class FormaPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        DEPOSITO = "DEPOSITO", "Depósito"

    cuota = models.ForeignKey(
        "creditos.Cuota",
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name="Cuota",
    )
    fecha_pago = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    forma_pago = models.CharField(
        max_length=20, choices=FormaPago.choices, default=FormaPago.EFECTIVO
    )
    numero_recibo = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = "PAGO"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Recibo {self.numero_recibo} - Cuota #{self.cuota.numero_cuota} ({self.monto})"

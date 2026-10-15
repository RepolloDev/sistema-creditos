from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class SolicitudCredito(models.Model):
    class Estado(models.TextChoices):
        REGISTRADA = "REGISTRADA", "Registrada"
        EN_EVALUACION = "EN_EVALUACION", "En Evaluación"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="solicitudes",
        verbose_name="Cliente",
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    monto_solicitado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    plazo_meses = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    destino = models.CharField(max_length=200)
    motivo_rechazo = models.CharField(max_length=300, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.REGISTRADA)

    class Meta:
        db_table = "SOLICITUD_CREDITO"
        verbose_name = "Solicitud de Crédito"
        verbose_name_plural = "Solicitudes de Crédito"

    def __str__(self):
        return f"Solicitud #{self.pk} - {self.cliente} ({self.get_estado_display()})"


class Garantia(models.Model):
    class Tipo(models.TextChoices):
        PERSONAL = "PERSONAL", "Personal"
        PRENDARIA = "PRENDARIA", "Prendaria"
        HIPOTECARIA = "HIPOTECARIA", "Hipotecaria"

    class Estado(models.TextChoices):
        REGISTRADA = "REGISTRADA", "Registrada"
        LIBERADA = "LIBERADA", "Liberada"

    solicitud = models.ForeignKey(
        SolicitudCredito,
        on_delete=models.CASCADE,
        related_name="garantias",
        verbose_name="Solicitud de Crédito",
    )
    tipo = models.CharField(max_length=50, choices=Tipo.choices)
    descripcion = models.CharField(max_length=300)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.REGISTRADA)

    class Meta:
        db_table = "GARANTIA"
        verbose_name = "Garantía"
        verbose_name_plural = "Garantías"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.valor} (Solicitud #{self.solicitud_id})"

from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class EvaluacionCredito(models.Model):
    class NivelRiesgo(models.TextChoices):
        BAJO = "BAJO", "Bajo"
        MEDIO = "MEDIO", "Medio"
        ALTO = "ALTO", "Alto"

    class Resultado(models.TextChoices):
        FAVORABLE = "FAVORABLE", "Favorable"
        DESFAVORABLE = "DESFAVORABLE", "Desfavorable"

    solicitud = models.OneToOneField(
        "solicitudes.SolicitudCredito",
        on_delete=models.CASCADE,
        related_name="evaluacion",
        verbose_name="Solicitud de Crédito",
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    ingresos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    gastos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    capacidad_pago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    nivel_riesgo = models.CharField(max_length=20, choices=NivelRiesgo.choices)
    resultado = models.CharField(max_length=20, choices=Resultado.choices)
    observaciones = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "EVALUACION_CREDITO"
        verbose_name = "Evaluación de Crédito"
        verbose_name_plural = "Evaluaciones de Crédito"

    def __str__(self):
        return f"Evaluación #{self.pk} - Solicitud #{self.solicitud_id} ({self.resultado})"

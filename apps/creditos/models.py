from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Credito(models.Model):
    class Estado(models.TextChoices):
        APROBADO = "APROBADO", "Aprobado"
        VIGENTE = "VIGENTE", "Vigente"
        EN_MORA = "EN_MORA", "En Mora"
        CANCELADO = "CANCELADO", "Cancelado"

    solicitud = models.OneToOneField(
        "solicitudes.SolicitudCredito",
        on_delete=models.PROTECT,
        related_name="credito",
        verbose_name="Solicitud de Crédito",
    )
    numero_credito = models.CharField(max_length=30, unique=True)
    monto_aprobado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    tasa_interes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Tasa de Interés Anual (%)",
    )
    plazo_meses = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    fecha_desembolso = models.DateTimeField(blank=True, null=True)
    saldo_capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.APROBADO
    )

    class Meta:
        db_table = "CREDITO"
        verbose_name = "Crédito"
        verbose_name_plural = "Créditos"

    def __str__(self):
        return f"{self.numero_credito} - {self.get_estado_display()} (Saldo: {self.saldo_capital})"


class Cuota(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        VENCIDA = "VENCIDA", "Vencida"
        PAGADA = "PAGADA", "Pagada"

    credito = models.ForeignKey(
        Credito,
        on_delete=models.CASCADE,
        related_name="cuotas",
        verbose_name="Crédito",
    )
    numero_cuota = models.PositiveIntegerField()
    fecha_vencimiento = models.DateField()
    capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    interes = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    monto_cuota = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    saldo_cuota = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )

    class Meta:
        db_table = "CUOTA"
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        constraints = [
            models.UniqueConstraint(
                fields=["credito", "numero_cuota"], name="unique_credito_numero_cuota"
            )
        ]

    def __str__(self):
        return f"Cuota #{self.numero_cuota} - {self.credito.numero_credito} ({self.get_estado_display()})"


class Contrato(models.Model):
    class Estado(models.TextChoices):
        GENERADO = "GENERADO", "Generado"
        FIRMADO = "FIRMADO", "Firmado"

    credito = models.OneToOneField(
        Credito,
        on_delete=models.CASCADE,
        related_name="contrato",
        verbose_name="Crédito",
    )
    numero_contrato = models.CharField(max_length=30, unique=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.GENERADO
    )

    class Meta:
        db_table = "CONTRATO"
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self):
        return f"{self.numero_contrato} - {self.get_estado_display()}"

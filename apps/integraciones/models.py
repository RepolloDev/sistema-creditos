from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class RegistroRiesgoExterno(models.Model):
    """
    Tabla simulada del Sistema de Riesgo Crediticio / Buró Externo.
    Almacena el historial y calificación crediticia por Cédula de Identidad.
    """

    class CalificacionRiesgo(models.TextChoices):
        BAJO = "BAJO", "Bajo Riesgo"
        MEDIO = "MEDIO", "Riesgo Medio"
        ALTO = "ALTO", "Alto Riesgo"

    ci = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    score_crediticio = models.PositiveIntegerField(
        validators=[MinValueValidator(300), MaxValueValidator(850)],
        verbose_name="Score Crediticio (300-850)",
    )
    calificacion_riesgo = models.CharField(
        max_length=10,
        choices=CalificacionRiesgo.choices,
        default=CalificacionRiesgo.BAJO,
    )
    deuda_sistema_financiero = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Deuda Total Vigente en Sistema Financiero",
    )
    entidades_reportantes = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de Entidades Financieras que Reportan Deuda",
    )
    tiene_mora_historica = models.BooleanField(
        default=False,
        verbose_name="¿Registra antecedentes de mora?",
    )
    detalle_antecedentes = models.TextField(
        blank=True,
        default="",
        verbose_name="Detalle de antecedentes crediticios",
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "EXT_REGISTRO_RIESGO"
        verbose_name = "Registro de Riesgo Externo"
        verbose_name_plural = "Registros de Riesgo Externo"

    def __str__(self):
        return f"Buró {self.ci} - {self.nombres} {self.apellidos} (Score: {self.score_crediticio}, {self.calificacion_riesgo})"


class TransaccionCoreBancario(models.Model):
    """
    Tabla simulada del Core Bancario para registrar transferencias y desembolsos.
    """

    class EstadoTransaccion(models.TextChoices):
        EXITOSA = "EXITOSA", "Exitosa"
        RECHAZADA = "RECHAZADA", "Rechazada"
        PENDIENTE = "PENDIENTE", "Pendiente"

    referencia_transaccion = models.CharField(
        max_length=50, unique=True, verbose_name="Código de Referencia Bancaria"
    )
    numero_credito = models.CharField(max_length=30, verbose_name="Número de Crédito")
    cuenta_destino = models.CharField(max_length=30, verbose_name="Número de Cuenta Destino")
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Monto Desembolsado",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoTransaccion.choices,
        default=EstadoTransaccion.EXITOSA,
    )
    codigo_autorizacion = models.CharField(max_length=30, blank=True, default="")
    mensaje_respuesta = models.CharField(
        max_length=255, default="Transacción procesada correctamente"
    )
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "EXT_TRANSACCION_CORE_BANCARIO"
        verbose_name = "Transacción Core Bancario"
        verbose_name_plural = "Transacciones Core Bancario"

    def __str__(self):
        return f"{self.referencia_transaccion} - {self.numero_credito} ({self.monto} BOB - {self.estado})"

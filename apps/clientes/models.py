from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal


class Cliente(models.Model):
    ci = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    ingresos_mensuales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Ingresos Mensuales",
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "CLIENTE"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.ci} - {self.nombres} {self.apellidos}"

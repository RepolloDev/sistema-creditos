"""
Capa de servicios para el módulo de pagos y cobranzas.
Reglas de negocio aplicables:
- RN07: Saldo no negativo (el saldo de capital y de cada cuota no pueden ser < 0).
- RN08: Asociación de pagos (se imputa de forma directa a la cuota más antigua impaga).
- RN09: Control de mora (cuota vencida impaga transiciona el crédito a EN_MORA).
- RN10: Condición de cancelación (crédito pasa a CANCELADO cuando saldo deudor sea 0.00).

Modelos matemáticos de cobranza (Sección 10.1.3 y 10.1.4 del informe):
1. Interés penal por mora:
   Ip = Scuota * (tasa_mora / 100) * (dias_retraso / 360)
2. Imputación de pagos:
   Nuevo saldo cuota = max(0, Scuota - Abono)
   Si Scuota == 0 -> Estado cuota = PAGADA
   Nuevo saldo crédito = max(0, Scredito - Amortizacion_Capital)
   Si Scredito == 0 y no hay cuotas pendientes -> Estado crédito = CANCELADO
"""

from decimal import Decimal
from typing import Any

from .models import Pago


def registrar_pago_cuota(
    cuota_id: int,
    monto: Decimal,
    forma_pago: str = "EFECTIVO",
    cajero_id: int = None,
) -> Pago:
    """
    CU12 / RF13 / RN08: Registra el abono monetario recibido en ventanilla.
    Aplica imputación a la cuota (RN08), valida que saldo no sea negativo (RN07),
    actualiza el saldo deudor del crédito y si liquida la última cuota,
    transiciona el crédito a CANCELADO (RN10). Genera comprobante formal.

    Retorna:
        Instancia de Pago con número de recibo generado.
    """
    pass


def aplicar_imputacion_cascada(credito_id: int, monto_total: Decimal) -> list[Pago]:
    """
    Imputa un pago en cascada sobre el cronograma comenzando siempre por la cuota
    exigible más antigua impaga (RN08).
    """
    pass


def ejecutar_control_mora() -> dict[str, Any]:
    """
    CU13 / RF14 / RN09: Tarea periódica de control de mora.
    Identifica cuotas cuya fecha_vencimiento < hoy y estado != PAGADA.
    Actualiza estado de cuotas a VENCIDA y el crédito a EN_MORA.
    Registra evento en bitácora de auditoría.
    """
    pass


def calcular_interes_penal(
    saldo_cuota: Decimal, dias_retraso: int, tasa_mora_anual: Decimal
) -> Decimal:
    """
    Sección 10.1.3: Devenga interés penal por cada día de mora sobre el saldo impago.
    """
    pass

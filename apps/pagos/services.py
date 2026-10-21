"""
Capa de servicios para el módulo de pagos y cobranzas.
Reglas de negocio aplicables:
- RN07: Saldo no negativo (el saldo de capital y de cada cuota no pueden ser < 0).
- RN08: Asociación de pagos (se imputa de forma directa a la cuota más antigua impaga).
- RN09: Control de mora (cuota vencida impaga transiciona el crédito a EN_MORA).
- RN10: Condición de cancelación (crédito pasa a CANCELADO cuando saldo deudor sea 0.00).
"""

import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from creditos.models import Credito, Cuota
from solicitudes.models import Garantia
from usuarios.models import Auditoria, Usuario
from .models import Pago


def _round(val: Decimal) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_interes_penal(
    saldo_cuota: Decimal, dias_retraso: int, tasa_mora_anual: Decimal = Decimal("24.00")
) -> Decimal:
    """
    Sección 10.1.3: Devenga interés penal por cada día de mora sobre el saldo impago.
    Ip = Scuota * (tasa_mora / 100) * (dias_retraso / 360)
    """
    if dias_retraso <= 0 or saldo_cuota <= Decimal("0.00"):
        return Decimal("0.00")
    tasa = Decimal(str(tasa_mora_anual)) / Decimal("100.00")
    interes_mora = Decimal(str(saldo_cuota)) * tasa * (Decimal(dias_retraso) / Decimal("360.00"))
    return _round(interes_mora)


def _generar_numero_recibo() -> str:
    ultimo = (Pago.objects.order_by("-id").values_list("id", flat=True).first() or 0) + 1
    recibo = f"REC-2026-{ultimo:05d}"
    while Pago.objects.filter(numero_recibo=recibo).exists():
        ultimo += 1
        recibo = f"REC-2026-{ultimo:05d}"
    return recibo


@transaction.atomic
def registrar_pago_cuota(
    cuota_id: int,
    monto: Decimal,
    forma_pago: str = "EFECTIVO",
    usuario: Optional[Usuario] = None,
) -> Pago:
    """
    CU12 / RF13 / RN07 / RN08 / RN10: Registra el abono monetario recibido en ventanilla.
    Aplica imputación a la cuota, valida que saldo no sea negativo (RN07),
    actualiza el saldo deudor del crédito y si liquida la última cuota,
    transiciona el crédito a CANCELADO (RN10).
    """
    abono = _round(monto)
    if abono <= Decimal("0.00"):
        raise ValidationError("El monto abonado debe ser mayor a 0.00.")

    cuota = Cuota.objects.select_for_update().select_related("credito").get(pk=cuota_id)
    credito = Credito.objects.select_for_update().get(pk=cuota.credito_id)

    if cuota.estado == Cuota.Estado.PAGADA or cuota.saldo_cuota <= Decimal("0.00"):
        raise ValidationError(f"La Cuota #{cuota.numero_cuota} ya se encuentra totalmente pagada.")

    # Si abona más del saldo de esta cuota, se limita al saldo o se aplica en cascada
    monto_aplicado = min(abono, cuota.saldo_cuota)

    # Proporción de capital amortizado
    if cuota.monto_cuota > Decimal("0.00"):
        proporcion_capital = (monto_aplicado / cuota.monto_cuota) * cuota.capital
    else:
        proporcion_capital = monto_aplicado
    amortizacion_capital = _round(min(credito.saldo_capital, proporcion_capital))

    # Actualizar cuota (RN07)
    cuota.saldo_cuota = _round(max(Decimal("0.00"), cuota.saldo_cuota - monto_aplicado))
    if cuota.saldo_cuota == Decimal("0.00"):
        cuota.estado = Cuota.Estado.PAGADA
    cuota.save(update_fields=["saldo_cuota", "estado"])

    # Actualizar crédito (RN07)
    credito.saldo_capital = _round(max(Decimal("0.00"), credito.saldo_capital - amortizacion_capital))

    # Verificar estado general de las cuotas del crédito (RN09 / RN10)
    cuotas_restantes = credito.cuotas.exclude(estado=Cuota.Estado.PAGADA)
    if not cuotas_restantes.exists():
        credito.saldo_capital = Decimal("0.00")
        credito.estado = Credito.Estado.CANCELADO
        # Liberar garantías asociadas (D07)
        credito.solicitud.garantias.update(estado=Garantia.Estado.LIBERADA)
    else:
        tiene_vencidas = cuotas_restantes.filter(estado=Cuota.Estado.VENCIDA).exists()
        if not tiene_vencidas and credito.estado == Credito.Estado.EN_MORA:
            credito.estado = Credito.Estado.VIGENTE

    credito.save(update_fields=["saldo_capital", "estado"])

    pago = Pago.objects.create(
        cuota=cuota,
        monto=monto_aplicado,
        forma_pago=forma_pago,
        numero_recibo=_generar_numero_recibo(),
    )

    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        operacion="REGISTRAR_PAGO",
        entidad="PAGO",
        id_entidad=pago.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return pago


@transaction.atomic
def aplicar_imputacion_cascada(
    credito_id: int,
    monto_total: Decimal,
    forma_pago: str = "EFECTIVO",
    usuario: Optional[Usuario] = None,
    cuota_inicial_id: Optional[int] = None,
) -> list[Pago]:
    """
    Imputa un pago en cascada comenzando por la cuota seleccionada o la más antigua impaga (RN08).
    Si el monto supera el saldo de la primera cuota, el excedente amortiza las siguientes cuotas.
    """
    remanente = _round(monto_total)
    if remanente <= Decimal("0.00"):
        raise ValidationError("El monto a abonar debe ser mayor a 0.00.")

    cuotas_pendientes = list(
        Cuota.objects.select_for_update()
        .filter(credito_id=credito_id, saldo_cuota__gt=Decimal("0.00"))
        .exclude(estado=Cuota.Estado.PAGADA)
        .order_by("numero_cuota")
    )

    if not cuotas_pendientes:
        raise ValidationError("El crédito no tiene cuotas pendientes de pago.")

    total_pendiente = _round(sum((c.saldo_cuota for c in cuotas_pendientes), Decimal("0.00")))
    if remanente > total_pendiente:
        raise ValidationError(
            f"El monto ingresado (Bs. {remanente}) excede el saldo total de cuotas pendientes del crédito (Bs. {total_pendiente})."
        )

    if cuota_inicial_id:
        cuotas_pendientes.sort(key=lambda c: (0 if c.pk == cuota_inicial_id else 1, c.numero_cuota))

    pagos_realizados = []
    for cuota in cuotas_pendientes:
        if remanente <= Decimal("0.00"):
            break
        abono_cuota = min(remanente, cuota.saldo_cuota)
        pago = registrar_pago_cuota(
            cuota_id=cuota.pk,
            monto=abono_cuota,
            forma_pago=forma_pago,
            usuario=usuario,
        )
        pagos_realizados.append(pago)
        remanente = _round(remanente - abono_cuota)

    return pagos_realizados


@transaction.atomic
def ejecutar_control_mora(usuario: Optional[Usuario] = None) -> dict[str, Any]:
    """
    CU13 / RF14 / RN09: Tarea periódica de control de mora.
    Identifica cuotas cuya fecha_vencimiento < hoy y estado != PAGADA.
    Actualiza estado de cuotas a VENCIDA y el crédito a EN_MORA.
    """
    hoy = date.today()
    cuotas_expiradas = Cuota.objects.select_related("credito").filter(
        fecha_vencimiento__lt=hoy,
        saldo_cuota__gt=Decimal("0.00"),
    ).exclude(estado=Cuota.Estado.PAGADA)

    cuotas_actualizadas = 0
    creditos_afectados_ids = set()

    for cuota in cuotas_expiradas:
        if cuota.estado != Cuota.Estado.VENCIDA:
            cuota.estado = Cuota.Estado.VENCIDA
            cuota.save(update_fields=["estado"])
            cuotas_actualizadas += 1
        creditos_afectados_ids.add(cuota.credito_id)

    creditos_en_mora = 0
    for cred_id in creditos_afectados_ids:
        credito = Credito.objects.get(pk=cred_id)
        if credito.estado == Credito.Estado.VIGENTE:
            credito.estado = Credito.Estado.EN_MORA
            credito.save(update_fields=["estado"])
            creditos_en_mora += 1
            Auditoria.objects.create(
                usuario=usuario if usuario and usuario.is_authenticated else None,
                operacion="DECLARAR_MORA",
                entidad="CREDITO",
                id_entidad=credito.pk,
                resultado=Auditoria.Resultado.EXITOSO,
            )

    return {
        "fecha_corte": hoy,
        "cuotas_marcadas_vencidas": cuotas_actualizadas,
        "total_cuotas_vencidas_activas": Cuota.objects.filter(estado=Cuota.Estado.VENCIDA).count(),
        "creditos_pasados_a_mora": creditos_en_mora,
        "total_creditos_en_mora": Credito.objects.filter(estado=Credito.Estado.EN_MORA).count(),
    }

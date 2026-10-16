"""
Capa de servicios para el módulo de evaluación crediticia.
Reglas de negocio aplicables:
- RN03: Evaluación obligatoria (ninguna solicitud puede aprobarse sin evaluación favorable).
- RN14: Asociación de riesgo (el dictamen debe respaldarse con consulta al buró externo).

Modelos matemáticos implementados (Sección 10.1.1 del informe):
1. Capacidad disponible mensual:
   Cd = I - G
   donde I = ingresos verificados, G = gastos declarados.
2. Cuota máxima admisible:
   Cmax = Cd * alpha  (factor prudencial de endeudamiento alpha = 0.40)
   Condición de solvencia: Cuota solicitada <= Cmax.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional
from django.core.exceptions import ValidationError
from django.db import transaction

from integraciones.services import ServicioRiesgoExterno
from solicitudes.models import SolicitudCredito
from usuarios.models import Auditoria, Usuario
from .models import EvaluacionCredito


def _round(val: Decimal) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_capacidad_pago(
    ingresos: Decimal, gastos: Decimal, alpha: Decimal = Decimal("0.40")
) -> dict[str, Decimal]:
    """
    CU04 / RF05: Calcula capacidad de pago y margen de endeudamiento mensual.
    """
    ing = _round(ingresos)
    gas = _round(gastos)
    cd = _round(ing - gas)
    cmax = _round(max(Decimal("0.00"), cd * Decimal(str(alpha))))
    return {
        "ingresos": ing,
        "gastos": gas,
        "capacidad_disponible": cd,
        "cuota_maxima_admisible": cmax,
    }


def estimar_cuota_francesa(
    monto: Decimal, plazo_meses: int, tasa_anual: Decimal = Decimal("14.00")
) -> Decimal:
    """
    Estima la cuota mensual fija bajo sistema francés para comparar contra Cmax.
    """
    if plazo_meses <= 0 or monto <= 0:
        return Decimal("0.00")
    im = Decimal(str(tasa_anual)) / Decimal("1200")
    if im == 0:
        return _round(monto / Decimal(plazo_meses))
    factor = (Decimal("1") + im) ** int(plazo_meses)
    cuota = Decimal(str(monto)) * (im * factor) / (factor - Decimal("1"))
    return _round(cuota)


def consultar_historial_externo(ci: str, nombres: str = "", apellidos: str = "") -> dict[str, Any]:
    """
    CU03 / RF04 / RN14: Consulta antecedentes de riesgo al servicio simulado de buró.
    """
    return ServicioRiesgoExterno.consultar_antecedentes(ci=ci, nombres=nombres, apellidos=apellidos)


@transaction.atomic
def registrar_dictamen_evaluacion(
    solicitud_id: int,
    ingresos: Decimal,
    gastos: Decimal,
    nivel_riesgo: str,
    resultado: str,
    observaciones: str = "",
    usuario: Optional[Usuario] = None,
) -> EvaluacionCredito:
    """
    CU05 / RF06: Registra la evaluación técnica y emite la recomendación formal (FAVORABLE / DESFAVORABLE).
    Actualiza el estado de la solicitud a EN_EVALUACION.
    """
    solicitud = SolicitudCredito.objects.select_for_update().get(pk=solicitud_id)
    calculo = calcular_capacidad_pago(ingresos, gastos)
    capacidad_pago = calculo["capacidad_disponible"]

    # Asegurar que exista registro en el buró de riesgo externo (RN14)
    consultar_historial_externo(
        ci=solicitud.cliente.ci,
        nombres=solicitud.cliente.nombres,
        apellidos=solicitud.cliente.apellidos,
    )

    evaluacion, _ = EvaluacionCredito.objects.update_or_create(
        solicitud=solicitud,
        defaults={
            "ingresos": calculo["ingresos"],
            "gastos": calculo["gastos"],
            "capacidad_pago": capacidad_pago,
            "nivel_riesgo": nivel_riesgo,
            "resultado": resultado,
            "observaciones": observaciones.strip() if observaciones else None,
        },
    )

    if solicitud.estado == SolicitudCredito.Estado.REGISTRADA:
        solicitud.estado = SolicitudCredito.Estado.EN_EVALUACION
        solicitud.save(update_fields=["estado"])

    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        operacion="EVALUAR_CREDITO",
        entidad="EVALUACION_CREDITO",
        id_entidad=evaluacion.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return evaluacion

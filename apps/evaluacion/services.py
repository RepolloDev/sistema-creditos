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

from decimal import Decimal
from typing import Any

from .models import EvaluacionCredito


def calcular_capacidad_pago(
    ingresos: Decimal, gastos: Decimal, alpha: Decimal = Decimal("0.40")
) -> dict[str, Decimal]:
    """
    CU04 / RF05: Calcula capacidad de pago y margen de endeudamiento mensual.

    Fórmulas:
        Cd = ingresos - gastos
        Cmax = Cd * alpha  (donde alpha = 0.40 por defecto)

    Retorna:
        dict con {"capacidad_disponible": Cd, "cuota_maxima_admisible": Cmax}
    """
    pass


def consultar_historial_externo(ci: str) -> dict[str, Any]:
    """
    CU03 / RF04 / RN14: Consulta antecedentes de riesgo al servicio simulado de buró.
    Usa ServicioRiesgoExterno.consultar_antecedentes.

    Retorna:
        dict con score, nivel_riesgo, deuda_vigente, observaciones y es_favorable.
    """
    pass


def registrar_dictamen_evaluacion(
    solicitud_id: int,
    ingresos: Decimal,
    gastos: Decimal,
    capacidad_pago: Decimal,
    nivel_riesgo: str,
    resultado: str,
    observaciones: str = "",
) -> EvaluacionCredito:
    """
    CU05 / RF06: Registra la evaluación técnica y emite la recomendación formal (FAVORABLE / DESFAVORABLE).
    Actualiza el estado de la solicitud y notifica que está lista para resolución.

    Retorna:
        Instancia de EvaluacionCredito guardada en BD.
    """
    pass

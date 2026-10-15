"""
Capa de servicios para el módulo de créditos bancarios.
Reglas de negocio aplicables:
- RN03: Evaluación obligatoria (no se aprueba sin evaluación técnica favorable).
- RN04: Atribución por monto (el usuario debe tener límite de aprobación suficiente).
- RN05: Formalización previa (la aprobación genera contrato formal correlativo).
- RN06: Cronograma obligatorio (todo crédito genera cronograma de cuotas antes de desembolso).
- RN11: Motivo de rechazo obligatorio en denegación.

Modelos matemáticos de amortización (Sección 10.1.2 del informe - Sistema Francés):
1. Tasa mensual efectiva:
   im = r / (12 * 100)
2. Cuota mensual fija (anualidad):
   C = P * [ im * (1 + im)^n ] / [ (1 + im)^n - 1 ]
3. Para cada cuota k = 1..n:
   Ik = S_{k-1} * im       (interés del periodo)
   Ak = C - Ik             (amortización a capital)
   Sk = S_{k-1} - Ak       (saldo deudor restante)
"""

from decimal import Decimal
from typing import Any

from .models import Contrato, Credito, Cuota


def aprobar_solicitud_credito(
    solicitud_id: int,
    usuario_id: int,
    tasa_anual: Decimal,
    plazo_meses: int = None,
    monto_aprobado: Decimal = None,
) -> Credito:
    """
    CU07 / RF08: Aprobar crédito, verificar atribución de monto (RN04) y evaluación previa (RN03).
    Dispara automáticamente:
      1. Generación de contrato legal correlativo (CU09 / RN05).
      2. Generación de cronograma de amortización francesa (CU10 / RN06).
    Transiciona solicitud a APROBADA y crédito a APROBADO.
    """
    pass


def rechazar_solicitud_credito(solicitud_id: int, motivo_rechazo: str) -> None:
    """
    CU08 / RF09 / RN11: Rechaza la solicitud registrando obligatoriamente el motivo formal.
    Transiciona solicitud a RECHAZADA.
    """
    pass


def generar_contrato(credito_id: int) -> Contrato:
    """
    CU09 / RF10 / RN05: Genera el instrumento legal con correlativo único en estado GENERADO.
    """
    pass


def generar_cronograma_frances(credito_id: int) -> list[Cuota]:
    """
    CU10 / RF11 / RN06: Calcula y persiste las n cuotas fijas bajo el Sistema Francés.
    Aplica fórmulas (3), (4), (5), (6) y (7) de la Sección 10.1.2.
    """
    pass


def desembolsar_credito(credito_id: int, cuenta_destino: str = "") -> dict[str, Any]:
    """
    CU11 / RF12: Valida formalización del contrato, solicita acreditación al Core Bancario
    simulado (ServicioCoreBancario.procesar_desembolso) y transiciona el crédito a VIGENTE.
    """
    pass


def generar_reporte_cartera() -> dict[str, Any]:
    """
    CU14 / RF15: Consolida métricas de cartera total, colocada, saldos y distribución por estado.
    """
    pass

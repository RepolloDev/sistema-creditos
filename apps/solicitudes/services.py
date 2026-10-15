"""
Capa de servicios para el módulo de solicitudes de crédito.
Reglas de negocio aplicables:
- RN01: Unicidad de cliente (una solicitud pertenece a un único cliente validado).
- RN02: Secuencia de estados: REGISTRADA -> EN_EVALUACION -> (APROBADA | RECHAZADA).
- RN13: Registro de garantías (tipo, descripción, valor y estado).
"""

from decimal import Decimal

from .models import Garantia, SolicitudCredito


def registrar_solicitud(
    cliente_id: int, monto: Decimal, plazo_meses: int, destino: str
) -> SolicitudCredito:
    """
    CU02 / RF03: Registrar solicitud de crédito en estado inicial REGISTRADA.

    Parámetros:
        cliente_id: ID del cliente solicitante previamente registrado.
        monto: Monto en moneda nacional solicitado (debe ser > 0).
        plazo_meses: Duración del crédito en meses (debe ser >= 1).
        destino: Objeto o destino del financiamiento.

    Retorna:
        Instancia de SolicitudCredito creada con estado REGISTRADA.
    """
    pass


def registrar_garantia(
    solicitud_id: int, tipo: str, descripcion: str, valor_estimado: Decimal
) -> Garantia:
    """
    CU06 / RF07: Registrar respaldo patrimonial o garante vinculado a una solicitud.

    Parámetros:
        solicitud_id: ID de la solicitud a respaldar.
        tipo: Tipo de garantía (PERSONAL, PRENDARIA, HIPOTECARIA).
        descripcion: Detalle del bien mueble/inmueble o datos del garante.
        valor_estimado: Avalúo o valor comercial estimado.

    Retorna:
        Instancia de Garantia creada en estado REGISTRADA.
    """
    pass


def enviar_a_evaluacion(solicitud_id: int) -> SolicitudCredito:
    """
    Transiciona el estado de la solicitud de REGISTRADA a EN_EVALUACION (RN02).
    Notifica al equipo de analistas de crédito para dar inicio a la evaluación técnica.
    """
    pass

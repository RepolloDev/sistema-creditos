"""
Capa de servicios para el módulo de solicitudes de crédito.
Reglas de negocio aplicables:
- RN01: Unicidad de cliente (una solicitud pertenece a un único cliente validado).
- RN02: Secuencia de estados: REGISTRADA -> EN_EVALUACION -> (APROBADA | RECHAZADA).
- RN13: Registro de garantías (tipo, descripción, valor y estado).
"""

from decimal import Decimal
from typing import Optional
from django.core.exceptions import ValidationError
from clientes.models import Cliente
from usuarios.models import Auditoria, Usuario
from .models import Garantia, SolicitudCredito


def registrar_solicitud(
    cliente_id: int,
    monto: Decimal,
    plazo_meses: int,
    destino: str,
    usuario: Optional[Usuario] = None,
) -> SolicitudCredito:
    """
    CU02 / RF03 / RN02: Registra una solicitud en estado inicial REGISTRADA.
    """
    if monto <= Decimal("0.00"):
        raise ValidationError("El monto solicitado debe ser mayor a cero.")
    if plazo_meses < 1 or plazo_meses > 240:
        raise ValidationError("El plazo debe estar entre 1 y 240 meses.")

    cliente = Cliente.objects.get(pk=cliente_id)

    solicitud = SolicitudCredito.objects.create(
        cliente=cliente,
        monto_solicitado=monto,
        plazo_meses=plazo_meses,
        destino=destino.strip(),
        estado=SolicitudCredito.Estado.REGISTRADA,
    )

    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        operacion="REGISTRAR_SOLICITUD",
        entidad="SOLICITUD_CREDITO",
        id_entidad=solicitud.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return solicitud


def registrar_garantia(
    solicitud_id: int,
    tipo: str,
    descripcion: str,
    valor: Decimal,
    usuario: Optional[Usuario] = None,
) -> Garantia:
    """
    CU06 / RF07 / RN13: Registra una garantía asociada a una solicitud de crédito.
    """
    if valor <= Decimal("0.00"):
        raise ValidationError("El valor estimado de la garantía debe ser positivo.")
    if not descripcion or not descripcion.strip():
        raise ValidationError("La descripción de la garantía es obligatoria.")

    solicitud = SolicitudCredito.objects.get(pk=solicitud_id)

    garantia = Garantia.objects.create(
        solicitud=solicitud,
        tipo=tipo,
        descripcion=descripcion.strip(),
        valor=valor,
        estado=Garantia.Estado.REGISTRADA,
    )

    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        operacion="REGISTRAR_GARANTIA",
        entidad="GARANTIA",
        id_entidad=garantia.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return garantia

"""
Capa de servicios para el módulo de clientes.
Lógica de negocio desacoplada de vistas y formularios.
"""

from decimal import Decimal
from typing import Optional
from django.core.exceptions import ValidationError
from usuarios.models import Auditoria, Usuario
from .models import Cliente


def registrar_cliente(datos: dict, usuario: Optional[Usuario] = None) -> Cliente:
    """
    CU01 / RF01 / RN01: Registrar nuevo cliente validando unicidad de CI e ingresos >= 0.
    """
    ci = str(datos.get("ci", "")).strip()
    if not ci:
        raise ValidationError("La Cédula de Identidad (CI) es obligatoria.")
    if Cliente.objects.filter(ci__iexact=ci).exists():
        raise ValidationError(f"Ya existe un cliente registrado con el CI '{ci}' (RN01).")

    ingresos = Decimal(str(datos.get("ingresos_mensuales", "0.00")))
    if ingresos < Decimal("0.00"):
        raise ValidationError("Los ingresos mensuales no pueden ser negativos.")

    cliente = Cliente.objects.create(
        ci=ci,
        nombres=datos.get("nombres", "").strip(),
        apellidos=datos.get("apellidos", "").strip(),
        telefono=datos.get("telefono", "").strip() or None,
        direccion=datos.get("direccion", "").strip() or None,
        ingresos_mensuales=ingresos,
    )

    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        operacion="REGISTRAR_CLIENTE",
        entidad="CLIENTE",
        id_entidad=cliente.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return cliente


def buscar_cliente_por_ci(ci: str) -> Optional[Cliente]:
    """
    Búsqueda de cliente por Cédula de Identidad exacta.
    """
    return Cliente.objects.filter(ci__iexact=ci.strip()).first()


def obtener_perfil_financiero(cliente_id: int) -> dict:
    """
    Retorna ingresos, solicitudes y créditos vigentes para evaluación crediticia.
    """
    cliente = Cliente.objects.prefetch_related("solicitudes__credito").get(pk=cliente_id)
    solicitudes = cliente.solicitudes.all()
    creditos_activos = [
        s.credito for s in solicitudes if hasattr(s, "credito") and s.credito.estado in ("VIGENTE", "EN_MORA")
    ]
    tiene_mora = any(c.estado == "EN_MORA" for c in creditos_activos)
    saldo_deudor_interno = sum((c.saldo_capital for c in creditos_activos), Decimal("0.00"))

    return {
        "cliente": cliente,
        "ingresos_mensuales": cliente.ingresos_mensuales,
        "total_solicitudes": solicitudes.count(),
        "creditos_activos": len(creditos_activos),
        "tiene_mora_interna": tiene_mora,
        "saldo_deudor_interno": saldo_deudor_interno,
    }

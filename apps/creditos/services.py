"""
Capa de servicios para el módulo de créditos bancarios.
Reglas de negocio aplicables:
- RN03: Evaluación obligatoria (no se aprueba sin evaluación técnica favorable).
- RN04: Atribución por monto (el usuario debe tener límite de aprobación suficiente).
- RN05: Formalización previa (la aprobación genera contrato formal correlativo).
- RN06: Cronograma obligatorio (todo crédito genera cronograma de cuotas antes de desembolso).
- RN11: Motivo de rechazo obligatorio en denegación.
"""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone

from integraciones.services import ServicioCoreBancario
from pagos.models import Pago
from solicitudes.models import SolicitudCredito
from usuarios.models import Auditoria, Usuario
from .models import Contrato, Credito, Cuota


def _round(val: Decimal) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@transaction.atomic
def generar_contrato(credito_id: int) -> Contrato:
    """
    CU09 / RF10 / RN05: Genera el instrumento legal con correlativo único en estado GENERADO.
    """
    credito = Credito.objects.get(pk=credito_id)
    numero_contrato = f"CON-2026-{credito.pk:04d}"
    contrato, _ = Contrato.objects.update_or_create(
        credito=credito,
        defaults={
            "numero_contrato": numero_contrato,
            "estado": Contrato.Estado.GENERADO,
        },
    )
    return contrato


@transaction.atomic
def generar_cronograma_frances(credito_id: int) -> list[Cuota]:
    """
    CU10 / RF11 / RN06: Calcula y persiste las n cuotas fijas bajo el Sistema Francés.
    """
    credito = Credito.objects.get(pk=credito_id)
    # Limpiar cuotas previas si se regenera
    credito.cuotas.all().delete()

    p = Decimal(str(credito.monto_aprobado))
    n = int(credito.plazo_meses)
    r = Decimal(str(credito.tasa_interes))
    im = r / Decimal("1200")

    if im == Decimal("0"):
        cuota_fija = _round(p / Decimal(n))
    else:
        factor = (Decimal("1") + im) ** n
        cuota_fija = _round(p * (im * factor) / (factor - Decimal("1")))

    saldo = p
    hoy = date.today()
    cuotas_creadas = []

    for k in range(1, n + 1):
        interes = _round(saldo * im)
        if k == n:
            capital = saldo
            monto_cuota = _round(capital + interes)
            saldo = Decimal("0.00")
        else:
            capital = _round(cuota_fija - interes)
            saldo = _round(saldo - capital)
            monto_cuota = cuota_fija

        fecha_vence = hoy + timedelta(days=30 * k)

        cuota = Cuota.objects.create(
            credito=credito,
            numero_cuota=k,
            fecha_vencimiento=fecha_vence,
            capital=capital,
            interes=interes,
            monto_cuota=monto_cuota,
            saldo_cuota=monto_cuota,
            estado=Cuota.Estado.PENDIENTE,
        )
        cuotas_creadas.append(cuota)

    return cuotas_creadas


@transaction.atomic
def aprobar_solicitud_credito(
    solicitud_id: int,
    usuario_id: Optional[int],
    tasa_anual: Decimal,
    plazo_meses: Optional[int] = None,
    monto_aprobado: Optional[Decimal] = None,
) -> Credito:
    """
    CU07 / RF08: Aprobar crédito, verificar evaluación previa (RN03) y atribución (RN04).
    Dispara automáticamente CU09 (Contrato) y CU10 (Cronograma).
    """
    solicitud = SolicitudCredito.objects.select_for_update().get(pk=solicitud_id)
    usuario = Usuario.objects.filter(pk=usuario_id).first() if usuario_id else None

    # Validar RN03: Evaluación obligatoria y favorable
    if not hasattr(solicitud, "evaluacion"):
        raise ValidationError("RN03: La solicitud no cuenta con una evaluación técnica registrada.")
    if solicitud.evaluacion.resultado != "FAVORABLE":
        raise ValidationError("RN03: No se puede aprobar una solicitud con dictamen DESFAVORABLE.")

    monto_final = _round(monto_aprobado if monto_aprobado is not None else solicitud.monto_solicitado)
    plazo_final = int(plazo_meses if plazo_meses is not None else solicitud.plazo_meses)
    tasa_final = _round(tasa_anual)

    # Validar RN04: Límite de atribución por monto (Techo referencial para Jefe: 500,000 Bs.)
    if monto_final > Decimal("500000.00") and (not usuario or not usuario.is_superuser):
        raise ValidationError("RN04: El monto excede el límite de atribución autorizado (Bs. 500,000.00).")

    # Generar número de crédito único
    ultimo_id = (Credito.objects.order_by("-id").values_list("id", flat=True).first() or 0) + 1
    numero_credito = f"CRE-2026-{ultimo_id:04d}"
    while Credito.objects.filter(numero_credito=numero_credito).exists():
        ultimo_id += 1
        numero_credito = f"CRE-2026-{ultimo_id:04d}"

    credito, _ = Credito.objects.update_or_create(
        solicitud=solicitud,
        defaults={
            "numero_credito": numero_credito,
            "monto_aprobado": monto_final,
            "tasa_interes": tasa_final,
            "plazo_meses": plazo_final,
            "saldo_capital": monto_final,
            "estado": Credito.Estado.APROBADO,
        },
    )

    # Disparo automático de CU09 y CU10
    generar_contrato(credito.pk)
    generar_cronograma_frances(credito.pk)

    solicitud.estado = SolicitudCredito.Estado.APROBADA
    solicitud.motivo_rechazo = None
    solicitud.save(update_fields=["estado", "motivo_rechazo"])

    Auditoria.objects.create(
        usuario=usuario,
        operacion="APROBAR_CREDITO",
        entidad="CREDITO",
        id_entidad=credito.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return credito


@transaction.atomic
def rechazar_solicitud_credito(
    solicitud_id: int, motivo_rechazo: str, usuario: Optional[Usuario] = None
) -> SolicitudCredito:
    """
    CU08 / RF09 / RN11: Rechaza la solicitud registrando obligatoriamente el motivo formal.
    """
    motivo = (motivo_rechazo or "").strip()
    if not motivo:
        raise ValidationError("RN11: Debe registrar de forma obligatoria el motivo formal del rechazo.")

    solicitud = SolicitudCredito.objects.select_for_update().get(pk=solicitud_id)
    solicitud.estado = SolicitudCredito.Estado.RECHAZADA
    solicitud.motivo_rechazo = motivo
    solicitud.save(update_fields=["estado", "motivo_rechazo"])

    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        operacion="RECHAZAR_SOLICITUD",
        entidad="SOLICITUD_CREDITO",
        id_entidad=solicitud.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return solicitud


@transaction.atomic
def firmar_contrato_credito(credito_id: int, usuario: Optional[Usuario] = None) -> Contrato:
    """
    Formaliza la firma del contrato (RN05) previo al desembolso.
    """
    credito = Credito.objects.get(pk=credito_id)
    contrato = getattr(credito, "contrato", None) or generar_contrato(credito.pk)
    contrato.estado = Contrato.Estado.FIRMADO
    contrato.save(update_fields=["estado"])

    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        operacion="FIRMAR_CONTRATO",
        entidad="CONTRATO",
        id_entidad=contrato.pk,
        resultado=Auditoria.Resultado.EXITOSO,
    )
    return contrato


@transaction.atomic
def desembolsar_credito(
    credito_id: int, cuenta_destino: str = "", usuario: Optional[Usuario] = None
) -> dict[str, Any]:
    """
    CU11 / RF12: Valida formalización del contrato (RN05), solicita acreditación al Core Bancario
    simulado y transiciona el crédito a VIGENTE.
    """
    credito = Credito.objects.select_for_update().get(pk=credito_id)

    if credito.estado != Credito.Estado.APROBADO:
        raise ValidationError(f"El crédito {credito.numero_credito} no está en estado APROBADO.")

    contrato = getattr(credito, "contrato", None)
    if not contrato:
        contrato = generar_contrato(credito.pk)

    # Si no estaba firmado, se suscribe en el acto de formalización o exige firma
    if contrato.estado != Contrato.Estado.FIRMADO:
        contrato.estado = Contrato.Estado.FIRMADO
        contrato.save(update_fields=["estado"])

    if not credito.cuotas.exists():
        generar_cronograma_frances(credito.pk)

    respuesta_core = ServicioCoreBancario.procesar_desembolso(
        numero_credito=credito.numero_credito,
        cuenta_destino=cuenta_destino.strip() or f"CTA-{credito.solicitud.cliente.ci.split()[0]}",
        monto=credito.monto_aprobado,
    )

    if respuesta_core.get("exito"):
        credito.fecha_desembolso = timezone.now()
        credito.estado = Credito.Estado.VIGENTE
        credito.save(update_fields=["fecha_desembolso", "estado"])

        Auditoria.objects.create(
            usuario=usuario if usuario and usuario.is_authenticated else None,
            operacion="DESEMBOLSAR_CREDITO",
            entidad="CREDITO",
            id_entidad=credito.pk,
            resultado=Auditoria.Resultado.EXITOSO,
        )

    return respuesta_core


def generar_reporte_cartera(estado_filtro: str = "") -> dict[str, Any]:
    """
    CU14 / RF15: Consolida métricas de cartera total, colocada, saldos y mora.
    """
    qs = Credito.objects.select_related("solicitud__cliente", "contrato").order_by("-id")
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)

    todos = Credito.objects.all()
    total_colocado = todos.aggregate(s=Sum("monto_aprobado"))["s"] or Decimal("0.00")
    saldo_activo = (
        todos.filter(estado__in=["VIGENTE", "EN_MORA"]).aggregate(s=Sum("saldo_capital"))["s"]
        or Decimal("0.00")
    )
    saldo_mora = (
        todos.filter(estado="EN_MORA").aggregate(s=Sum("saldo_capital"))["s"]
        or Decimal("0.00")
    )
    total_recaudado = Pago.objects.aggregate(s=Sum("monto"))["s"] or Decimal("0.00")

    tasa_morosidad = Decimal("0.00")
    if saldo_activo > Decimal("0.00"):
        tasa_morosidad = _round((saldo_mora / saldo_activo) * Decimal("100.00"))

    conteo_estados = {
        "APROBADO": todos.filter(estado="APROBADO").count(),
        "VIGENTE": todos.filter(estado="VIGENTE").count(),
        "EN_MORA": todos.filter(estado="EN_MORA").count(),
        "CANCELADO": todos.filter(estado="CANCELADO").count(),
    }

    cuotas_vencidas = (
        Cuota.objects.filter(estado="VENCIDA")
        .select_related("credito__solicitud__cliente")
        .order_by("fecha_vencimiento")[:15]
    )

    return {
        "creditos": qs,
        "total_creditos": todos.count(),
        "total_colocado": total_colocado,
        "saldo_activo": saldo_activo,
        "saldo_mora": saldo_mora,
        "total_recaudado": total_recaudado,
        "tasa_morosidad": tasa_morosidad,
        "conteo_estados": conteo_estados,
        "cuotas_vencidas": cuotas_vencidas,
    }

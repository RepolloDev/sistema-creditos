import random
import uuid
from decimal import Decimal
from typing import Any

from .models import RegistroRiesgoExterno, TransaccionCoreBancario


class ServicioRiesgoExterno:
    """
    Simulador de cliente para el Buró de Información Crediticia / Sistema de Riesgo.
    Implementa CU03 / RF04 / RNF09.
    """

    @classmethod
    def consultar_antecedentes(
        cls, ci: str, nombres: str = "", apellidos: str = ""
    ) -> dict[str, Any]:
        """
        Consulta antecedentes crediticios por CI.
        Si la persona no existe en la base del buró simulado, se autogenera un perfil realista.
        """
        registro, created = RegistroRiesgoExterno.objects.get_or_create(
            ci=ci.strip(),
            defaults={
                "nombres": nombres or "Solicitante",
                "apellidos": apellidos or "Referencia",
                "score_crediticio": random.randint(620, 800),
                "calificacion_riesgo": RegistroRiesgoExterno.CalificacionRiesgo.BAJO,
                "deuda_sistema_financiero": Decimal("0.00"),
                "entidades_reportantes": 0,
                "tiene_mora_historica": False,
                "detalle_antecedentes": "Historial crediticio limpio sin incidencias.",
            },
        )

        return {
            "ci": registro.ci,
            "score": registro.score_crediticio,
            "nivel_riesgo": registro.calificacion_riesgo,
            "deuda_vigente": registro.deuda_sistema_financiero,
            "entidades_deuda": registro.entidades_reportantes,
            "tiene_mora": registro.tiene_mora_historica,
            "observaciones": registro.detalle_antecedentes,
            "es_favorable": registro.calificacion_riesgo
            != RegistroRiesgoExterno.CalificacionRiesgo.ALTO,
        }


class ServicioCoreBancario:
    """
    Simulador de interfaz con el Core Bancario para la dispersión de fondos.
    Implementa CU11 / RF12 / RNF09.
    """

    @classmethod
    def procesar_desembolso(
        cls, numero_credito: str, cuenta_destino: str, monto: Decimal
    ) -> dict[str, Any]:
        """
        Envía la instrucción de acreditación de fondos al Core Bancario simulado.
        Retorna la confirmación formal con referencia bancaria única.
        """
        referencia = f"CORE-{uuid.uuid4().hex[:10].upper()}"
        autorizacion = f"AUTH-{random.randint(100000, 999999)}"

        transaccion = TransaccionCoreBancario.objects.create(
            referencia_transaccion=referencia,
            numero_credito=numero_credito,
            cuenta_destino=cuenta_destino or f"CTA-{random.randint(1000000, 9999999)}",
            monto=monto,
            estado=TransaccionCoreBancario.EstadoTransaccion.EXITOSA,
            codigo_autorizacion=autorizacion,
            mensaje_respuesta="Acreditación de fondos realizada satisfactoriamente.",
        )

        return {
            "exito": True,
            "referencia": transaccion.referencia_transaccion,
            "codigo_autorizacion": transaccion.codigo_autorizacion,
            "monto": transaccion.monto,
            "fecha": transaccion.fecha_procesamiento,
            "mensaje": transaccion.mensaje_respuesta,
        }

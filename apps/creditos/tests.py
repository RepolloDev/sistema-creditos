from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from usuarios.models import Usuario, Auditoria
from clientes.models import Cliente
from solicitudes.models import SolicitudCredito, Garantia
from evaluacion.models import EvaluacionCredito
from creditos.models import Credito, Cuota, Contrato
from pagos.models import Pago
from integraciones.models import TransaccionCoreBancario


class FlujoIntegralSistemaCreditosTest(TestCase):
    """Pruebas de integración de extremo a extremo para todos los módulos del sistema."""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            login="admin_test",
            password="Password123!",
            nombre_completo="Carlos Mendoza",
            rol=Usuario.Rol.ADMINISTRADOR,
            activo=True,
        )
        self.client.force_login(self.admin)

    def test_ciclo_completo_credito_vistas_y_servicios(self):
        # 1. Dashboard y Auditoría
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("usuarios:auditoria_list"))
        self.assertEqual(resp.status_code, 200)

        # 2. Crear Cliente
        resp = self.client.post(
            reverse("clientes:crear"),
            {
                "ci": "4829104 LP",
                "nombres": "Roberto",
                "apellidos": "Guzmán Rojas",
                "telefono": "70192834",
                "direccion": "Av. 16 de Julio N° 1490",
                "email": "rguzman@correo.bo",
                "ingresos_mensuales": "12000.00",
            },
        )
        self.assertEqual(resp.status_code, 302)
        cliente = Cliente.objects.get(ci="4829104 LP")

        # Vistas de Cliente (listado, detalle, editar) verificando contenido renderizado
        resp_list = self.client.get(reverse("clientes:listado"))
        self.assertContains(resp_list, "Guzmán Rojas, Roberto")
        self.assertContains(resp_list, "+ Nuevo Cliente")
        resp_det = self.client.get(reverse("clientes:detalle", args=[cliente.pk]))
        self.assertContains(resp_det, "Ficha de Identificación")
        self.assertEqual(self.client.get(reverse("clientes:editar", args=[cliente.pk])).status_code, 200)

        # 3. Crear Solicitud de Crédito
        resp = self.client.post(
            reverse("solicitudes:crear"),
            {
                "cliente": cliente.pk,
                "monto_solicitado": "24000.00",
                "plazo_meses": 12,
                "destino": "Capital de Operaciones Comerciales",
            },
        )
        self.assertEqual(resp.status_code, 302)
        solicitud = SolicitudCredito.objects.get(cliente=cliente)
        self.assertEqual(solicitud.estado, SolicitudCredito.Estado.REGISTRADA)

        # Registrar Garantía
        resp = self.client.post(
            reverse("solicitudes:garantia_crear", args=[solicitud.pk]),
            {
                "tipo": Garantia.Tipo.HIPOTECARIA,
                "descripcion": "Inmueble Comercial Zona Sopocachi",
                "valor": "65000.00",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(solicitud.garantias.count(), 1)
        self.assertEqual(self.client.get(reverse("solicitudes:listado")).status_code, 200)
        self.assertEqual(self.client.get(reverse("solicitudes:detalle", args=[solicitud.pk])).status_code, 200)

        # 4. Evaluación Crediticia y Consulta a Central de Riesgos
        self.assertEqual(self.client.get(reverse("evaluacion:listado")).status_code, 200)
        self.assertEqual(self.client.get(f"{reverse('evaluacion:crear')}?solicitud_id={solicitud.pk}").status_code, 200)

        resp = self.client.post(
            reverse("evaluacion:crear"),
            {
                "solicitud": solicitud.pk,
                "ingresos": "12000.00",
                "gastos": "4500.00",
                "nivel_riesgo": EvaluacionCredito.NivelRiesgo.BAJO,
                "resultado": EvaluacionCredito.Resultado.FAVORABLE,
                "observaciones": "Cliente solvente con respaldo hipotecario",
            },
        )
        self.assertEqual(resp.status_code, 302)
        evaluacion = EvaluacionCredito.objects.get(solicitud=solicitud)
        self.assertEqual(evaluacion.capacidad_pago, Decimal("7500.00"))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCredito.Estado.EN_EVALUACION)

        self.assertEqual(self.client.get(reverse("evaluacion:detalle", args=[evaluacion.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("evaluacion:consultar_riesgo", args=[evaluacion.pk])).status_code, 302)

        # 5. Aprobación del Crédito y Generación de Cronograma Francés + Contrato
        self.assertEqual(self.client.get(reverse("creditos:aprobar", args=[solicitud.pk])).status_code, 200)
        resp = self.client.post(
            reverse("creditos:aprobar", args=[solicitud.pk]),
            {
                "monto_aprobado": "24000.00",
                "tasa_interes_anual": "18.00",
                "plazo_meses": 12,
            },
        )
        self.assertEqual(resp.status_code, 302)
        credito = Credito.objects.get(solicitud=solicitud)
        self.assertEqual(credito.estado, Credito.Estado.APROBADO)
        self.assertEqual(credito.cuotas.count(), 12)
        self.assertTrue(hasattr(credito, "contrato"))

        # Verificar que la suma de capital de las 12 cuotas sea exactamente el monto aprobado
        suma_capital = sum(c.capital for c in credito.cuotas.all())
        self.assertEqual(suma_capital, Decimal("24000.00"))

        # 6. Firma de Contrato y Desembolso en Core Bancario
        resp = self.client.post(reverse("creditos:firmar_contrato", args=[credito.pk]))
        self.assertEqual(resp.status_code, 302)
        credito.contrato.refresh_from_db()
        self.assertEqual(credito.contrato.estado, Contrato.Estado.FIRMADO)

        resp = self.client.post(
            reverse("creditos:desembolsar", args=[credito.pk]),
            {"cuenta_destino": "VK-CTA-4829104"},
        )
        self.assertEqual(resp.status_code, 302)
        credito.refresh_from_db()
        self.assertEqual(credito.estado, Credito.Estado.VIGENTE)
        self.assertEqual(
            TransaccionCoreBancario.objects.filter(
                numero_credito=credito.numero_credito
            ).count(),
            1,
        )

        # Vistas de Crédito (listado, detalle, cronograma, reportes)
        self.assertEqual(self.client.get(reverse("creditos:listado")).status_code, 200)
        self.assertEqual(self.client.get(reverse("creditos:detalle", args=[credito.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("creditos:cronograma", args=[credito.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("creditos:reportes")).status_code, 200)

        # 7. Simular Mora en Primera Cuota y Ejecutar Barrido de Control de Mora
        cuota_1 = credito.cuotas.get(numero_cuota=1)
        cuota_1.fecha_vencimiento = date.today() - timedelta(days=15)
        cuota_1.save(update_fields=["fecha_vencimiento"])

        resp = self.client.post(reverse("pagos:control_mora"))
        self.assertEqual(resp.status_code, 302)
        cuota_1.refresh_from_db()
        credito.refresh_from_db()
        self.assertEqual(cuota_1.estado, Cuota.Estado.VENCIDA)
        self.assertEqual(credito.estado, Credito.Estado.EN_MORA)
        self.assertEqual(self.client.get(reverse("pagos:control_mora")).status_code, 200)

        # 8. Cobrar Cuota en Ventanilla
        self.assertEqual(self.client.get(f"{reverse('pagos:registrar')}?credito_id={credito.pk}").status_code, 200)
        resp = self.client.post(
            reverse("pagos:registrar"),
            {
                "cuota": cuota_1.pk,
                "monto": str(cuota_1.monto_cuota),
                "forma_pago": Pago.FormaPago.EFECTIVO,
            },
        )
        self.assertEqual(resp.status_code, 302)
        pago = Pago.objects.get(cuota=cuota_1)
        cuota_1.refresh_from_db()
        credito.refresh_from_db()
        self.assertEqual(cuota_1.estado, Cuota.Estado.PAGADA)
        self.assertEqual(credito.estado, Credito.Estado.VIGENTE)
        self.assertEqual(credito.saldo_capital, Decimal("24000.00") - cuota_1.capital)

        # Vistas de Pagos (listado, comprobante)
        self.assertEqual(self.client.get(reverse("pagos:listado")).status_code, 200)
        self.assertEqual(self.client.get(reverse("pagos:comprobante", args=[pago.pk])).status_code, 200)

        # 9. Probar Reversión/Eliminación de Pago (Modo MVP)
        resp = self.client.post(reverse("pagos:eliminar", args=[pago.pk]))
        self.assertEqual(resp.status_code, 302)
        cuota_1.refresh_from_db()
        credito.refresh_from_db()
        self.assertEqual(cuota_1.estado, Cuota.Estado.VENCIDA)
        self.assertEqual(credito.saldo_capital, Decimal("24000.00"))

        # Verificar que las acciones quedaron registradas en la bitácora de auditoría
        self.assertTrue(Auditoria.objects.count() >= 6)

    def test_flujo_rechazo_y_eliminaciones_mvp(self):
        cliente = Cliente.objects.create(
            ci="9988776 SC",
            nombres="Elena",
            apellidos="Vargas",
            telefono="71234567",
            direccion="Calle Bolívar #100",
            ingresos_mensuales=Decimal("8000.00"),
        )
        solicitud = SolicitudCredito.objects.create(
            cliente=cliente,
            monto_solicitado=Decimal("15000.00"),
            plazo_meses=6,
            destino="Compra de Maquinaria",
        )
        garantia = Garantia.objects.create(
            solicitud=solicitud,
            tipo=Garantia.Tipo.PRENDARIA,
            descripcion="Maquinaria Industrial",
            valor=Decimal("20000.00"),
        )
        evaluacion = EvaluacionCredito.objects.create(
            solicitud=solicitud,
            ingresos=Decimal("8000.00"),
            gastos=Decimal("3000.00"),
            capacidad_pago=Decimal("5000.00"),
            nivel_riesgo=EvaluacionCredito.NivelRiesgo.MEDIO,
            resultado=EvaluacionCredito.Resultado.FAVORABLE,
        )

        # Probar vista GET y POST de Rechazo (CU08 / RN11)
        self.assertEqual(self.client.get(reverse("creditos:rechazar", args=[solicitud.pk])).status_code, 200)
        resp = self.client.post(
            reverse("creditos:rechazar", args=[solicitud.pk]),
            {"motivo_rechazo": "Sobreendeudamiento detectado en comité."},
        )
        self.assertEqual(resp.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudCredito.Estado.RECHAZADA)

        # Probar confirmación GET y eliminación POST de Evaluación, Garantía, Solicitud y Cliente
        self.assertEqual(self.client.get(reverse("evaluacion:eliminar", args=[evaluacion.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("evaluacion:eliminar", args=[evaluacion.pk])).status_code, 302)

        self.assertEqual(self.client.post(reverse("solicitudes:garantia_eliminar", args=[garantia.pk])).status_code, 302)

        self.assertEqual(self.client.get(reverse("solicitudes:eliminar", args=[solicitud.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("solicitudes:eliminar", args=[solicitud.pk])).status_code, 302)

        self.assertEqual(self.client.get(reverse("clientes:eliminar", args=[cliente.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("clientes:eliminar", args=[cliente.pk])).status_code, 302)
        self.assertFalse(Cliente.objects.filter(pk=cliente.pk).exists())


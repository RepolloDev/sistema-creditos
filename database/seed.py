"""
Script avanzado para poblar la base de datos con datos realistas para pruebas.
Genera:
- 17 Usuarios de prueba cubriendo todos los roles bancarios.
- 25 Clientes con registros en el Buró de Riesgo Externo.
- 45 Préstamos en diversos estados (Aprobado, Vigente, En Mora, Cancelado).
- 10 Solicitudes adicionales (En evaluación, Rechazadas con motivo).
- Cronogramas de cuotas bajo amortización fija (Sistema Francés).
- Pagos aplicados y comprobantes de ventanilla.
- Transacciones del Core Bancario simulado.

Ejecución:
    uv run python database/seed.py
    o
    uv run task seed
"""

import os
import random
import sys
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

# Configurar rutas y entorno Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from clientes.models import Cliente
from creditos.models import Contrato, Credito, Cuota
from django.contrib.auth import get_user_model
from django.utils import timezone
from evaluacion.models import EvaluacionCredito
from integraciones.models import RegistroRiesgoExterno, TransaccionCoreBancario
from pagos.models import Pago
from solicitudes.models import Garantia, SolicitudCredito

Usuario = get_user_model()


def round_cur(val) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_cuota_francesa(
    monto: Decimal, tasa_anual: Decimal, meses: int
) -> tuple[Decimal, list[dict]]:
    """
    Calcula cronograma de amortización francesa exacta (Sección 10.1.2).
    """
    im = Decimal(tasa_anual) / Decimal(12 * 100)
    p = Decimal(monto)
    n = int(meses)

    factor = (Decimal(1) + im) ** n
    cuota_fija = p * (im * factor) / (factor - Decimal(1))
    cuota_fija = round_cur(cuota_fija)

    saldo = p
    cronograma = []
    hoy = date.today()

    for k in range(1, n + 1):
        interes = round_cur(saldo * im)
        if k == n:
            capital = saldo
            cuota_periodo = round_cur(capital + interes)
            saldo = Decimal("0.00")
        else:
            capital = round_cur(cuota_fija - interes)
            saldo = round_cur(saldo - capital)
            cuota_periodo = cuota_fija

        vencimiento = hoy + timedelta(
            days=30 * (k - 1) - 60
        )  # Fechas escalonadas para probar mora/pasados

        cronograma.append(
            {
                "numero_cuota": k,
                "fecha_vencimiento": vencimiento,
                "capital": capital,
                "interes": interes,
                "monto_cuota": cuota_periodo,
                "saldo_cuota": cuota_periodo,
            }
        )

    return cuota_fija, cronograma


def seed_usuarios():
    print("--- [1/5] Creando usuarios bancarios por rol ---")
    usuarios_data = [
        # Administrador
        ("admin", "Administrador Central", Usuario.Rol.ADMINISTRADOR, "admin123", True),
        # Oficiales de Crédito (al menos 4)
        ("oficial1", "Carlos Mendoza Flores", Usuario.Rol.OFICIAL, "oficial123", False),
        ("oficial2", "Mariana Rios Gutierrez", Usuario.Rol.OFICIAL, "oficial123", False),
        ("oficial3", "Gustavo Paredes Luna", Usuario.Rol.OFICIAL, "oficial123", False),
        ("oficial4", "Elena Choque Fernandez", Usuario.Rol.OFICIAL, "oficial123", False),
        # Cajeros (al menos 5)
        ("cajero1", "Valeria Rojas Suarez", Usuario.Rol.CAJERO, "cajero123", False),
        ("cajero2", "Roberto Quispe Mamani", Usuario.Rol.CAJERO, "cajero123", False),
        ("cajero3", "Daniela Vargas Pinto", Usuario.Rol.CAJERO, "cajero123", False),
        ("cajero4", "Jorge Lopez Arratia", Usuario.Rol.CAJERO, "cajero123", False),
        ("cajero5", "Sonia Condori Laura", Usuario.Rol.CAJERO, "cajero123", False),
        # Analistas de Crédito (3)
        ("analista1", "Fernando Morales Silva", Usuario.Rol.ANALISTA, "analista123", False),
        ("analista2", "Lucia Benitez Aliaga", Usuario.Rol.ANALISTA, "analista123", False),
        ("analista3", "Andres Guzman Teran", Usuario.Rol.ANALISTA, "analista123", False),
        # Jefes de Créditos (2)
        ("jefe1", "Dr. Victor Hugo Banzer", Usuario.Rol.JEFE, "jefe123", False),
        ("jefe2", "Lic. Patricia Miranda Soliz", Usuario.Rol.JEFE, "jefe123", False),
        # Gerentes (2)
        ("gerente1", "Ing. Mauricio Del Carpio", Usuario.Rol.GERENTE, "gerente123", False),
        ("gerente2", "Lic. Claudia Villarroel Paz", Usuario.Rol.GERENTE, "gerente123", False),
    ]

    creados = 0
    for login, nombre, rol, password, is_super in usuarios_data:
        user, created = Usuario.objects.get_or_create(
            login=login,
            defaults={
                "nombre_completo": nombre,
                "rol": rol,
                "is_staff": is_super,
                "is_superuser": is_super,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            creados += 1

    print(f"  -> Usuarios listos: {len(usuarios_data)} (Nuevos: {creados})")


def seed_clientes():
    print("--- [2/5] Creando 25 Clientes y registros de Buró de Riesgo ---")
    datos_clientes = [
        (
            "4892301",
            "Alejandro",
            "Suarez Beltran",
            "71542100",
            "Av. Arce #1420, La Paz",
            Decimal("8500.00"),
            760,
            "BAJO",
        ),
        (
            "5921843",
            "Beatriz",
            "Mamani Condori",
            "68124930",
            "Calle Murillo #850, El Alto",
            Decimal("4200.00"),
            680,
            "MEDIO",
        ),
        (
            "6819204",
            "Carlos",
            "Quisbert Poma",
            "72091444",
            "Zona Villa Fatima #302, La Paz",
            Decimal("6100.00"),
            710,
            "BAJO",
        ),
        (
            "7102948",
            "Daniela",
            "Torres Zeballos",
            "76501928",
            "Av. Ballivian #510, Calacoto",
            Decimal("14500.00"),
            810,
            "BAJO",
        ),
        (
            "3910294",
            "Eduardo",
            "Flores Alarcon",
            "73019283",
            "Calle Comercio #210, Oruro",
            Decimal("5300.00"),
            640,
            "MEDIO",
        ),
        (
            "8291048",
            "Fabiola",
            "Guzman Ortiz",
            "69018274",
            "Av. America #740, Cochabamba",
            Decimal("9800.00"),
            740,
            "BAJO",
        ),
        (
            "9018273",
            "Gabriel",
            "Roca Mercado",
            "77182903",
            "Equipetrol Calle 4, Santa Cruz",
            Decimal("22000.00"),
            820,
            "BAJO",
        ),
        (
            "4192830",
            "Helena",
            "Vaca Diez",
            "78291029",
            "Barrio Sirari #120, Santa Cruz",
            Decimal("12500.00"),
            730,
            "BAJO",
        ),
        (
            "5182904",
            "Ignacio",
            "Callejas Bravo",
            "67102938",
            "Calle Sucre #405, Potosi",
            Decimal("3800.00"),
            580,
            "ALTO",
        ),
        (
            "6271920",
            "Jimena",
            "Pardo Salinas",
            "71928374",
            "Av. Hernando Siles #920, Obrajes",
            Decimal("11000.00"),
            780,
            "BAJO",
        ),
        (
            "7381920",
            "Kevin",
            "Aruquipa Chuquimia",
            "72819203",
            "Av. 16 de Julio #450, El Alto",
            Decimal("4900.00"),
            660,
            "MEDIO",
        ),
        (
            "8491029",
            "Lorena",
            "Salguero Tapia",
            "68910293",
            "Calle Junin #180, Sucre",
            Decimal("7200.00"),
            720,
            "BAJO",
        ),
        (
            "9501829",
            "Marcelo",
            "Zambrana Ledezma",
            "77819203",
            "Av. Heroinas #620, Cochabamba",
            Decimal("16500.00"),
            800,
            "BAJO",
        ),
        (
            "3819201",
            "Natalia",
            "Chavez Justiniano",
            "75019283",
            "Calle Monseñor Rivero #310, Santa Cruz",
            Decimal("18000.00"),
            790,
            "BAJO",
        ),
        (
            "4920193",
            "Oscar",
            "Ticona Huanca",
            "69102938",
            "Zona 12 de Octubre #110, El Alto",
            Decimal("3500.00"),
            540,
            "ALTO",
        ),
        (
            "5039281",
            "Pamela",
            "Rios Barrientos",
            "73819204",
            "Av. Camacho #1240, La Paz",
            Decimal("9200.00"),
            750,
            "BAJO",
        ),
        (
            "6149204",
            "Rodrigo",
            "Camacho Paz",
            "71029384",
            "Calle Espana #530, Cochabamba",
            Decimal("8800.00"),
            730,
            "BAJO",
        ),
        (
            "7259102",
            "Silvia",
            "Villalba Morales",
            "68291029",
            "Calle Loayza #202, La Paz",
            Decimal("6700.00"),
            700,
            "BAJO",
        ),
        (
            "8369102",
            "Tomas",
            "Arce Villarroel",
            "76102938",
            "Calle Arenales #140, Santa Cruz",
            Decimal("13400.00"),
            770,
            "BAJO",
        ),
        (
            "9479201",
            "Ursula",
            "Medina Castro",
            "77291029",
            "Av. Salamanca #820, Cochabamba",
            Decimal("5900.00"),
            650,
            "MEDIO",
        ),
        (
            "3589201",
            "Victor",
            "Maldonado Claros",
            "74019283",
            "Av. 6 de Agosto #2400, La Paz",
            Decimal("15000.00"),
            810,
            "BAJO",
        ),
        (
            "4699201",
            "Wendy",
            "Cardona Pinto",
            "69291029",
            "Zona Sopocachi #415, La Paz",
            Decimal("7800.00"),
            720,
            "BAJO",
        ),
        (
            "5709201",
            "Xavier",
            "Borda Caceres",
            "71102938",
            "Calle Bolivar #320, Tarija",
            Decimal("6400.00"),
            670,
            "MEDIO",
        ),
        (
            "6819202",
            "Yolanda",
            "Peñaranda Soliz",
            "68391029",
            "Av. Las Americas #100, Tarija",
            Decimal("8100.00"),
            740,
            "BAJO",
        ),
        (
            "7929201",
            "Zulma",
            "Colque Yana",
            "76201928",
            "Calle Cochabamba #205, Oruro",
            Decimal("4500.00"),
            630,
            "MEDIO",
        ),
    ]

    clientes_list = []
    for ci, nom, ape, tel, dir_, ing, score, calif in datos_clientes:
        cli, _ = Cliente.objects.get_or_create(
            ci=ci,
            defaults={
                "nombres": nom,
                "apellidos": ape,
                "telefono": tel,
                "direccion": dir_,
                "ingresos_mensuales": ing,
            },
        )
        clientes_list.append(cli)

        # Poblar buró simulado
        RegistroRiesgoExterno.objects.get_or_create(
            ci=ci,
            defaults={
                "nombres": nom,
                "apellidos": ape,
                "score_crediticio": score,
                "calificacion_riesgo": calif,
                "deuda_sistema_financiero": Decimal("0.00")
                if calif == "BAJO"
                else Decimal("12000.00"),
                "entidades_reportantes": 0 if calif == "BAJO" else 2,
                "tiene_mora_historica": (calif == "ALTO"),
                "detalle_antecedentes": f"Calificación {calif}. Score crediticio buró: {score}/850.",
            },
        )

    print(f"  -> Clientes y registros de Buró listos: {len(clientes_list)}")
    return clientes_list


def seed_solicitudes_y_prestamos(clientes):
    print("--- [3/5] Generando 45 Préstamos y 10 Solicitudes de prueba ---")
    destinos = [
        "Capital de trabajo para microempresa",
        "Compra de maquinaria y equipamiento",
        "Refacción y ampliación de vivienda",
        "Consumo familiar y estudios superiores",
        "Adquisición de vehículo comercial",
    ]

    tipos_garantia = [
        (Garantia.Tipo.PERSONAL, "Garante solidario con boleta de pago formal"),
        (Garantia.Tipo.PRENDARIA, "Maquinaria industrial con registro de propiedad"),
        (Garantia.Tipo.HIPOTECARIA, "Inmueble urbano registrado en Derechos Reales"),
    ]

    # Estados de los 45 créditos a generar:
    # 10 Aprobados (pendientes desembolso)
    # 15 Vigentes (con pagos al día)
    # 10 En Mora (con cuotas vencidas)
    # 10 Cancelados (saldo 0)
    estados_credito = (
        [Credito.Estado.APROBADO] * 10
        + [Credito.Estado.VIGENTE] * 15
        + [Credito.Estado.EN_MORA] * 10
        + [Credito.Estado.CANCELADO] * 10
    )

    tasa_anual = Decimal("14.50")
    total_prestamos = 0

    for idx, estado_cred in enumerate(estados_credito, start=1):
        cliente = clientes[(idx - 1) % len(clientes)]
        monto = Decimal(random.choice([15000, 25000, 35000, 50000, 75000, 100000]))
        plazo = random.choice([6, 12, 18, 24])

        # 1. Crear Solicitud
        solicitud, _ = SolicitudCredito.objects.get_or_create(
            cliente=cliente,
            destino=f"{random.choice(destinos)} (Ref #{idx:03d})",
            defaults={
                "monto_solicitado": monto,
                "plazo_meses": plazo,
                "estado": SolicitudCredito.Estado.APROBADA,
            },
        )

        # 2. Registrar Garantía
        tipo_g, desc_g = random.choice(tipos_garantia)
        Garantia.objects.get_or_create(
            solicitud=solicitud,
            defaults={
                "tipo": tipo_g,
                "descripcion": desc_g,
                "valor": round_cur(monto * Decimal("1.30")),
                "estado": Garantia.Estado.REGISTRADA,
            },
        )

        # 3. Registrar Evaluación Técnica Favorable
        ingresos_cli = cliente.ingresos_mensuales
        gastos_cli = round_cur(ingresos_cli * Decimal("0.45"))
        cap_pago = round_cur(ingresos_cli - gastos_cli)
        EvaluacionCredito.objects.get_or_create(
            solicitud=solicitud,
            defaults={
                "ingresos": ingresos_cli,
                "gastos": gastos_cli,
                "capacidad_pago": cap_pago,
                "nivel_riesgo": EvaluacionCredito.NivelRiesgo.BAJO,
                "resultado": EvaluacionCredito.Resultado.FAVORABLE,
                "observaciones": "Capacidad de pago suficiente y margen crediticio verificado.",
            },
        )

        # 4. Crear Crédito
        num_credito = f"CRE-2026-{idx:04d}"
        cuota_fija, cronograma = calcular_cuota_francesa(monto, tasa_anual, plazo)

        credito, _ = Credito.objects.get_or_create(
            numero_credito=num_credito,
            defaults={
                "solicitud": solicitud,
                "monto_aprobado": monto,
                "tasa_interes": tasa_anual,
                "plazo_meses": plazo,
                "saldo_capital": monto
                if estado_cred != Credito.Estado.CANCELADO
                else Decimal("0.00"),
                "estado": estado_cred,
                "fecha_desembolso": timezone.now()
                if estado_cred != Credito.Estado.APROBADO
                else None,
            },
        )

        # 5. Generar Contrato
        Contrato.objects.get_or_create(
            credito=credito,
            defaults={
                "numero_contrato": f"CTR-2026-{idx:04d}",
                "estado": Contrato.Estado.FIRMADO
                if estado_cred != Credito.Estado.APROBADO
                else Contrato.Estado.GENERADO,
            },
        )

        # 6. Registrar Cuotas
        cuotas_objs = []
        for c_data in cronograma:
            cuota, _ = Cuota.objects.get_or_create(
                credito=credito,
                numero_cuota=c_data["numero_cuota"],
                defaults={
                    "fecha_vencimiento": c_data["fecha_vencimiento"],
                    "capital": c_data["capital"],
                    "interes": c_data["interes"],
                    "monto_cuota": c_data["monto_cuota"],
                    "saldo_cuota": c_data["saldo_cuota"],
                    "estado": Cuota.Estado.PENDIENTE,
                },
            )
            cuotas_objs.append(cuota)

        # 7. Desembolso simulado Core Bancario para créditos vigentes, en mora o cancelados
        if estado_cred != Credito.Estado.APROBADO:
            TransaccionCoreBancario.objects.get_or_create(
                numero_credito=credito.numero_credito,
                defaults={
                    "referencia_transaccion": f"TXB-2026-{idx:05d}",
                    "cuenta_destino": f"CTA-{random.randint(1000000, 9999999)}",
                    "monto": credito.monto_aprobado,
                    "estado": TransaccionCoreBancario.EstadoTransaccion.EXITOSA,
                    "codigo_autorizacion": f"AUTH-{random.randint(100000, 999999)}",
                    "mensaje_respuesta": "Desembolso acreditado en cuenta bancaria del titular.",
                },
            )

        # 8. Generar Pagos según el estado del crédito
        if estado_cred == Credito.Estado.CANCELADO:
            # Todas las cuotas pagadas
            for c_obj in cuotas_objs:
                c_obj.saldo_cuota = Decimal("0.00")
                c_obj.estado = Cuota.Estado.PAGADA
                c_obj.save()
                Pago.objects.get_or_create(
                    cuota=c_obj,
                    defaults={
                        "monto": c_obj.monto_cuota,
                        "forma_pago": Pago.FormaPago.EFECTIVO,
                        "numero_recibo": f"REC-CAN-{c_obj.id:06d}",
                    },
                )
        elif estado_cred == Credito.Estado.VIGENTE:
            # 1 o 2 cuotas pagadas
            for c_obj in cuotas_objs[:2]:
                c_obj.saldo_cuota = Decimal("0.00")
                c_obj.estado = Cuota.Estado.PAGADA
                c_obj.save()
                Pago.objects.get_or_create(
                    cuota=c_obj,
                    defaults={
                        "monto": c_obj.monto_cuota,
                        "forma_pago": Pago.FormaPago.DEPOSITO,
                        "numero_recibo": f"REC-VIG-{c_obj.id:06d}",
                    },
                )
            # Reducir saldo capital proporcional
            credito.saldo_capital = round_cur(credito.monto_aprobado * Decimal("0.75"))
            credito.save()
        elif estado_cred == Credito.Estado.EN_MORA:
            # Cuotas vencidas sin pagar
            for c_obj in cuotas_objs[:2]:
                c_obj.estado = Cuota.Estado.VENCIDA
                c_obj.save()

        total_prestamos += 1

    # Generar 5 solicitudes adicionales en estado EN_EVALUACION
    for i in range(1, 6):
        cliente = clientes[i]
        sol, _ = SolicitudCredito.objects.get_or_create(
            cliente=cliente,
            destino=f"Trámite en evaluación técnica #{i}",
            defaults={
                "monto_solicitado": Decimal(random.choice([20000, 30000, 45000])),
                "plazo_meses": 12,
                "estado": SolicitudCredito.Estado.EN_EVALUACION,
            },
        )
        Garantia.objects.get_or_create(
            solicitud=sol,
            defaults={
                "tipo": Garantia.Tipo.PERSONAL,
                "descripcion": "Garante personal en verificación laboral",
                "valor": Decimal("35000.00"),
            },
        )

    # Generar 5 solicitudes rechazadas con motivo (RN11)
    motivos_rechazo = [
        "Nivel de endeudamiento vigente excede el 40% admisible (RN03/RF05).",
        "Antecedentes crediticios con mora recurrente en buró externo.",
        "Garantía propuesta no cumple con el aforo mínimo requerido.",
        "Ingresos mensuales declarados no fueron sustentados con documentación legal.",
        "Capacidad de pago nula según flujo de ingresos y gastos deducidos.",
    ]
    for i in range(1, 6):
        cliente = clientes[-i]
        SolicitudCredito.objects.get_or_create(
            cliente=cliente,
            destino=f"Trámite denegado de prueba #{i}",
            defaults={
                "monto_solicitado": Decimal(random.choice([60000, 80000, 120000])),
                "plazo_meses": 24,
                "estado": SolicitudCredito.Estado.RECHAZADA,
                "motivo_rechazo": motivos_rechazo[i - 1],
            },
        )

    print(f"  -> Préstamos creados y configurados: {total_prestamos}")
    print("  -> Solicitudes adicionales en evaluación y rechazadas listas.")


def seed_all():
    print("======================================================")
    print("  INICIANDO SEED DE BASE DE DATOS - SISTEMA DE CRÉDITOS")
    print("======================================================")
    seed_usuarios()
    clientes = seed_clientes()
    seed_solicitudes_y_prestamos(clientes)
    print("======================================================")
    print("  SEED COMPLETADO SATISFACTORIAMENTE")
    print("  Total Préstamos: 45 | Clientes: 25 | Usuarios: 17")
    print("======================================================")


if __name__ == "__main__":
    seed_all()

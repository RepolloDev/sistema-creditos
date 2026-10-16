# Usuarios de Prueba y Matrices de Control de Acceso (RBAC)

Este documento detalla las cuentas disponibles en la base de datos de pruebas (`database/seed.py`), la matriz de acceso a módulos/rutas del sistema, la matriz de acciones/casos de uso permitidos por rol y la segmentación del dashboard operativo según el informe del sistema (`docs/informe.md`).

---

## 1. Usuarios Disponibles para Pruebas

Todos los usuarios se encuentran activos y precargados en la base de datos:

| Rol | Usuario (`login`) | Contraseña | Nombre Completo |
| :--- | :--- | :--- | :--- |
| **Administrador** (`ADMINISTRADOR`) | `admin` | `admin123` | Administrador Central |
| **Oficial de Crédito** (`OFICIAL`) | `oficial1` | `oficial123` | Carlos Mendoza Flores |
| **Oficial de Crédito** (`OFICIAL`) | `oficial2` | `oficial123` | Mariana Rios Gutierrez |
| **Oficial de Crédito** (`OFICIAL`) | `oficial3` | `oficial123` | Gustavo Paredes Luna |
| **Oficial de Crédito** (`OFICIAL`) | `oficial4` | `oficial123` | Elena Choque Fernandez |
| **Analista de Crédito** (`ANALISTA`) | `analista1` | `analista123` | Fernando Morales Silva |
| **Analista de Crédito** (`ANALISTA`) | `analista2` | `analista123` | Lucia Benitez Aliaga |
| **Analista de Crédito** (`ANALISTA`) | `analista3` | `analista123` | Andres Guzman Teran |
| **Jefe de Créditos** (`JEFE`) | `jefe1` | `jefe123` | Dr. Victor Hugo Banzer |
| **Jefe de Créditos** (`JEFE`) | `jefe2` | `jefe123` | Lic. Patricia Miranda Soliz |
| **Cajero** (`CAJERO`) | `cajero1` | `cajero123` | Valeria Rojas Suarez |
| **Cajero** (`CAJERO`) | `cajero2` | `cajero123` | Roberto Quispe Mamani |
| **Cajero** (`CAJERO`) | `cajero3` | `cajero123` | Daniela Vargas Pinto |
| **Cajero** (`CAJERO`) | `cajero4` | `cajero123` | Jorge Lopez Arratia |
| **Cajero** (`CAJERO`) | `cajero5` | `cajero123` | Sonia Condori Laura |
| **Gerente** (`GERENTE`) | `gerente1` | `gerente123` | Ing. Mauricio Del Carpio |
| **Gerente** (`GERENTE`) | `gerente2` | `gerente123` | Lic. Claudia Villarroel Paz |

---

## 2. Matriz de Acceso a Módulos y Vistas (Dónde Pueden Acceder)

Indica qué módulos y pantallas puede abrir cada rol en el sistema:

| Módulo / Vista | Ruta (URL) | ADMINISTRADOR | OFICIAL | ANALISTA | JEFE | CAJERO | GERENTE |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Inicio (Resumen Operativo)** | `/` | Sí | Sí | Sí | Sí | Sí | Sí |
| **Clientes — Listado y Detalle** | `/clientes/`, `/clientes/<id>/` | Sí | Sí | Sí | Sí | Sí | Sí |
| **Clientes — Crear / Editar / Eliminar** | `/clientes/nuevo/`, `/clientes/<id>/editar/` | Sí | Sí | No | No | No | No |
| **Solicitudes — Listado y Detalle** | `/solicitudes/`, `/solicitudes/<id>/` | Sí | Sí | Sí | Sí | No | Sí |
| **Solicitudes — Crear Solicitud y Garantía** | `/solicitudes/nueva/`, `/solicitudes/<id>/garantias/nueva/` | Sí | Sí | No | No | No | No |
| **Evaluaciones — Listado y Dictamen** | `/evaluacion/`, `/evaluacion/<id>/` | Sí | No | Sí | Sí | No | Sí |
| **Evaluaciones — Emitir Evaluación y Consultar Buró** | `/evaluacion/nueva/`, `/evaluacion/<id>/consultar-riesgo/` | Sí | No | Sí | No | No | No |
| **Créditos — Cartera, Detalle y Cronograma** | `/creditos/`, `/creditos/<id>/`, `/creditos/<id>/cronograma/` | Sí | Sí | Sí | Sí | Sí | Sí |
| **Créditos — Aprobar / Rechazar Solicitud** | `/creditos/aprobar/<id>/`, `/creditos/rechazar/<id>/` | Sí | No | No | Sí | No | No |
| **Créditos — Reportes de Cartera y Mora** | `/creditos/reportes/` | Sí | No | No | Sí | No | Sí |
| **Pagos — Listado, Recibo y Control de Mora** | `/pagos/`, `/pagos/<id>/comprobante/`, `/pagos/control-mora/` | Sí | No | No | Sí | Sí | Sí |
| **Pagos — Registrar Cobro / Anular Pago** | `/pagos/registrar/`, `/pagos/<id>/eliminar/` | Sí | No | No | No | Sí | No |
| **Usuarios y Bitácora de Auditoría** | `/usuarios/`, `/usuarios/auditoria/` | Sí | No | No | No | No | No |

---

## 3. Matriz de Acciones y Casos de Uso (Qué Pueden Hacer)

Relación entre los Casos de Uso del negocio (`CU01` a `CU15`) y las acciones específicas habilitadas para cada rol:

| Caso de Uso | Acción en el Sistema | ADMINISTRADOR | OFICIAL | ANALISTA | JEFE | CAJERO | GERENTE |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CU01** | Registrar, editar y eliminar clientes | Sí | Sí | No (Solo lectura) | No (Solo lectura) | No (Solo lectura) | No (Solo lectura) |
| **CU02** | Registrar solicitud de crédito | Sí | Sí | No (Solo lectura) | No (Solo lectura) | No | No (Solo lectura) |
| **CU03** | Consultar historial crediticio (Central de Riesgos) | Sí | No | Sí | No (Solo lectura) | No | No (Solo lectura) |
| **CU04** | Evaluar capacidad de pago (ingresos vs gastos) | Sí | No | Sí | No (Solo lectura) | No | No (Solo lectura) |
| **CU05** | Emitir dictamen de riesgo crediticio | Sí | No | Sí | No (Solo lectura) | No | No (Solo lectura) |
| **CU06** | Registrar y quitar garantías de una solicitud | Sí | Sí | No (Solo lectura) | No (Solo lectura) | No | No (Solo lectura) |
| **CU07** | Aprobar solicitud de crédito | Sí | No | No | Sí | No | No |
| **CU08** | Rechazar solicitud de crédito con motivo | Sí | No | No | Sí | No | No |
| **CU09** | Generar contrato (automático al aprobar) y registrar firma | Sí | Sí (Firma) | No | Sí (Genera y Firma) | No | No |
| **CU10** | Generar y consultar cronograma de pagos (Sistema Francés) | Sí | Sí (Consulta) | Sí (Consulta) | Sí (Genera y Consulta) | Sí (Consulta) | Sí (Consulta) |
| **CU11** | Ejecutar desembolso del crédito en Core Bancario | Sí | Sí | No | Sí | No | No |
| **CU12** | Registrar cobro de cuota en ventanilla y emitir comprobante | Sí | No | No | No (Solo consulta) | Sí | No (Solo consulta) |
| **CU13** | Controlar mora y actualizar recargos por atraso | Sí | No | No | Sí (Consulta) | Sí (Ejecuta y Cobra) | Sí (Consulta) |
| **CU14** | Generar y consultar reportes de cartera, cobranzas y mora | Sí | No | No | Sí | No | Sí |
| **CU15** | Administrar usuarios, roles y consultar bitácora de auditoría | Sí | No | No | No | No | No |

---

## 4. Segmentación del Dashboard Operativo (`/`) por Rol

El Dashboard principal muestra únicamente las métricas y bandejas de trabajo pertinentes a las responsabilidades de cada rol, evitando la exposición de datos confidenciales o ajenos a su función:

| Componente del Dashboard | Contenido / Métrica | OFICIAL | ANALISTA | CAJERO | JEFE | GERENTE | ADMINISTRADOR |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **KPI: Clientes** | Padrón total de clientes registrados | Visible | Oculto | Oculto | Visible | Visible | Visible |
| **KPI: Solicitudes** | Total de solicitudes pendientes de trámite | Visible | Visible | Oculto | Visible | Visible | Visible |
| **KPI: Evaluaciones** | Total de evaluaciones técnicas realizadas | Oculto | Visible | Oculto | Oculto | Oculto | Oculto |
| **KPI: Desembolsos** | Créditos aprobados pendientes de desembolsar | Visible | Oculto | Oculto | Oculto | Oculto | Oculto |
| **KPI: Cartera Activa** | Saldo total de capital vigente | Oculto | Oculto | Oculto | Visible | Visible | Visible |
| **KPI: Recaudado en Caja**| Total acumulado de cobranzas | Oculto | Oculto | Visible | Visible | Visible | Visible |
| **KPI: Cartera en Mora** | Operaciones en estado de mora | Oculto | Oculto | Visible | Visible | Visible | Visible |
| **Bandeja: Solicitudes** | Tabla de últimas solicitudes registradas | Visible | Visible | Oculto | Visible | Visible | Visible |
| **Bandeja: Pagos** | Tabla de últimos cobros en ventanilla | Oculto | Oculto | Visible | Visible | Visible | Visible |
| **Botones de Acción** | Accesos directos a crear/procesar | + Cliente, + Solicitud | + Evaluación | Cobrar, Mora | Reportes | Reportes | Todos |

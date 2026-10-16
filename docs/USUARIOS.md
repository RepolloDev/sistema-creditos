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
| **Clientes — Crear / Editar** | `/clientes/nuevo/`, `/clientes/<id>/editar/` | Sí | Sí | No | No | No | No |
| **Clientes — Eliminar** | `/clientes/<id>/eliminar/` | Sí | No | No | No | No | No |
| **Solicitudes — Listado y Detalle** | `/solicitudes/`, `/solicitudes/<id>/` | Sí | Sí | Sí | Sí | No | Sí |
| **Solicitudes — Crear Solicitud y Garantía** | `/solicitudes/nueva/`, `/solicitudes/<id>/garantias/nueva/` | Sí | Sí | No | No | No | No |
| **Solicitudes / Garantías — Eliminar** | `/solicitudes/<id>/eliminar/`, `/solicitudes/garantias/<id>/eliminar/` | Sí | No | No | No | No | No |
| **Evaluaciones — Listado y Dictamen** | `/evaluacion/`, `/evaluacion/<id>/` | Sí | No | Sí | Sí | No | Sí |
| **Evaluaciones — Emitir y Consultar Buró** | `/evaluacion/nueva/`, `/evaluacion/<id>/consultar-riesgo/` | Sí | No | Sí | No | No | No |
| **Evaluaciones — Eliminar** | `/evaluacion/<id>/eliminar/` | Sí | No | No | No | No | No |
| **Créditos — Cartera, Detalle y Cronograma** | `/creditos/`, `/creditos/<id>/`, `/creditos/<id>/cronograma/` | Sí | Sí | Sí | Sí | Sí | Sí |
| **Créditos — Aprobar / Rechazar Solicitud** | `/creditos/aprobar/<id>/`, `/creditos/rechazar/<id>/` | Sí | No | No | Sí | No | No |
| **Créditos — Desembolso y Firma Contrato** | `/creditos/<id>/firmar-contrato/`, `/creditos/<id>/desembolsar/` | Sí | Sí | No | Sí | No | No |
| **Créditos — Eliminar** | `/creditos/<id>/eliminar/` | Sí | No | No | No | No | No |
| **Créditos — Reportes de Cartera y Mora** | `/creditos/reportes/` | Sí | No | No | Sí | No | Sí |
| **Pagos — Listado, Recibo y Control de Mora** | `/pagos/`, `/pagos/<id>/comprobante/`, `/pagos/control-mora/` | Sí | No | No | Sí | Sí | Sí |
| **Pagos — Registrar Cobro en Ventanilla** | `/pagos/registrar/` | Sí | No | No | No | Sí | No |
| **Pagos — Anular Pago** | `/pagos/<id>/eliminar/` | Sí | No | No | No | No | No |
| **Usuarios y Bitácora de Auditoría** | `/usuarios/`, `/usuarios/auditoria/` | Sí | No | No | No | No | No |

---

## 3. Matriz de Acciones y Casos de Uso (Qué Pueden Hacer)

Relación entre los Casos de Uso del negocio (`CU01` a `CU15`) y las acciones específicas habilitadas para cada rol:

| Caso de Uso | Acción en el Sistema | ADMINISTRADOR | OFICIAL | ANALISTA | JEFE | CAJERO | GERENTE |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CU01** | Registrar y editar clientes | Sí | Sí | No (Solo lectura) | No (Solo lectura) | No (Solo lectura) | No (Solo lectura) |
| **CU01-DEL** | Eliminar clientes | Sí | No | No | No | No | No |
| **CU02** | Registrar solicitud de crédito | Sí | Sí | No (Solo lectura) | No (Solo lectura) | No | No (Solo lectura) |
| **CU02-DEL** | Eliminar solicitudes | Sí | No | No | No | No | No |
| **CU03** | Consultar historial crediticio (Central de Riesgos) | Sí | No | Sí | No (Solo lectura) | No | No (Solo lectura) |
| **CU04** | Evaluar capacidad de pago (ingresos vs gastos) | Sí | No | Sí | No (Solo lectura) | No | No (Solo lectura) |
| **CU05** | Emitir dictamen de riesgo crediticio | Sí | No | Sí | No (Solo lectura) | No | No (Solo lectura) |
| **CU05-DEL** | Eliminar evaluaciones | Sí | No | No | No | No | No |
| **CU06** | Registrar garantías de una solicitud | Sí | Sí | No (Solo lectura) | No (Solo lectura) | No | No (Solo lectura) |
| **CU06-DEL** | Quitar garantías de una solicitud | Sí | No | No | No | No | No |
| **CU07** | Aprobar solicitud de crédito | Sí | No | No | Sí | No | No |
| **CU08** | Rechazar solicitud de crédito con motivo | Sí | No | No | Sí | No | No |
| **CU09** | Generar contrato (automático al aprobar) y registrar firma | Sí | Sí (Firma) | No | Sí (Genera y Firma) | No | No |
| **CU10** | Generar y consultar cronograma de pagos (Sistema Francés) | Sí | Sí (Consulta) | Sí (Consulta) | Sí (Genera y Consulta) | Sí (Consulta) | Sí (Consulta) |
| **CU11** | Ejecutar desembolso del crédito en Core Bancario | Sí | Sí | No | Sí | No | No |
| **CU11-DEL** | Eliminar crédito | Sí | No | No | No | No | No |
| **CU12** | Registrar cobro de cuota en ventanilla y emitir comprobante | Sí | No | No | No (Solo consulta) | Sí | No (Solo consulta) |
| **CU12-DEL** | Anular pago registrado | Sí | No | No | No | No | No |
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

---

## 5. Flujo Operativo Completo de Extremo a Extremo (Paso a Paso)

Guía para recrear el ciclo de vida completo de un crédito, desde el registro inicial del cliente hasta la cobranza total y auditoría.

```
[1. OFICIAL]              [2. ANALISTA]             [3. JEFE]               [4. OFICIAL / JEFE]         [5. CAJERO]
Registra Cliente  ───>  Evalúa Solicitud   ───>  Aprueba Solicitud  ───>  Firma Contrato      ───>  Cobra Cuotas en Caja
Crea Solicitud          Consulta Buró            Genera Crédito           Ejecuta Desembolso        Emite Comprobantes
Agrega Garantías        Dictamina Riesgo         Crea Cronograma          Activa Crédito            Controla Mora
```

---

### Paso 1: Originación (Oficial de Crédito)
- **Usuario:** `oficial1` | **Contraseña:** `oficial123`
1. **Registrar Cliente:**
   - Ir a **Clientes** (`/clientes/`) → Clic en **+ Nuevo Cliente** (`/clientes/nuevo/`).
   - Llenar C.I., nombres, apellidos, teléfono, dirección e ingresos mensuales (ej. Bs. 8,500.00). Guardar.
2. **Crear Solicitud de Crédito:**
   - En el detalle del cliente (`/clientes/<id>/`), hacer clic en el botón negro principal **+ Solicitud** (o ir a `/solicitudes/nueva/`).
   - Ingresar monto solicitado (ej. Bs. 15,000.00), plazo (ej. 12 meses) y destino del crédito. Guardar.
   - Estado inicial de la solicitud: `REGISTRADA` (Paso 1 activo en la barra de progreso).
3. **Registrar Garantías:**
   - En el detalle de la solicitud (`/solicitudes/<id>/`), hacer clic en **+ Garantía** (`/solicitudes/<id>/garantias/nueva/`).
   - Seleccionar tipo (Hipotecaria, Vehicular, Personal), descripción y valor estimado (ej. Bs. 25,000.00). Guardar.
4. **Cerrar sesión:** Clic en botón **Salir** de la barra lateral.

---

### Paso 2: Análisis de Riesgo y Capacidad de Pago (Analista de Crédito)
- **Usuario:** `analista1` | **Contraseña:** `analista123`
1. **Identificar Solicitud Pendiente:**
   - Al ingresar al inicio (`/`) o a **Evaluaciones** (`/evaluacion/`), aparece la bandeja de **Solicitudes Pendientes de Evaluación**.
   - Hacer clic en el botón **Evaluar #ID** correspondiente a la solicitud creada en el Paso 1.
2. **Emitir Evaluación Financiera:**
   - El sistema carga los ingresos del cliente automáticamente.
   - Ingresar gastos mensuales declarados (ej. Bs. 3,200.00).
   - El sistema calcula:
     - Capacidad de Pago neta = Ingresos - Gastos.
     - Cuota máxima admisible (40% de la capacidad de pago).
     - Cuota estimada del crédito.
   - Seleccionar nivel de riesgo (`BAJO`, `MEDIO` o `ALTO`) y dictamen (`APROBADO` o `OBSERVADO`). Guardar.
3. **Verificación en Central de Riesgos (Buró Externo):**
   - En la vista del dictamen (`/evaluacion/<id>/`), hacer clic en **Consultar Central de Riesgos** (`/evaluacion/<id>/consultar-riesgo/`).
   - El sistema consulta el servicio externo simulado y registra score crediticio (ej. 850 puntos), deudas en otras entidades y reporte de mora activa.
   - El estado de la solicitud avanza a `EN_EVALUACION` (Paso 2 activo en el stepper).
4. **Cerrar sesión.**

---

### Paso 3: Resolución y Aprobación (Jefe de Créditos)
- **Usuario:** `jefe1` | **Contraseña:** `jefe123`
1. **Revisar Solicitud y Dictamen:**
   - Ir a **Solicitudes** (`/solicitudes/`) o **Evaluaciones** (`/evaluacion/`).
   - Abrir el detalle de la solicitud (`/solicitudes/<id>/`).
2. **Aprobar Solicitud:**
   - Hacer clic en el botón negro principal **Aprobar** (`/creditos/aprobar/<id>/`).
   - Confirmar monto aprobado final (ej. Bs. 15,000.00), tasa de interés anual (ej. 12.00%) y plazo (12 meses).
   - Clic en **Confirmar y Aprobar Crédito**.
   - **Resultado automático generado por el sistema:**
     - Solicitud cambia a estado `APROBADA`.
     - Se crea el registro del **Crédito** en estado `APROBADO`.
     - Se genera automáticamente el **Contrato** con código `VK-CTR-XXXXXX` en estado `GENERADO`.
     - Se calcula y genera el **Cronograma de Pagos (Plan de Cuotas)** bajo el Sistema Francés (capital creciente, interés decreciente).
3. **Cerrar sesión.**

---

### Paso 4: Formalización y Desembolso (Oficial de Crédito o Jefe)
- **Usuario:** `oficial1` (o `jefe1`) | **Contraseña:** `oficial123`
1. **Abrir Crédito Aprobado:**
   - Ir a **Créditos** (`/creditos/`) y abrir el crédito recién creado (`/creditos/<id>/`).
   - El stepper visual muestra `1. Aprobado` completado y `2. Firma Contrato` activo.
2. **Registrar Firma del Contrato:**
   - En la tarjeta *Formalización y Desembolso*, hacer clic en:
     **1. Registrar Firma del Contrato (VK-CTR-XXXXXX)**.
   - El contrato cambia a estado `FIRMADO`.
   - El botón de desembolso queda habilitado de inmediato.
3. **Ejecutar Desembolso en Core Bancario:**
   - En la misma pantalla, verificar la cuenta destino bancaria (`VK-CTA-...`).
   - Hacer clic en el botón negro:
     **2. Ejecutar Desembolso (Bs. 15,000.00)**.
   - **Resultado automático:**
     - Se genera una transacción de abono exitosa en el Core Bancario (`TransaccionCoreBancario`).
     - El crédito pasa oficialmente a estado `VIGENTE`.
     - El crédito entra a la cartera activa y queda listo para recibir cobros.
4. **Cerrar sesión.**

---

### Paso 5: Cobranzas y Caja (Cajero)
- **Usuario:** `cajero1` | **Contraseña:** `cajero123`
1. **Cobro de Cuota en Ventanilla:**
   - En el Dashboard (`/`), hacer clic en **Cobrar Cuota** (o en el menú **Pagos y Mora** → **+ Cobrar Cuota** en `/pagos/registrar/`).
   - Seleccionar el crédito por su código o nombre del cliente.
   - El sistema preselecciona la cuota pendiente más antigua (#1).
   - Verificar monto exacto de la cuota (Capital + Interés).
   - Seleccionar forma de pago: `EFECTIVO`, `TRANSFERENCIA` o `QR`.
   - Clic en **Procesar Cobro**.
2. **Comprobante de Pago:**
   - El sistema redirige al recibo oficial (`/pagos/<id>/comprobante/`) con número correlativo `REC-XXXXXX`.
   - Muestra desglose de capital abonado, interés ordinario, recargo por mora (si hubiese) y saldo de capital restante.
3. **Control y Actualización de Mora:**
   - Ir a **Control de Mora** (`/pagos/control-mora/`).
   - Muestra las cuotas que superaron su fecha de vencimiento y los días de atraso acumulados.
   - Clic en **Actualizar Mora** para recalcular los intereses penales al día de hoy.
4. **Cerrar sesión.**

---

### Paso 6: Supervisión de Cartera y Métricas (Gerente o Jefe)
- **Usuario:** `gerente1` | **Contraseña:** `gerente123`
1. **Dashboard Financiero (`/`):**
   - Visualiza en tiempo real:
     - Saldo de Cartera Activa colocada.
     - Total recaudado acumulado en caja.
     - Cantidad de créditos en mora.
2. **Reportes Ejecutivos (`/creditos/reportes/`):**
   - Filtrar cartera por estado (`VIGENTE`, `EN_MORA`, `PAGADO`).
   - Consultar indicadores consolidados de colocación, recuperación de capital y tasa de mora de la institución.
3. **Cerrar sesión.**

---

### Paso 7: Administración Central y Auditoría (Administrador)
- **Usuario:** `admin` | **Contraseña:** `admin123`
1. **Control de Usuarios y Roles (`/usuarios/`):**
   - Dar de alta nuevos empleados (`+ Nuevo Usuario`) o inactivar cuentas.
2. **Bitácora de Auditoría (`/usuarios/auditoria/`):**
   - Revisar el historial cronológico de todas las operaciones críticas ejecutadas en el sistema (quién creó, aprobó, desembolsó o cobró cada crédito, con dirección IP y fecha/hora).
3. **Eliminación Exclusiva de Registros:**
   - El `ADMINISTRADOR` es el **único rol** que tiene visibles y habilitados los botones rojos de eliminación (`Eliminar` / `Anular`) en clientes, solicitudes, evaluaciones, créditos y pagos.
   - Cualquier intento de eliminación por parte de otro rol es rechazado por el sistema con código HTTP 403 / redirección segura.

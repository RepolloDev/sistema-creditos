# Cuentas de Usuario para Pruebas del Sistema

Este documento detalla los 17 usuarios generados por el script de seed (`database/seed.py`) para pruebas funcionales, verificación de roles (RBAC) y control de acceso en el **Sistema de Gestión de Créditos (Banco Volkskas S.A.)**.

---

## 1. Credenciales de Acceso Rápido

| Rol en el Sistema | Login | Contraseña | Nombre Completo | Módulos Autorizados |
| :--- | :--- | :--- | :--- | :--- |
| **Administrador** | `admin` | `admin123` | Administrador Central | **Todos los módulos** + Auditoría y Usuarios (CU15) + Django Admin |
| **Oficial de Crédito** | `oficial1` | `oficial123` | Carlos Mendoza Flores | Clientes (CU01), Solicitudes (CU02, CU06), Consulta de Cartera |
| **Oficial de Crédito** | `oficial2` | `oficial123` | Mariana Rios Gutierrez | Clientes (CU01), Solicitudes (CU02, CU06), Consulta de Cartera |
| **Oficial de Crédito** | `oficial3` | `oficial123` | Gustavo Paredes Luna | Clientes (CU01), Solicitudes (CU02, CU06), Consulta de Cartera |
| **Oficial de Crédito** | `oficial4` | `oficial123` | Elena Choque Fernandez | Clientes (CU01), Solicitudes (CU02, CU06), Consulta de Cartera |
| **Analista de Crédito** | `analista1` | `analista123` | Fernando Morales Silva | Evaluación de Riesgo (CU03, CU04, CU05), Consulta Clientes y Solicitudes |
| **Analista de Crédito** | `analista2` | `analista123` | Lucia Benitez Aliaga | Evaluación de Riesgo (CU03, CU04, CU05), Consulta Clientes y Solicitudes |
| **Analista de Crédito** | `analista3` | `analista123` | Andres Guzman Teran | Evaluación de Riesgo (CU03, CU04, CU05), Consulta Clientes y Solicitudes |
| **Jefe de Créditos** | `jefe1` | `jefe123` | Dr. Victor Hugo Banzer | Aprobación / Rechazo (CU07, CU08), Contratos (CU09), Desembolso (CU11), Reportes |
| **Jefe de Créditos** | `jefe2` | `jefe123` | Lic. Patricia Miranda Soliz | Aprobación / Rechazo (CU07, CU08), Contratos (CU09), Desembolso (CU11), Reportes |
| **Cajero de Ventanilla**| `cajero1` | `cajero123` | Valeria Rojas Suarez | Ventanilla de Caja y Pagos (CU12), Comprobantes, Consulta Créditos |
| **Cajero de Ventanilla**| `cajero2` | `cajero123` | Roberto Quispe Mamani | Ventanilla de Caja y Pagos (CU12), Comprobantes, Consulta Créditos |
| **Cajero de Ventanilla**| `cajero3` | `cajero123` | Daniela Vargas Pinto | Ventanilla de Caja y Pagos (CU12), Comprobantes, Consulta Créditos |
| **Cajero de Ventanilla**| `cajero4` | `cajero123` | Jorge Lopez Arratia | Ventanilla de Caja y Pagos (CU12), Comprobantes, Consulta Créditos |
| **Cajero de Ventanilla**| `cajero5` | `cajero123` | Sonia Condori Laura | Ventanilla de Caja y Pagos (CU12), Comprobantes, Consulta Créditos |
| **Gerente de Agencia** | `gerente1` | `gerente123` | Ing. Mauricio Del Carpio | Reportes Gerenciales y Monitoreo de Cartera (CU14), Consulta Global |
| **Gerente de Agencia** | `gerente2` | `gerente123` | Lic. Claudia Villarroel Paz | Reportes Gerenciales y Monitoreo de Cartera (CU14), Consulta Global |

---

## 2. Matriz de Control de Acceso y Bloqueo en Sidebar (RBAC)

El menú lateral del sistema deshabilita visualmente los módulos fuera del alcance del rol en sesión con el indicador `[RESTRINGIDO]` o `[BLOQUEADO]`:

| Módulo del Sistema | ADMINISTRADOR | OFICIAL | ANALISTA | JEFE | CAJERO | GERENTE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dashboard Operativo** | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado |
| **Clientes** | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado |
| **Solicitudes y Garantías** | ✅ Habilitado | ✅ Habilitado | 🔒 Restringido | ✅ Habilitado | 🔒 Restringido | 🔒 Restringido |
| **Evaluación de Riesgo** | ✅ Habilitado | 🔒 Restringido | ✅ Habilitado | ✅ Habilitado | 🔒 Restringido | 🔒 Restringido |
| **Cartera de Créditos** | ✅ Habilitado | ✅ Habilitado | 🔒 Restringido | ✅ Habilitado | ✅ Habilitado | ✅ Habilitado |
| **Ventanilla de Caja (Pagos)**| ✅ Habilitado | 🔒 Restringido | 🔒 Restringido | 🔒 Restringido | ✅ Habilitado | 🔒 Restringido |
| **Reportes Gerenciales** | ✅ Habilitado | 🔒 Restringido | 🔒 Restringido | ✅ Habilitado | 🔒 Restringido | ✅ Habilitado |
| **Auditoría y Usuarios** | ✅ Habilitado | 🚫 Bloqueado | 🚫 Bloqueado | 🚫 Bloqueado | 🚫 Bloqueado | 🚫 Bloqueado |

---

## 3. Comandos de Inicialización

Para restablecer o repoblar la base de datos con estos usuarios y los 45 créditos de prueba:

```bash
# 1. Aplicar migraciones
uv run task migrate

# 2. Ejecutar seed de datos
uv run task seed

# 3. Iniciar servidor de desarrollo
uv run task dev
```

La URL de inicio de sesión es: `http://127.0.0.1:8000/usuarios/login/`

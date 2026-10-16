# Módulo de Usuarios y Seguridad (`apps/usuarios`)

¡Bienvenido a este módulo! Esta guía está escrita para que cualquier miembro del equipo entienda qué hace esta carpeta, cómo funciona por dentro y cómo conectan sus partes, sin rodeos ni términos complicados de programación.

---

## 1. ¿Qué es este módulo y para qué sirve?

Imagina este módulo como **la puerta de entrada y el guardia de seguridad del banco**:
1. **Control de acceso:** Aquí se gestiona quién puede entrar al sistema mediante su nombre de usuario (`login`) y su contraseña.
2. **Cargos y permisos (Roles):** En un banco no todos pueden hacer lo mismo. Este módulo le asigna un cargo a cada persona (Cajero, Oficial de Crédito, Jefe, Administrador, etc.) para que el sistema solo le permita ver los botones y pantallas que le corresponden a su trabajo.
3. **El cuaderno de firmas (Bitácora de Auditoría):** Cada vez que alguien aprueba un crédito, rechaza una solicitud o cobra una cuota en ventanilla, este módulo anota de manera automática quién lo hizo, a qué hora exacta y si la acción salió bien o dio error. En un banco es obligatorio saber quién es responsable de cada movimiento.

---

## 2. Mapa rápido de los archivos

Dentro de esta carpeta (`apps/usuarios/`) encontrarás los siguientes archivos principales:

```text
apps/usuarios/
├── models.py      --> La definición de la base de datos (qué información guardamos).
├── views.py       --> El cerebro / recepcionista (qué pasa cuando el usuario hace clic o pide una página).
├── forms.py       --> El revisor de formularios (se asegura de que los datos escritos en pantalla sean válidos).
├── urls.py        --> El mapa de direcciones (conecta los enlaces de la web con las pantallas).
├── admin.py       --> La ventana técnica de soporte (para ver los datos en el panel administrativo).
└── apps.py        --> La tarjeta de presentación de la aplicación ante el sistema.
```

---

## 3. Explicación detallada archivo por archivo

### A. `models.py` (La base de datos)
En Django, este archivo sirve para decirle a la base de datos qué tablas crear y qué casillas de información debe tener cada registro.

Aquí se definen dos cosas:
1. **`Usuario` (Tabla `USUARIO`):**
   - Es cada empleado del banco.
   - Guarda su nombre de usuario (`login`), su nombre y apellidos (`nombre_completo`), su cargo (`rol`) y si su cuenta está habilitada (`activo`).
   - **Nota sobre la contraseña:** La contraseña nunca se guarda como texto normal (por ejemplo, nunca se guarda "123456"). Django la transforma en un código enredado e indescifrable (`password` hash) por motivos de seguridad.
   - **Los 6 Roles disponibles:**
     - `OFICIAL`: Oficial de Crédito (recibe al cliente y crea la solicitud).
     - `ANALISTA`: Analista de Crédito (evalúa si el cliente tiene dinero para pagar).
     - `JEFE`: Jefe de Créditos (aprueba o rechaza el préstamo).
     - `CAJERO`: Cajero (cobra las cuotas en ventanilla).
     - `ADMINISTRADOR`: Administrador del sistema (crea cuentas a los empleados).
     - `GERENTE`: Gerente (revisa reportes generales de dinero y deudas).

2. **`Auditoria` (Tabla `AUDITORIA`):**
   - Es el historial inalterable.
   - Guarda: fecha y hora (`fecha_hora`), nombre de la operación (`operacion`, por ejemplo: "APROBAR_SOLICITUD"), tabla intervenida (`entidad`), número de trámite (`id_entidad`), resultado (`resultado`: "EXITOSO" o "ERROR") y el empleado responsable (`usuario`).

---

### B. `views.py` (Las vistas / El coordinador)
Este archivo es el que recibe las peticiones cuando alguien usa la web y decide qué hacer.

- **Iniciar sesión (`UsuarioLoginView`):** Recibe el usuario y la clave ingresados en pantalla, verifica si coinciden y, si todo está en orden, le abre la sesión de trabajo al empleado.
- **Cerrar sesión (`UsuarioLogoutView`):** Cierra la sesión activa y regresa al login.
- **Redirigir al inicio (`dashboard_redirect_view`):** Manda al usuario a la página de bienvenida general (`/`).
- **Gestión de empleados (Solo para el Administrador):**
  - `UsuarioListView`: Muestra la lista de todos los empleados en una tabla, permitiendo buscar por nombre o filtrar por cargo.
  - `UsuarioCreateView`: Recibe los datos para dar de alta a un nuevo empleado y guarda su clave encriptada.
  - `UsuarioUpdateView`: Permite cambiar el nombre, el cargo o el estado activo de un empleado existente.
  - `UsuarioDeleteView`: Pantalla para dar de baja o eliminar un usuario.
- **Regla de seguridad (`SoloAdminMixin`):** Este archivo contiene un "freno de mano". Si un cajero o un oficial intenta entrar a la fuerza a la dirección de crear usuarios, el sistema lo detecta, frena la petición y le dice: *"Acceso restringido. Solo administradores pueden gestionar usuarios."*

---

### C. `forms.py` (Los formularios en pantalla)
Cuando un usuario escribe en cajitas de texto y presiona un botón de "Guardar", la información llega primero a este archivo.

- **¿Para qué sirve?** Para revisar que la información no venga con errores antes de tocar la base de datos.
- **`LoginForm`:** Dibuja las cajas de texto de "Usuario" y "Contraseña" para el inicio de sesión.
- **`UsuarioCreateForm` (Crear empleado):**
  - Muestra las casillas para el nombre de usuario, nombre completo, selector de cargo y estado activo.
  - Pide escribir la contraseña **dos veces** (`password` y `confirmar_password`). Si no son exactamente idénticas o tienen menos de 6 letras/números, avisa en pantalla del error y no deja continuar.
- **`UsuarioUpdateForm` (Editar empleado):**
  - Permite modificar nombre, cargo y estado.
  - El nombre de usuario (`login`) se deja bloqueado como solo lectura para que nadie cambie el identificador de una persona que ya firmó trámites en el pasado.
  - El cambio de contraseña aquí es opcional: solo se llena si se quiere restablecer la clave del trabajador.

---

### D. `urls.py` (El mapa de direcciones web)
Es la lista de caminos que entiende este módulo. Le indica al navegador a qué parte de `views.py` debe acudir según la dirección URL:

| Dirección URL | Nombre del camino | ¿Para qué sirve? |
| :--- | :--- | :--- |
| `/usuarios/login/` | `usuarios:login` | Muestra la pantalla para iniciar sesión. |
| `/usuarios/logout/` | `usuarios:logout` | Cierra la sesión activa. |
| `/usuarios/dashboard/` | `usuarios:dashboard` | Envía al panel principal de trabajo. |
| `/usuarios/` | `usuarios:usuario_list` | Muestra la tabla con todos los empleados (solo Administrador). |
| `/usuarios/nuevo/` | `usuarios:usuario_create` | Muestra el formulario para crear un nuevo usuario (solo Administrador). |
| `/usuarios/<id>/editar/` | `usuarios:usuario_update` | Muestra el formulario para editar a un empleado (solo Administrador). |
| `/usuarios/<id>/eliminar/` | `usuarios:usuario_delete` | Pide confirmación antes de dar de baja a un usuario (solo Administrador). |

---

### E. `admin.py` (La consola técnica de Django)
Django viene con un panel de control automático para los técnicos y programadores (accesible en `/admin/`).
- Este archivo registra los modelos `Usuario` y `Auditoria` en ese panel.
- Permite que, en caso de emergencia, un administrador técnico pueda entrar a revisar auditorías o desbloquear una cuenta directamente.

---

### F. `apps.py` (Configuración de la aplicación)
Es un archivo muy pequeño pero obligatorio en Django. Simplemente le indica al sistema global: *"Hola, me llamo usuarios y estoy lista para trabajar dentro del proyecto"*.

---

## 4. ¿Cómo se conecta este módulo con el resto del proyecto?

Este módulo es la base sobre la que se apoyan todos los demás:
- **Con `apps/solicitudes`:** Cada solicitud de crédito guarda quién fue el oficial que la registró y quién fue el jefe que la aprobó o rechazó.
- **Con `apps/evaluacion`:** Cada evaluación financiera guarda qué analista de crédito emitió el dictamen.
- **Con `apps/pagos`:** Cada cobro de cuota en caja guarda el usuario del cajero que recibió el dinero.
- **En los menús y plantillas (`templates/`):**
  En cualquier página HTML del sistema, puedes saber quién está conectado usando la variable especial `request.user`. Por ejemplo:
  ```html
  <!-- Muestra el nombre del funcionario en la barra superior -->
  Hola, {{ request.user.nombre_completo }} ({{ request.user.get_rol_display }})

  <!-- Oculta o muestra botones según el cargo -->
  {% if request.user.rol == "JEFE" %}
      <button class="btn btn-primary">Aprobar Solicitud</button>
  {% endif %}
  ```

"""
================================================================================
MÓDULO: USUARIOS (apps/usuarios/models.py)
================================================================================
¿QUÉ HACE ESTE ARCHIVO?
Define las tablas de la base de datos para los usuarios y la auditoría.
Le dice a la base de datos qué información guardar sobre los empleados del
banco y cómo registrar cada acción importante que ocurre en el sistema.

¿POR QUÉ ES NECESARIO?
Django por defecto viene con un modelo de usuario pensado para sitios web
comunes (con email, primer nombre y apellido por separado).
En un banco necesitamos:
1. Entrar con un nombre de usuario interno (`login`) sin obligar a tener email.
2. Manejar 6 cargos o roles específicos (Cajero, Oficial, Analista, Jefe, etc.).
3. Tener una tabla de auditoría legal obligatoria para saber quién hizo qué.
================================================================================
"""

# ------------------------------------------------------------------------------
# IMPORTACIONES (Herramientas que traemos de Django)
# ------------------------------------------------------------------------------

# AbstractBaseUser: Es la plantilla básica de Django que ya sabe cómo manejar
# contraseñas seguras (encriptadas) y sesiones sin que tengamos que programarlo desde cero.
#
# BaseUserManager: Es la clase encargada de crear usuarios y guardar contraseñas
# de forma correcta en la base de datos.
#
# PermissionsMixin: Le da al usuario la capacidad de tener permisos especiales,
# grupos y saber si es un superadministrador (is_superuser).
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# models: El módulo central de Django para definir tablas, columnas y tipos de datos
# (texto, números, fechas, booleanos, relaciones).
from django.db import models


# ------------------------------------------------------------------------------
# GESTOR DE USUARIOS (Cómo se crean los usuarios en código)
# ------------------------------------------------------------------------------
class UsuarioManager(BaseUserManager):
    """
    Este gestor le enseña a Django cómo crear usuarios normales y administradores
    usando nuestro campo `login` en vez del clásico `username` o `email`.
    """

    def create_user(self, login, password=None, **extra_fields):
        """
        Crea y guarda un usuario común en la base de datos.
        - login: El nombre de usuario que usará el empleado para entrar.
        - password: La contraseña en texto plano que el usuario escribió.
        - **extra_fields: Cualquier otro dato extra (nombre completo, rol, etc.).
        """
        if not login:
            raise ValueError("El login es obligatorio")

        # Crea el objeto Usuario en memoria con su login y demás campos
        user = self.model(login=login, **extra_fields)

        # Si se le pasó contraseña, la encripta con un algoritmo seguro (hash).
        # NUNCA se guarda la contraseña tal cual la escribió el usuario.
        if password:
            user.set_password(password)
        else:
            # Si no hay contraseña, marca la cuenta como no accesible por clave
            user.set_unusable_password()

        # Guarda el registro en la base de datos actual
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        """
        Crea un superusuario (administrador total con acceso a todo el sistema
        y a la consola técnica de Django en /admin/).
        """
        extra_fields.setdefault("is_staff", True)       # Puede entrar a /admin/
        extra_fields.setdefault("is_superuser", True)   # Tiene todos los permisos
        extra_fields.setdefault("rol", Usuario.Rol.ADMINISTRADOR)  # Rol máximo

        return self.create_user(login, password, **extra_fields)


# ------------------------------------------------------------------------------
# MODELO PRINCIPAL: USUARIO (Tabla 'USUARIO' en la base de datos)
# ------------------------------------------------------------------------------
class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Representa a cada trabajador del Banco Volkskas dentro del sistema.
    """

    # Definimos los 6 cargos oficiales permitidos en el banco.
    # El primer valor es cómo se guarda en la BD (ej. 'OFICIAL')
    # El segundo valor es cómo se muestra a los humanos (ej. 'Oficial de Crédito').
    class Rol(models.TextChoices):
        OFICIAL = "OFICIAL", "Oficial de Crédito"
        ANALISTA = "ANALISTA", "Analista de Crédito"
        JEFE = "JEFE", "Jefe de Créditos"
        CAJERO = "CAJERO", "Cajero"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        GERENTE = "GERENTE", "Gerente"

    # Nombre de usuario único para entrar al sistema (ej: 'cvaldez_jefe')
    login = models.CharField(max_length=50, unique=True)

    # Nombre y apellido completos del empleado
    nombre_completo = models.CharField(max_length=150)

    # Cargo asignado en el banco (por defecto es Oficial de Crédito)
    rol = models.CharField(max_length=30, choices=Rol.choices, default=Rol.OFICIAL)

    # Si es True, el empleado puede entrar. Si es False, su cuenta está bloqueada.
    activo = models.BooleanField(default=True)

    # Obligatorio para Django: indica si tiene permiso de entrar al panel técnico /admin/
    is_staff = models.BooleanField(default=False)

    # Conecta este modelo con nuestro gestor personalizado de arriba
    objects = UsuarioManager()

    # Le dice a Django: "Para iniciar sesión, usa la columna 'login'"
    USERNAME_FIELD = "login"

    # Campos que Django pide obligatoriamente cuando se crea un superusuario por terminal
    REQUIRED_FIELDS = ["nombre_completo"]

    class Meta:
        db_table = "USUARIO"  # Nombre exacto de la tabla en PostgreSQL
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    # Django busca internamente un atributo llamado 'is_active'.
    # Como en nuestro diseño llamamos a la columna 'activo', usamos estas dos
    # funciones (@property) para que cuando Django pregunte por 'is_active',
    # responda con el valor de nuestra columna 'activo'.
    @property
    def is_active(self):
        return self.activo

    @is_active.setter
    def is_active(self, value):
        self.activo = bool(value)

    def __str__(self):
        # Cómo se muestra este usuario si lo imprimimos como texto
        return f"{self.login} ({self.get_rol_display()})"


# ------------------------------------------------------------------------------
# MODELO: AUDITORIA (Tabla 'AUDITORIA' en la base de datos)
# ------------------------------------------------------------------------------
class Auditoria(models.Model):
    """
    El cuaderno de registro legal inmutable del banco.
    Cada vez que se aprueba un crédito, se rechaza una solicitud, se desembolsa dinero
    o se cobra una cuota, se crea una fila en esta tabla.
    """

    class Resultado(models.TextChoices):
        EXITOSO = "EXITOSO", "Exitoso"
        ERROR = "ERROR", "Error"

    # Qué empleado realizó la acción.
    # on_delete=models.SET_NULL: Si en el futuro se borra el usuario, la fila de auditoría
    # NO se borra; el campo queda vacío para no perder el registro histórico de lo que pasó.
    usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="auditorias"
    )

    # Fecha y hora exacta de la acción (se llena sola en el momento de crear el registro)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    # Nombre de la operación (ej: 'APROBAR_SOLICITUD', 'REGISTRAR_PAGO', 'CREAR_CLIENTE')
    operacion = models.CharField(max_length=50)

    # Qué tabla o módulo fue modificado (ej: 'SOLICITUD_CREDITO', 'CREDITO', 'PAGO')
    entidad = models.CharField(max_length=50)

    # El número identificador (ID) del trámite o registro que se tocó
    id_entidad = models.IntegerField()

    # Si la operación terminó bien ('EXITOSO') o falló ('ERROR')
    resultado = models.CharField(max_length=20, choices=Resultado.choices)

    class Meta:
        db_table = "AUDITORIA"  # Nombre exacto en la base de datos
        verbose_name = "Auditoría"
        verbose_name_plural = "Auditorías"

    def __str__(self):
        return f"{self.fecha_hora} - {self.operacion} {self.entidad}#{self.id_entidad} ({self.resultado})"

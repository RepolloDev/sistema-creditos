from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError("El login es obligatorio")
        user = self.model(login=login, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", Usuario.Rol.ADMINISTRADOR)
        return self.create_user(login, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Rol(models.TextChoices):
        OFICIAL = "OFICIAL", "Oficial de Crédito"
        ANALISTA = "ANALISTA", "Analista de Crédito"
        JEFE = "JEFE", "Jefe de Créditos"
        CAJERO = "CAJERO", "Cajero"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        GERENTE = "GERENTE", "Gerente"

    login = models.CharField(max_length=50, unique=True)
    nombre_completo = models.CharField(max_length=150)
    rol = models.CharField(max_length=30, choices=Rol.choices, default=Rol.OFICIAL)
    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = ["nombre_completo"]

    class Meta:
        db_table = "USUARIO"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    @property
    def is_active(self):
        return self.activo

    @is_active.setter
    def is_active(self, value):
        self.activo = bool(value)

    def __str__(self):
        return f"{self.login} ({self.get_rol_display()})"


class Auditoria(models.Model):
    class Resultado(models.TextChoices):
        EXITOSO = "EXITOSO", "Exitoso"
        ERROR = "ERROR", "Error"

    usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="auditorias"
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    operacion = models.CharField(max_length=50)
    entidad = models.CharField(max_length=50)
    id_entidad = models.IntegerField()
    resultado = models.CharField(max_length=20, choices=Resultado.choices)

    class Meta:
        db_table = "AUDITORIA"
        verbose_name = "Auditoría"
        verbose_name_plural = "Auditorías"

    def __str__(self):
        return f"{self.fecha_hora} - {self.operacion} {self.entidad}#{self.id_entidad} ({self.resultado})"

"""
================================================================================
MÓDULO: USUARIOS (apps/usuarios/apps.py)
================================================================================
¿QUÉ HACE ESTE ARCHIVO?
Es la tarjeta de identidad de la aplicación ante el motor de Django.
Declara el nombre oficial de la app y qué tipo de identificadores numéricos
usarán las tablas de la base de datos por defecto.

¿POR QUÉ ES NECESARIO?
Django necesita que cada carpeta de aplicación tenga una clase de configuración
(AppConfig) para poder registrarla en la lista de `INSTALLED_APPS` del archivo
central `config/settings.py`.
================================================================================
"""

# AppConfig: Clase base de Django para configurar una aplicación
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    # BigAutoField: Le indica a la base de datos que use números enteros gigantes
    # (64 bits) para las claves primarias (IDs), soportando millones de registros.
    default_auto_field = "django.db.models.BigAutoField"

    # El nombre de la carpeta de la aplicación
    name = "usuarios"

"""
Script para poblar la base de datos con datos iniciales de desarrollo.
Ejecución:
    uv run task seed
    o
    uv run python database/seed.py
"""

import os
import sys
from pathlib import Path

# Configurar rutas y entorno Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model


def seed_superuser():
    User = get_user_model()
    username = os.getenv("SEED_ADMIN_USER", "admin")
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
        },
    )

    if created:
        user.set_password(password)
        user.save()
        print(f"[OK] Superusuario creado: {username} (password: {password})")
    else:
        print(f"[INFO] Superusuario '{username}' ya existe.")


def seed_all():
    print("Iniciando seed de base de datos...")
    seed_superuser()
    # Agregar aquí llamadas a funciones adicionales (ej. seed_clientes(), seed_creditos())
    print("Seed completado exitosamente.")


if __name__ == "__main__":
    seed_all()

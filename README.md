- Hola desde Juan

## Inicio Rápido (Setup Inicial)

```bash
# 1. Configurar variables de entorno
cp .env.example .env

# 2. Instalar dependencias
uv sync

# 3. Aplicar migraciones a la base de datos (SQLite)
uv run task migrate

# 4. Crear usuario administrador (opcional)
uv run python manage.py createsuperuser

# 5. Iniciar servidor de desarrollo
uv run task dev
```

El servidor estará disponible en [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
Panel de administración en [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

---

## Comandos Rápidos (Scripts)

| Comando | Descripción |
|---|---|
| `uv run task dev` | Inicia el servidor de desarrollo |
| `uv run task migrate` | Aplica migraciones a `db.sqlite3` |
| `uv run task makemigrations` | Genera nuevas migraciones a partir de los modelos |
| `uv run task check` | Verifica el estado de la configuración |
| `uv run task test` | Corre las pruebas unitarias |

---

## Estructura del Código

```text
sis-creditos/
├── apps/          # Módulos de dominio (clientes, creditos, etc.)
├── config/        # Configuración central (settings, urls, wsgi)
├── templates/     # Frontend (HTML, base.html con Tailwind)
├── static/        # CSS, JavaScript e imágenes globales
├── pyproject.toml # Dependencias y scripts del proyecto
├── .env           # Variables locales (ignorado por Git)
└── db.sqlite3     # Base de datos local (ignorado por Git)
```

---

## Reglas para el Equipo

1. **Nunca subir `db.sqlite3` ni `.env`** al repositorio.
2. Cada desarrollador trabaja en su app correspondiente dentro de `apps/`.
3. Antes de abrir un PR, asegurarse de ejecutar `uv run task makemigrations` y `uv run task check`.

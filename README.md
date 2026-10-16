> [!IMPORTANT]
> Revisar [docs/USUARIOS.md](./docs/USUARIOS.md) donde se explica los usuarios disponibles y el flujo de trabajo.

## Inicio Rápido (Setup Inicial)
```bash
# 1. Instalar las librarias
uv sync

# 2. Aplicar las migraciones (crear la base de datos)
uv run task migrate

# 3. Crear los datos de prueba
uv run task seed

# 4. Iniciar el servidor de desarrollo
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
| `uv run task seed` | Puebla la base de datos con datos iniciales |
| `uv run task format` | Formatea el código con Ruff |
| `uv run task lint` | Analiza el código con linter Ruff |
| `uv run task lint-fix` | Corrige advertencias de lint automáticamente |

---

## Estructura del Código

```text
sis-creditos/
├── apps/          # Módulos de dominio (clientes, creditos, etc.)
├── config/        # Configuración central (settings, urls, wsgi)
├── database/      # SQLite local (ignorado por Git) y scripts seed
├── templates/     # Frontend (HTML, base.html con Tailwind)
├── static/        # CSS, JavaScript e imágenes globales
├── pyproject.toml # Dependencias y scripts del proyecto
└── .env           # Variables locales (ignorado por Git)
```

---

## Reglas para el Equipo

1. **Nunca subir `database/*.sqlite3` ni `.env`** al repositorio.
2. Cada desarrollador trabaja en su app correspondiente dentro de `apps/`.
3. Antes de abrir un PR, asegurarse de ejecutar `uv run task makemigrations` y `uv run task check`.
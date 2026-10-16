"""
================================================================================
MÓDULO: USUARIOS (apps/usuarios/urls.py)
================================================================================
¿QUÉ HACE ESTE ARCHIVO?
Es el mapa de direcciones web (rutas o URLs) del módulo de usuarios.
Le dice a Django:
"Cuando un usuario visite esta dirección en su navegador, ejecuta esta vista de views.py".

¿POR QUÉ ES NECESARIO?
Sin este archivo, Django no sabría qué pantalla mostrar al hacer clic en un enlace.
Además, el `app_name = 'usuarios'` permite usar nombres limpios en los templates,
como `{% url 'usuarios:login' %}`, sin tener que escribir las rutas a mano.
================================================================================
"""

# path: Función de Django para asociar una ruta de texto (ej: "login/") con una vista
from django.urls import path

# Importamos las vistas desde el archivo views.py de esta misma carpeta
from . import views

# Espacio de nombres (namespace) de la aplicación.
# Nos permite referirnos a estas rutas como 'usuarios:login', 'usuarios:logout', etc.
app_name = "usuarios"

urlpatterns = [
    # --------------------------------------------------------------------------
    # SESIONES DE USUARIO
    # --------------------------------------------------------------------------
    # Pantalla para ingresar usuario y contraseña: /usuarios/login/
    path("login/", views.UsuarioLoginView.as_view(), name="login"),
    # Acción para salir del sistema: /usuarios/logout/
    path("logout/", views.UsuarioLogoutView.as_view(), name="logout"),
    # Redirección rápida al panel principal: /usuarios/dashboard/
    path("dashboard/", views.dashboard_redirect_view, name="dashboard"),
    # --------------------------------------------------------------------------
    # ADMINISTRACIÓN DE EMPLEADOS (CU15 - Solo para Administradores)
    # --------------------------------------------------------------------------
    # Lista de todos los usuarios del banco: /usuarios/
    path("", views.UsuarioListView.as_view(), name="usuario_list"),
    # Formulario para registrar un nuevo empleado: /usuarios/nuevo/
    path("nuevo/", views.UsuarioCreateView.as_view(), name="usuario_create"),
    # Formulario para editar datos o rol de un empleado: /usuarios/<id>/editar/
    # Ejemplo: /usuarios/5/editar/
    path("<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="usuario_update"),
    # Pantalla de confirmación para dar de baja: /usuarios/<id>/eliminar/
    # Ejemplo: /usuarios/5/eliminar/
    path("<int:pk>/eliminar/", views.UsuarioDeleteView.as_view(), name="usuario_delete"),
    path("auditorias/", views.AuditoriaListView.as_view(), name="auditoria_list"),
]

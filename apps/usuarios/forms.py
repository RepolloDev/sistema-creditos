"""
================================================================================
MÓDULO: USUARIOS (apps/usuarios/forms.py)
================================================================================
¿QUÉ HACE ESTE ARCHIVO?
Define la estructura y validación de los formularios que el usuario llena en pantalla:
1. El formulario de inicio de sesión (`LoginForm`).
2. El formulario para dar de alta a un empleado (`UsuarioCreateForm`).
3. El formulario para modificar datos de un empleado (`UsuarioUpdateForm`).

¿POR QUÉ ES NECESARIO?
En Django, los formularios no son solo etiquetas HTML. Son inspectores de seguridad:
- Se aseguran de que ningún campo obligatorio quede vacío.
- Validan que las dos contraseñas escritas sean idénticas.
- Se encargan de llamar a `set_password()` para que la clave se guarde cifrada
  y nunca en texto plano.
- Asignan clases CSS (como bordes y colores) para que las casillas se vean bien.
================================================================================
"""

# ------------------------------------------------------------------------------
# IMPORTACIONES
# ------------------------------------------------------------------------------

# forms: El módulo de Django para crear campos de texto, selectores, casillas, etc.
from django import forms

# AuthenticationForm: El formulario base estándar de Django para iniciar sesión.
# Ya sabe cómo verificar si la clave coincide con la guardada en la base de datos.
from django.contrib.auth.forms import AuthenticationForm

# Importamos nuestro modelo Usuario
from .models import Usuario


# ------------------------------------------------------------------------------
# 1. FORMULARIO DE INICIO DE SESIÓN
# ------------------------------------------------------------------------------
class LoginForm(AuthenticationForm):
    """
    Formulario que aparece en la pantalla de login.
    Le pide al usuario su 'login' y su 'contraseña'.
    """

    # Campo para el nombre de usuario
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Ingrese su usuario",
                "autofocus": True,  # Pone el cursor en esta casilla de inmediato
            }
        ),
    )

    # Campo para la contraseña (oculta los caracteres con puntitos)
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Ingrese su contraseña",
                "autocomplete": "current-password",
            }
        ),
    )


# ------------------------------------------------------------------------------
# 2. FORMULARIO PARA CREAR UN NUEVO EMPLEADO
# ------------------------------------------------------------------------------
class UsuarioCreateForm(forms.ModelForm):
    """
    Formulario utilizado por el Administrador para dar de alta a un usuario.
    Hereda de ModelForm, lo que significa que Django crea automáticamente los campos
    basándose en las columnas de nuestro modelo `Usuario`.
    """

    # Agregamos dos campos manuales para la contraseña porque necesitamos
    # que el administrador la escriba dos veces para evitar errores de tipeo.
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Mínimo 6 caracteres",
            }
        ),
    )
    confirmar_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Repita la contraseña",
            }
        ),
    )

    class Meta:
        # Le decimos a Django a qué modelo está conectado este formulario
        model = Usuario
        # Qué columnas del modelo queremos mostrar en pantalla
        fields = ["login", "nombre_completo", "rol", "activo"]
        # Cómo se debe ver cada casilla en el navegador (clases CSS y textos de ayuda)
        widgets = {
            "login": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Nombre de usuario único",
                }
            ),
            "nombre_completo": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Nombres y Apellidos",
                }
            ),
            "rol": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                }
            ),
            "activo": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-blue-600 rounded focus:ring-blue-500",
                }
            ),
        }

    def clean(self):
        """
        Revisión de seguridad: se ejecuta antes de guardar.
        Comprueba que la contraseña y la confirmación sean exactamente iguales.
        Si no coinciden, muestra un aviso de error en la casilla.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")

        if password and confirmar_password and password != confirmar_password:
            self.add_error("confirmar_password", "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        """
        Guardado seguro:
        1. Crea el usuario en memoria sin guardarlo todavía en la base de datos (commit=False).
        2. Encripta la contraseña usando set_password().
        3. Ahora sí, lo guarda en la base de datos de manera segura.
        """
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


# ------------------------------------------------------------------------------
# 3. FORMULARIO PARA EDITAR UN EMPLEADO EXISTENTE
# ------------------------------------------------------------------------------
class UsuarioUpdateForm(forms.ModelForm):
    """
    Formulario utilizado por el Administrador para modificar datos de un usuario.
    Permite cambiar nombre, rol o deshabilitar la cuenta.
    La contraseña es OPCIONAL: solo se llena si se desea restablecer la clave.
    """

    nueva_password = forms.CharField(
        label="Nueva Contraseña (opcional)",
        required=False,  # Puede dejarse vacío si no se quiere cambiar la contraseña
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Dejar en blanco para no cambiar",
            }
        ),
    )

    class Meta:
        model = Usuario
        fields = ["login", "nombre_completo", "rol", "activo"]
        widgets = {
            "login": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                }
            ),
            "nombre_completo": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                }
            ),
            "rol": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                }
            ),
            "activo": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-blue-600 rounded focus:ring-blue-500",
                }
            ),
        }

    def save(self, commit=True):
        """
        Guarda los cambios. Si el administrador escribió algo en 'nueva_password',
        se encripta la nueva clave y se actualiza; si lo dejó vacío, la contraseña
        antigua se mantiene intacta.
        """
        usuario = super().save(commit=False)
        nueva_pass = self.cleaned_data.get("nueva_password")
        if nueva_pass:
            usuario.set_password(nueva_pass)
        if commit:
            usuario.save()
        return usuario

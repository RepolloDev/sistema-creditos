from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Usuario


class LoginForm(AuthenticationForm):
    """
    Formulario de autenticación para login.
    """

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                "placeholder": "Ingrese su usuario",
                "autofocus": True,
            }
        ),
    )
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


class UsuarioCreateForm(forms.ModelForm):
    """
    Formulario para creación de usuarios por el Administrador.
    """

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
        model = Usuario
        fields = ["login", "nombre_completo", "rol", "activo"]
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
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")

        if password and confirmar_password and password != confirmar_password:
            self.add_error("confirmar_password", "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


class UsuarioUpdateForm(forms.ModelForm):
    """
    Formulario para actualización de usuarios por el Administrador.
    Permite cambio opcional de contraseña.
    """

    nueva_password = forms.CharField(
        label="Nueva Contraseña (opcional)",
        required=False,
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
        usuario = super().save(commit=False)
        nueva_pass = self.cleaned_data.get("nueva_password")
        if nueva_pass:
            usuario.set_password(nueva_pass)
        if commit:
            usuario.save()
        return usuario

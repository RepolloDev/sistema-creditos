from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={"placeholder": "Usuario", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Contraseña"}),
    )


class UsuarioCreateForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Mínimo 6 caracteres"}),
    )
    confirmar_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Repita la contraseña"}),
    )

    class Meta:
        model = Usuario
        fields = ["login", "nombre_completo", "rol", "activo"]

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
    nueva_password = forms.CharField(
        label="Nueva Contraseña (opcional)",
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Dejar en blanco para mantener"}),
    )

    class Meta:
        model = Usuario
        fields = ["login", "nombre_completo", "rol", "activo"]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nueva_pass = self.cleaned_data.get("nueva_password")
        if nueva_pass:
            usuario.set_password(nueva_pass)
        if commit:
            usuario.save()
        return usuario

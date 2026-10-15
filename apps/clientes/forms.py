from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    """
    Formulario para alta y edición de Cliente (CU01).
    """

    class Meta:
        model = Cliente
        fields = [
            # "ci", "nombres", "apellidos", "telefono", "direccion", "ingresos_mensuales"
        ]

    def clean_ci(self):
        """Validar formato o reglas de CI."""
        pass

    def clean_ingresos_mensuales(self):
        """Validar monto no negativo."""
        pass

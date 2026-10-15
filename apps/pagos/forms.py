from django import forms

from .models import Pago


class PagoForm(forms.ModelForm):
    """
    Formulario base para CU12 / RF13: Registrar abono a cuota en ventanilla por Cajero.
    """

    class Meta:
        model = Pago
        fields = ["cuota", "monto", "forma_pago"]
        widgets = {
            "cuota": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "monto": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "step": "0.01",
                }
            ),
            "forma_pago": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
        }

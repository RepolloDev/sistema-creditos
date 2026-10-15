from django import forms

from .models import Garantia, SolicitudCredito


class SolicitudCreditoForm(forms.ModelForm):
    """
    Formulario base para RF03: Registrar solicitud de crédito.
    """

    class Meta:
        model = SolicitudCredito
        fields = ["cliente", "monto_solicitado", "plazo_meses", "destino"]
        widgets = {
            "cliente": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "monto_solicitado": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "step": "0.01",
                }
            ),
            "plazo_meses": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "destino": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Ej. Capital de trabajo, Vivienda...",
                }
            ),
        }


class GarantiaForm(forms.ModelForm):
    """
    Formulario base para RF07: Registrar garantía asociada a la solicitud.
    """

    class Meta:
        model = Garantia
        fields = ["solicitud", "tipo", "descripcion", "valor"]
        widgets = {
            "solicitud": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "tipo": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "descripcion": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "valor": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "step": "0.01",
                }
            ),
        }

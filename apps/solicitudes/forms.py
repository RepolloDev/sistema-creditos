from decimal import Decimal
from django import forms
from .models import Garantia, SolicitudCredito


class SolicitudCreditoForm(forms.ModelForm):
    """
    Formulario para CU02 / RF03: Registrar solicitud de crédito.
    """

    class Meta:
        model = SolicitudCredito
        fields = ["cliente", "monto_solicitado", "plazo_meses", "destino"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select border-dark"}),
            "monto_solicitado": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "Ej: 25000.00",
                }
            ),
            "plazo_meses": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "min": "1",
                    "max": "240",
                    "placeholder": "Ej: 24",
                }
            ),
            "destino": forms.Textarea(
                attrs={
                    "class": "form-control border-dark",
                    "rows": 3,
                    "placeholder": "Propósito detallado del financiamiento (Ej: Capital de operaciones, Ampliación de vivienda)...",
                }
            ),
        }

    def clean_monto_solicitado(self):
        monto = self.cleaned_data.get("monto_solicitado")
        if not monto or monto <= Decimal("0.00"):
            raise forms.ValidationError("El monto solicitado debe ser mayor a 0.00.")
        return monto

    def clean_plazo_meses(self):
        plazo = self.cleaned_data.get("plazo_meses")
        if not plazo or plazo < 1 or plazo > 240:
            raise forms.ValidationError("El plazo debe estar entre 1 y 240 meses.")
        return plazo


class GarantiaForm(forms.ModelForm):
    """
    Formulario para CU06 / RF07 / RN13: Registrar garantía patrimonial o personal.
    """

    class Meta:
        model = Garantia
        fields = ["tipo", "descripcion", "valor"]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select border-dark"}),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control border-dark",
                    "rows": 3,
                    "placeholder": "Detalle del bien mueble/inmueble, ubicación, placa o Folio Real / Datos del garante...",
                }
            ),
            "valor": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "Valor comercial tasado en Bs.",
                }
            ),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")
        if not valor or valor <= Decimal("0.00"):
            raise forms.ValidationError("El valor estimado debe ser mayor a 0.00 (RN13).")
        return valor

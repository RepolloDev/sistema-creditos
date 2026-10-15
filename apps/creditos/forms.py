from decimal import Decimal

from django import forms


class AprobacionCreditoForm(forms.Form):
    """
    Formulario para CU07 / RF08: Aprobación formal de crédito por Jefe de Créditos.
    """

    monto_aprobado = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "w-full px-3 py-2 border rounded-lg", "step": "0.01"}
        ),
    )
    tasa_interes_anual = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=Decimal("12.00"),
        widget=forms.NumberInput(
            attrs={"class": "w-full px-3 py-2 border rounded-lg", "step": "0.01"}
        ),
    )
    plazo_meses = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "w-full px-3 py-2 border rounded-lg"}),
    )


class RechazoCreditoForm(forms.Form):
    """
    Formulario para CU08 / RF09: Rechazo fundamentado de crédito (RN11).
    """

    motivo_rechazo = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-3 py-2 border rounded-lg",
                "rows": 4,
                "placeholder": "Ingrese el motivo formal y justificado de la denegación (obligatorio por RN11)...",
            }
        ),
        required=True,
    )

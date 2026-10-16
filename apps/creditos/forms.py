from decimal import Decimal
from django import forms


class AprobacionCreditoForm(forms.Form):
    """
    Formulario para CU07 / RF08: Aprobación formal de crédito por Jefe de Créditos.
    """

    monto_aprobado = forms.DecimalField(
        label="Monto Aprobado (Bs.)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(
            attrs={"class": "form-control border-dark font-mono", "step": "0.01"}
        ),
    )
    tasa_interes_anual = forms.DecimalField(
        label="Tasa de Interés Nominal Anual (%)",
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00"),
        initial=Decimal("14.00"),
        widget=forms.NumberInput(
            attrs={"class": "form-control border-dark font-mono", "step": "0.01"}
        ),
    )
    plazo_meses = forms.IntegerField(
        label="Plazo Definitivo (Meses)",
        min_value=1,
        max_value=240,
        widget=forms.NumberInput(attrs={"class": "form-control border-dark font-mono"}),
    )


class RechazoCreditoForm(forms.Form):
    """
    Formulario para CU08 / RF09: Rechazo fundamentado de crédito (RN11).
    """

    motivo_rechazo = forms.CharField(
        label="Motivo Formal de la Denegación (RN11)",
        widget=forms.Textarea(
            attrs={
                "class": "form-control border-dark",
                "rows": 4,
                "placeholder": "Ingrese el motivo técnico y justificado del rechazo (obligatorio según RN11)...",
            }
        ),
        required=True,
    )

    def clean_motivo_rechazo(self):
        motivo = self.cleaned_data.get("motivo_rechazo", "").strip()
        if not motivo:
            raise forms.ValidationError("El motivo de rechazo no puede estar vacío (RN11).")
        return motivo

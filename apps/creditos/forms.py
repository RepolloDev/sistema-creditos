from decimal import Decimal
from django import forms


class AprobacionCreditoForm(forms.Form):
    monto_aprobado = forms.DecimalField(
        label="Monto Aprobado (Bs.)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )
    tasa_interes_anual = forms.DecimalField(
        label="Tasa de Interés Anual (%)",
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00"),
        initial=Decimal("14.00"),
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )
    plazo_meses = forms.IntegerField(
        label="Plazo (Meses)",
        min_value=1,
        max_value=240,
    )


class RechazoCreditoForm(forms.Form):
    motivo_rechazo = forms.CharField(
        label="Motivo del Rechazo",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
    )

    def clean_motivo_rechazo(self):
        motivo = self.cleaned_data.get("motivo_rechazo", "").strip()
        if not motivo:
            raise forms.ValidationError("El motivo de rechazo es obligatorio.")
        return motivo

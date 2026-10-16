from decimal import Decimal
from django import forms
from solicitudes.models import SolicitudCredito
from .models import EvaluacionCredito


class EvaluacionCreditoForm(forms.ModelForm):
    """
    Formulario para CU04 / CU05: Evaluación técnica de capacidad de pago y riesgo.
    """

    class Meta:
        model = EvaluacionCredito
        fields = [
            "solicitud",
            "ingresos",
            "gastos",
            "capacidad_pago",
            "nivel_riesgo",
            "resultado",
            "observaciones",
        ]
        widgets = {
            "solicitud": forms.Select(attrs={"class": "form-select border-dark"}),
            "ingresos": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "step": "0.01",
                    "min": "0.00",
                    "id": "id_ingresos",
                }
            ),
            "gastos": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "step": "0.01",
                    "min": "0.00",
                    "id": "id_gastos",
                }
            ),
            "capacidad_pago": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono bg-light",
                    "step": "0.01",
                    "readonly": "readonly",
                    "id": "id_capacidad_pago",
                }
            ),
            "nivel_riesgo": forms.Select(attrs={"class": "form-select border-dark"}),
            "resultado": forms.Select(attrs={"class": "form-select border-dark"}),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control border-dark",
                    "rows": 3,
                    "placeholder": "Fundamento técnico de la recomendación emitida por el analista...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["capacidad_pago"].required = False

    def clean(self):
        cleaned_data = super().clean()
        ingresos = cleaned_data.get("ingresos") or Decimal("0.00")
        gastos = cleaned_data.get("gastos") or Decimal("0.00")
        cleaned_data["capacidad_pago"] = ingresos - gastos
        return cleaned_data

from django import forms

from .models import EvaluacionCredito


class EvaluacionCreditoForm(forms.ModelForm):
    """
    Formulario base para CU04 / CU05: Evaluación técnica y de riesgo crediticio.
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
            "solicitud": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "ingresos": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "step": "0.01",
                }
            ),
            "gastos": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "step": "0.01",
                }
            ),
            "capacidad_pago": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "step": "0.01",
                }
            ),
            "nivel_riesgo": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "resultado": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500",
                    "rows": 3,
                }
            ),
        }

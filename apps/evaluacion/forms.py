from decimal import Decimal
from django import forms
from .models import EvaluacionCredito


class EvaluacionCreditoForm(forms.ModelForm):
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
            "ingresos": forms.NumberInput(attrs={"step": "0.01", "min": "0.00", "id": "id_ingresos"}),
            "gastos": forms.NumberInput(attrs={"step": "0.01", "min": "0.00", "id": "id_gastos"}),
            "capacidad_pago": forms.NumberInput(attrs={"step": "0.01", "readonly": True, "id": "id_capacidad_pago"}),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["capacidad_pago"].required = False
        from django.db.models import Q
        from solicitudes.models import SolicitudCredito

        qs = SolicitudCredito.objects.select_related("cliente").filter(
            estado__in=["REGISTRADA", "EN_EVALUACION"]
        )
        if self.instance and self.instance.pk:
            qs = qs.filter(Q(evaluacion__isnull=True) | Q(pk=self.instance.solicitud_id))
        else:
            qs = qs.filter(evaluacion__isnull=True)
        self.fields["solicitud"].queryset = qs.order_by("-id")
        self.fields["solicitud"].label_from_instance = (
            lambda s: f"Solicitud #{s.pk} — {s.cliente.apellidos}, {s.cliente.nombres} (Bs. {s.monto_solicitado:.2f})"
        )

    def clean(self):
        cleaned_data = super().clean()
        ingresos = cleaned_data.get("ingresos") or Decimal("0.00")
        gastos = cleaned_data.get("gastos") or Decimal("0.00")
        cleaned_data["capacidad_pago"] = ingresos - gastos
        return cleaned_data

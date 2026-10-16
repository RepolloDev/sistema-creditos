from decimal import Decimal
from django import forms
from .models import Garantia, SolicitudCredito


class SolicitudCreditoForm(forms.ModelForm):
    class Meta:
        model = SolicitudCredito
        fields = ["cliente", "monto_solicitado", "plazo_meses", "destino"]
        widgets = {
            "monto_solicitado": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "plazo_meses": forms.NumberInput(attrs={"min": "1", "max": "240"}),
            "destino": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from clientes.models import Cliente
        self.fields["cliente"].queryset = Cliente.objects.order_by("apellidos", "nombres")
        self.fields["cliente"].label_from_instance = (
            lambda c: f"{c.apellidos}, {c.nombres} ({c.ci})"
        )

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
    class Meta:
        model = Garantia
        fields = ["tipo", "descripcion", "valor"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
            "valor": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")
        if not valor or valor <= Decimal("0.00"):
            raise forms.ValidationError("El valor estimado debe ser mayor a 0.00.")
        return valor

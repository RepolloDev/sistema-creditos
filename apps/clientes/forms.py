from decimal import Decimal
from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["ci", "nombres", "apellidos", "telefono", "direccion", "ingresos_mensuales"]
        widgets = {
            "ingresos_mensuales": forms.NumberInput(attrs={"step": "0.01", "min": "0.00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["ci"].widget.attrs["readonly"] = True

    def clean_ci(self):
        ci = self.cleaned_data.get("ci", "").strip()
        if not ci:
            raise forms.ValidationError("La Cédula de Identidad es obligatoria.")
        if self.instance and self.instance.pk:
            return self.instance.ci
        if Cliente.objects.filter(ci__iexact=ci).exists():
            raise forms.ValidationError(f"Ya existe un cliente con el CI '{ci}'.")
        return ci

    def clean_ingresos_mensuales(self):
        ingresos = self.cleaned_data.get("ingresos_mensuales")
        if ingresos is None or ingresos < Decimal("0.00"):
            raise forms.ValidationError("Los ingresos mensuales deben ser mayores o iguales a 0.00.")
        return ingresos

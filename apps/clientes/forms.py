from decimal import Decimal
from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    """
    Formulario para alta y edición de Cliente (CU01 / RF01 / RF02).
    """

    class Meta:
        model = Cliente
        fields = [
            "ci",
            "nombres",
            "apellidos",
            "telefono",
            "direccion",
            "ingresos_mensuales",
        ]
        widgets = {
            "ci": forms.TextInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "placeholder": "Ej: 4892104 LP",
                }
            ),
            "nombres": forms.TextInput(
                attrs={
                    "class": "form-control border-dark",
                    "placeholder": "Nombres del solicitante",
                }
            ),
            "apellidos": forms.TextInput(
                attrs={
                    "class": "form-control border-dark",
                    "placeholder": "Apellidos del solicitante",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "placeholder": "Ej: 71542890",
                }
            ),
            "direccion": forms.TextInput(
                attrs={
                    "class": "form-control border-dark",
                    "placeholder": "Zona, Avenida/Calle y Número",
                }
            ),
            "ingresos_mensuales": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "step": "0.01",
                    "min": "0.00",
                    "placeholder": "0.00",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el cliente ya existe, bloquear edición de CI (RN01)
        if self.instance and self.instance.pk:
            self.fields["ci"].widget.attrs["readonly"] = True

    def clean_ci(self):
        ci = self.cleaned_data.get("ci", "").strip()
        if not ci:
            raise forms.ValidationError("La Cédula de Identidad es obligatoria.")
        if self.instance and self.instance.pk:
            return self.instance.ci
        if Cliente.objects.filter(ci__iexact=ci).exists():
            raise forms.ValidationError(f"Ya existe un cliente registrado con el CI '{ci}' (RN01).")
        return ci

    def clean_ingresos_mensuales(self):
        ingresos = self.cleaned_data.get("ingresos_mensuales")
        if ingresos is None or ingresos < Decimal("0.00"):
            raise forms.ValidationError("Los ingresos mensuales deben ser mayores o iguales a 0.00.")
        return ingresos

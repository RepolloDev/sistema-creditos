from decimal import Decimal
from django import forms
from creditos.models import Cuota
from .models import Pago


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["cuota", "monto", "forma_pago"]
        widgets = {
            "monto": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        credito_id = kwargs.pop("credito_id", None)
        super().__init__(*args, **kwargs)
        qs = (
            Cuota.objects.select_related("credito", "credito__solicitud__cliente")
            .exclude(estado="PAGADA")
            .order_by("credito__numero_credito", "numero_cuota")
        )
        if credito_id:
            qs = qs.filter(credito_id=credito_id)
        self.fields["cuota"].queryset = qs
        self.fields["cuota"].label_from_instance = (
            lambda obj: f"{obj.credito.numero_credito} - Cuota #{obj.numero_cuota} (Bs. {obj.saldo_cuota}) - {obj.credito.solicitud.cliente.apellidos}"
        )

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if not monto or monto <= Decimal("0.00"):
            raise forms.ValidationError("El monto debe ser mayor a 0.00.")
        return monto

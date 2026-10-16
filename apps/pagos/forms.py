from decimal import Decimal
from django import forms
from creditos.models import Cuota
from .models import Pago


class PagoForm(forms.ModelForm):
    """
    Formulario para CU12 / RF13: Registrar abono a cuota en ventanilla por Cajero.
    """

    class Meta:
        model = Pago
        fields = ["cuota", "monto", "forma_pago"]
        widgets = {
            "cuota": forms.Select(attrs={"class": "form-select border-dark font-mono", "id": "id_cuota"}),
            "monto": forms.NumberInput(
                attrs={
                    "class": "form-control border-dark font-mono",
                    "step": "0.01",
                    "min": "0.01",
                    "id": "id_monto",
                    "placeholder": "Monto recibido en Bs.",
                }
            ),
            "forma_pago": forms.Select(attrs={"class": "form-select border-dark"}),
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
            lambda obj: f"{obj.credito.numero_credito} | Cuota #{obj.numero_cuota} (Vence: {obj.fecha_vencimiento.strftime('%d/%m/%Y')}) - Saldo: Bs. {obj.saldo_cuota} [{obj.get_estado_display()}] - {obj.credito.solicitud.cliente.nombres} {obj.credito.solicitud.cliente.apellidos}"
        )

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if not monto or monto <= Decimal("0.00"):
            raise forms.ValidationError("RN07: El monto abonado debe ser mayor a 0.00.")
        return monto

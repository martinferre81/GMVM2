from django import forms
from .models import Reclamo, Contribuyente


class ReclamoForm(forms.ModelForm):
    id_contribuyente = forms.ModelChoiceField(
        queryset=Contribuyente.objects.all().order_by('apellido'),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm select2-modal'
        })
    )

    class Meta:
        model = Reclamo
        fields = [
            "id_contribuyente",
            "titulo",
            "descripcion",
            "tipo_reclamo",
            "estado",
            "prioridad"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 👇 SOLO deshabilitar si es edición
        if self.instance and self.instance.pk:
            self.fields["id_contribuyente"].disabled = True

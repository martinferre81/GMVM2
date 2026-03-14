from django import forms
from .models import Reclamo
class ReclamoForm(forms.ModelForm):

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

            # Deshabilitar el contribuyente cuando se edita
            self.fields["id_contribuyente"].disabled = True


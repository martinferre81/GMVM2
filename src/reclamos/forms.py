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
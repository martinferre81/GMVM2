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
            "descripcion",
            "tipo_reclamo",
            "estado",
            "prioridad",
            "direccion",
            'entre_calle_1',
            'entre_calle_2'
        ]
        widgets = {
        "descripcion": forms.Textarea(attrs={
            "class": "form-control form-control-sm",
            "style": "min-height: 50px;",
            "rows": 3
        }),
        "tipo_reclamo": forms.Select(attrs={
            "class": "form-select form-select-sm"
        }),
        "estado": forms.Select(attrs={
            "class": "form-select form-select-sm"
        }),
        "prioridad": forms.Select(attrs={
            "class": "form-select form-select-sm"
        }),
        'entre_calle_1': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        'entre_calle_2': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
    }

    def __init__(self, *args, **kwargs):
        es_admin = kwargs.pop('es_admin', False)
        super().__init__(*args, **kwargs)
        self.fields['id_contribuyente'].required = False

        # 🔒 Permisos (NO ADMIN)
        if not es_admin and self.instance and self.instance.pk:
            self.fields['descripcion'].disabled = True
            self.fields['tipo_reclamo'].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.titulo = ""
        if commit:
            instance.save()
        return instance

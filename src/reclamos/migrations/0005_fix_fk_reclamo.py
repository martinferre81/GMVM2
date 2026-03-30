from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('reclamos', '0004_create_contribuyente_prod'),  # la migración que creó Contribuyente
    ]

    operations = [
        # Si el campo id_contribuyente ya existe, lo alteramos a ForeignKey
        migrations.AlterField(
            model_name='reclamo',
            name='id_contribuyente',
            field=models.ForeignKey(
                to='reclamos.contribuyente',
                on_delete=models.CASCADE,
                null=True,  # si tus datos actuales pueden tener valores nulos
                blank=True,
            ),
        ),
    ]

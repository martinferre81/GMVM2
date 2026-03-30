from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('reclamos', '0003_fix_fk_prod'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contribuyente',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('dni', models.CharField(max_length=15, unique=True)),
                ('apellido', models.CharField(max_length=100)),
                ('nombres', models.CharField(max_length=100)),
                ('telefono', models.CharField(max_length=30, blank=True)),
                ('email', models.EmailField(blank=True)),
                ('fecha_alta', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

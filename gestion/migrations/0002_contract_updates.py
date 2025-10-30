from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrat',
            name='date_rupture',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contrat',
            name='motif_rupture',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contrat',
            name='frais_rupture',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='vehicule',
            name='kilometrage',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='vehicule',
            name='date_derniere_maintenance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vehicule',
            name='prochaine_maintenance',
            field=models.DateField(blank=True, null=True),
        ),
    ]
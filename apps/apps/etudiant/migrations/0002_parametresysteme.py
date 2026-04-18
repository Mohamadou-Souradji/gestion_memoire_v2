from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etudiant', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParametreSysteme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taux_ia_max', models.IntegerField(default=10, help_text='Taux IA maximum autorisé (%). Au-delà, le document est rejeté.')),
                ('seuil_similarite_theme', models.IntegerField(default=10, help_text='Seuil de similarité des thèmes (%). En-dessous, la proposition est acceptée.')),
                ('otp_actif', models.BooleanField(default=True, help_text='Activer la double authentification (OTP par e-mail).')),
                ('mis_a_jour', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Paramètre système',
                'verbose_name_plural': 'Paramètres système',
            },
        ),
    ]

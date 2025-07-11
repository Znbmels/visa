# Generated by Django 5.2.1 on 2025-05-17 06:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_visaapplication_admin_comments_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VisaFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visa_type', models.CharField(choices=[('tourist', 'Tourist'), ('work', 'Work'), ('study', 'Study'), ('business', 'Business')], max_length=20, verbose_name='Visa Type')),
                ('consular_fee', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Consular Fee')),
                ('service_fee', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Service Fee')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.country', verbose_name='Country')),
            ],
        ),
    ]

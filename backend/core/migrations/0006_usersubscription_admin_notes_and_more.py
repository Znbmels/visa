# Generated by Django 5.2.1 on 2025-06-02 09:59

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_currencyrate_faq_language_service_subscription_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='admin_notes',
            field=models.TextField(blank=True, help_text='Заметки администратора при одобрении/отклонении'),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='applied_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='processed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='status',
            field=models.CharField(choices=[('pending', 'В ожидании одобрения'), ('approved', 'Одобрена'), ('rejected', 'Отклонена'), ('expired', 'Истекла'), ('cancelled', 'Отменена')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

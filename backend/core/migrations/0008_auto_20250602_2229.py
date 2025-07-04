# Generated by Django 5.2.1 on 2025-06-02 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_usersubscription_applied_at'),
    ]

    operations = [
        # Удаляем старое уникальное ограничение
        migrations.RunSQL(
            "ALTER TABLE core_usersubscription DROP CONSTRAINT IF EXISTS core_usersubscription_user_id_key;",
            reverse_sql="",
        ),
        # Добавляем новое условное ограничение
        migrations.AddConstraint(
            model_name='usersubscription',
            constraint=models.UniqueConstraint(
                condition=models.Q(status__in=['pending', 'approved'], is_active=True),
                fields=['user'],
                name='unique_active_subscription',
            ),
        ),
    ]

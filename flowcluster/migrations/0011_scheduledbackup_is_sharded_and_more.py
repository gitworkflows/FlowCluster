# Generated by Django 4.1.1 on 2024-01-31 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowcluster', '0010_scheduledbackup_incremental_schedule_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledbackup',
            name='is_sharded',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='scheduledbackup',
            name='table',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

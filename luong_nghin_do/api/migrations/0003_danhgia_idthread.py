# Generated by Django 5.1.7 on 2025-03-15 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_chude_danhgia_file_userdetail_delete_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='danhgia',
            name='idThread',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]

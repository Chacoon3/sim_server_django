# Generated by Django 4.1.6 on 2023-07-28 00:37

import bmgt435_platform.bmgtModels
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmgt435_platform', '0006_rename_user_activated_bmgtuser_activated_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bmgtuser',
            name='activated',
            field=models.IntegerField(default=0,),
        ),
    ]

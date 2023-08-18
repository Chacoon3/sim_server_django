# Generated by Django 4.1.6 on 2023-08-14 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmgt435_platform', '0018_alter_bmgtcase_visible_alter_bmgtuser_activated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bmgtcase',
            name='flag_deleted',
        ),
        migrations.RemoveField(
            model_name='bmgtcaseconfig',
            name='flag_deleted',
        ),
        migrations.RemoveField(
            model_name='bmgtcaserecord',
            name='flag_deleted',
        ),
        migrations.RemoveField(
            model_name='bmgtgroup',
            name='flag_deleted',
        ),
        migrations.RemoveField(
            model_name='bmgttag',
            name='flag_deleted',
        ),
        migrations.RemoveField(
            model_name='bmgttagged',
            name='flag_deleted',
        ),
        migrations.RemoveField(
            model_name='bmgtuser',
            name='flag_deleted',
        ),
        migrations.AlterField(
            model_name='bmgtcase',
            name='visible',
            field=models.IntegerField(default=1, verbose_name=[(0, 'False'), (1, 'True')]),
        ),
        migrations.AlterField(
            model_name='bmgtuser',
            name='activated',
            field=models.IntegerField(choices=[(0, 'False'), (1, 'True')], default=0),
        ),
        migrations.AlterField(
            model_name='bmgtuser',
            name='did',
            field=models.CharField(max_length=60, unique=True),
        ),
    ]
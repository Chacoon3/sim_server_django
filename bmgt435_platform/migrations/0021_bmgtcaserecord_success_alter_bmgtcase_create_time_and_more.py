# Generated by Django 4.1.6 on 2023-08-15 20:11

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bmgt435_platform', '0020_delete_bmgtcaseconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='bmgtcaserecord',
            name='success',
            field=models.IntegerField(default=1, verbose_name=[(0, 'False'), (1, 'True')]),
        ),
        migrations.AlterField(
            model_name='bmgtcase',
            name='create_time',
            field=models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='bmgtcaserecord',
            name='create_time',
            field=models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='bmgtgroup',
            name='create_time',
            field=models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='bmgttag',
            name='create_time',
            field=models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='bmgttagged',
            name='create_time',
            field=models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='bmgtuser',
            name='create_time',
            field=models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
        ),
        migrations.CreateModel(
            name='CaseConfig',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('config_json', models.TextField(default='')),
                ('case_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bmgt435_platform.bmgtcase')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

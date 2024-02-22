# Generated by Django 4.2.1 on 2023-11-28 18:08

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bmgt435_elp', '0002_bmgtcaseconfig_edited_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='BMGTSystemStatus',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('allow_join_group', models.BooleanField(default=True)),
                ('allow_user_login', models.BooleanField(default=True)),
                ('allow_case_submit', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='bmgtgroup',
            name='is_frozen',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='bmgtgroup',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='bmgt435_elp.bmgtsemester'),
        ),
    ]
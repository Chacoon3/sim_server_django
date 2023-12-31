# Generated by Django 4.2.1 on 2023-09-29 00:57

import bmgt435_elp.bmgtModels
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BMGTCase',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=50)),
                ('visible', models.BooleanField(default=True)),
                ('max_submission', models.IntegerField(default=5)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BMGTGroup',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('number', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BMGTSemester',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('year', models.IntegerField()),
                ('season', models.CharField(choices=[('spring', 'spring'), ('summer', 'summer'), ('fall', 'fall')], max_length=10)),
            ],
            options={
                'unique_together': {('year', 'season')},
            },
        ),
        migrations.CreateModel(
            name='BMGTUser',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('did', models.CharField(max_length=60, unique=True)),
                ('first_name', models.CharField(max_length=60)),
                ('last_name', models.CharField(max_length=60)),
                ('password', models.CharField(default='', max_length=100)),
                ('activated', models.IntegerField(choices=[(0, 'False'), (1, 'True')], default=0)),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('user', 'User')], default='user', max_length=5)),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtgroup')),
                ('semester', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtsemester')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('activity', models.CharField(choices=[('sign-in', 'sign-in'), ('sign-up', 'sign-up'), ('sign-out', 'sign-out'), ('forget-password', 'forget-password'), ('submit-case', 'submit-case')], max_length=20)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtuser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CaseConfig',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('config_json', models.TextField(default='')),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bmgt435_elp.bmgtcase')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='bmgtgroup',
            name='semeter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtsemester'),
        ),
        migrations.CreateModel(
            name='BMGTFeedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('content', models.TextField(default='')),
                ('user_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtuser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BMGTCaseRecord',
            fields=[
                ('create_time', models.DateTimeField(auto_created=True, default=django.utils.timezone.now)),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('score', models.FloatField(default=None, null=True)),
                ('state', models.IntegerField(default=0, verbose_name=[(0, 'Running'), (1, 'Success'), (2, 'Failed')])),
                ('summary_dict', models.TextField(default='')),
                ('file_name', models.CharField(editable=False, max_length=30, unique=True)),
                ('case', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtcase')),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtgroup')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bmgt435_elp.bmgtuser')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

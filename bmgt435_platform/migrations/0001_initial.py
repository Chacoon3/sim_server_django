# Generated by Django 4.1.6 on 2023-07-25 19:33

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BMGTGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(default='', max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=50)),
                ('case_description', models.TextField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(default='', max_length=10)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(default='', max_length=10)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CaseRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('case_record_status', models.IntegerField(default=0)),
                ('case_record_score', models.FloatField(default=0.0)),
                ('case_record_detail_json', models.TextField(null=True)),
                ('case_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bmgt435_platform.case')),
                ('group_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bmgt435_platform.bmgtgroup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BMGTUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('user_did', models.CharField(max_length=100)),
                ('user_first_name', models.CharField(max_length=60, null=True)),
                ('user_last_name', models.CharField(max_length=60, null=True)),
                ('user_password', models.CharField(default='', max_length=100)),
                ('user_activated', models.BooleanField(default=False)),
                ('group_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bmgt435_platform.bmgtgroup')),
                ('role_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bmgt435_platform.role')),
                ('tag_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bmgt435_platform.tag')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

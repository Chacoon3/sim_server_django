# Generated by Django 4.2.1 on 2023-11-16 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmgt435_elp', '0007_alter_bmgtgroup_semester'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='bmgtsemester',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='bmgtsemester',
            constraint=models.UniqueConstraint(fields=('year', 'season'), name='unique_semester'),
        ),
        migrations.AddConstraint(
            model_name='bmgtsemester',
            constraint=models.CheckConstraint(check=models.Q(('year__gte', 2022)), name='year_constraint'),
        ),
        migrations.AddConstraint(
            model_name='bmgtsemester',
            constraint=models.CheckConstraint(check=models.Q(('season__in', ['spring', 'summer', 'fall'])), name='season_constraint'),
        ),
    ]

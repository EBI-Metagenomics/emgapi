# Generated by Django 3.2.18 on 2023-09-14 07:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0013_delete_analysisjobann'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisjob',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed'), (100, 'Ancestor Suppressed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='assembly',
            name='study',
            field=models.ForeignKey(blank=True, db_column='STUDY_ID', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assemblies', to='emgapi.study'),
        ),
        migrations.AlterField(
            model_name='assembly',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed'), (100, 'Ancestor Suppressed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='run',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed'), (100, 'Ancestor Suppressed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed'), (100, 'Ancestor Suppressed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed'), (100, 'Ancestor Suppressed')], db_column='SUPPRESSION_REASON', null=True),
        ),
    ]

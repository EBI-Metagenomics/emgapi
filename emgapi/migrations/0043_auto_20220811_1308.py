# Generated by Django 3.2.12 on 2022-08-11 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0042_auto_20220722_0745'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisjob',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='assembly',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='run',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed')], db_column='SUPPRESSION_REASON', null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='suppression_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Draft'), (3, 'Cancelled'), (5, 'Suppressed'), (6, 'Killed'), (7, 'Temporary Suppressed'), (8, 'Temporary Killed')], db_column='SUPPRESSION_REASON', null=True),
        ),
    ]
# Generated by Django 3.2.18 on 2024-01-29 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0016_auto_20240117_1757'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisjob',
            name='last_indexed',
            field=models.DateTimeField(blank=True, db_column='LAST_EBI_SEARCH_INDEXED', help_text='Date at which this model was last included in an EBI Search initial/incremental index.', null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='last_indexed',
            field=models.DateTimeField(blank=True, db_column='LAST_EBI_SEARCH_INDEXED', help_text='Date at which this model was last included in an EBI Search initial/incremental index.', null=True),
        ),
        migrations.RenameField(
            model_name='analysisjob',
            old_name='last_indexed',
            new_name='last_ebi_search_indexed',
        ),
        migrations.RenameField(
            model_name='study',
            old_name='last_indexed',
            new_name='last_ebi_search_indexed',
        ),
        migrations.AddField(
            model_name='analysisjob',
            name='last_mgx_indexed',
            field=models.DateTimeField(blank=True, db_column='LAST_MGX_INDEXED', help_text='Date at which this model was last indexed in the Metagenomics Exchange', null=True),
        ),
        migrations.AddField(
            model_name='analysisjob',
            name='mgx_accession',
            field=models.CharField(blank=True, db_column='MGX_ACCESSION', help_text='The Metagenomics Exchange accession.', max_length=10, null=True, unique=True),
        ),
    ]

# Generated by Django 3.2.12 on 2022-10-31 15:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0004_genome_catalogues_last_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisjob',
            name='pipeline',
            field=models.ForeignKey(blank=True, db_column='PIPELINE_ID', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='analyses', to='emgapi.pipeline'),
        ),
        migrations.AlterField(
            model_name='sampleann',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='studypublication',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name='AssemblyExtraAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('realname', models.CharField(db_column='REAL_NAME', max_length=255)),
                ('alias', models.CharField(db_column='ALIAS', max_length=255)),
                ('file_checksum', models.CharField(blank=True, db_column='CHECKSUM', max_length=255)),
                ('assembly', models.ForeignKey(db_column='ASSEMBLY_ID', on_delete=django.db.models.deletion.CASCADE, related_name='extra_annotations', to='emgapi.assembly')),
                ('checksum_algorithm', models.ForeignKey(blank=True, db_column='CHECKSUM_ALGORITHM', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.checksumalgorithm')),
                ('description', models.ForeignKey(blank=True, db_column='DESCRIPTION_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.downloaddescriptionlabel')),
                ('file_format', models.ForeignKey(blank=True, db_column='FORMAT_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.fileformat')),
                ('group_type', models.ForeignKey(blank=True, db_column='GROUP_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.downloadgrouptype')),
                ('parent_id', models.ForeignKey(blank=True, db_column='PARENT_DOWNLOAD_ID', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='emgapi.assemblyextraannotation')),
                ('subdir', models.ForeignKey(blank=True, db_column='SUBDIR_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.downloadsubdir')),
            ],
            options={
                'db_table': 'ASSEMBLY_DOWNLOAD',
                'ordering': ('group_type', 'alias'),
                'unique_together': {('realname', 'alias', 'assembly')},
            },
        ),
    ]
# Generated by Django 3.2.18 on 2023-07-17 13:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0009_genome_annotations_v2_downloads'),
    ]

    operations = [
        migrations.CreateModel(
            name='RunExtraAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('realname', models.CharField(db_column='REAL_NAME', max_length=255)),
                ('alias', models.CharField(db_column='ALIAS', max_length=255)),
                ('file_checksum', models.CharField(blank=True, db_column='CHECKSUM', max_length=255)),
                ('checksum_algorithm', models.ForeignKey(blank=True, db_column='CHECKSUM_ALGORITHM', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.checksumalgorithm')),
                ('description', models.ForeignKey(blank=True, db_column='DESCRIPTION_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.downloaddescriptionlabel')),
                ('file_format', models.ForeignKey(blank=True, db_column='FORMAT_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.fileformat')),
                ('group_type', models.ForeignKey(blank=True, db_column='GROUP_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.downloadgrouptype')),
                ('parent_id', models.ForeignKey(blank=True, db_column='PARENT_DOWNLOAD_ID', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='emgapi.runextraannotation')),
                ('run', models.ForeignKey(db_column='RUN_ID', on_delete=django.db.models.deletion.CASCADE, related_name='extra_annotations', to='emgapi.run')),
                ('subdir', models.ForeignKey(blank=True, db_column='SUBDIR_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.downloadsubdir')),
            ],
            options={
                'db_table': 'RUN_DOWNLOAD',
                'ordering': ('group_type', 'alias'),
                'unique_together': {('realname', 'alias', 'run')},
            },
        ),
    ]

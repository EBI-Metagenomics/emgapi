# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-27 13:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emgapi', '0005_study_sample_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='pipeline',
            name='tools',
            field=models.ManyToManyField(related_name='pipelines', through='emgapi.PipelineReleaseTool', to='emgapi.PipelineTool'),
        ),
        migrations.AddField(
            model_name='study',
            name='publications',
            field=models.ManyToManyField(related_name='studies', through='emgapi.StudyPublication', to='emgapi.Publication'),
        ),
        migrations.AddField(
            model_name='study',
            name='samples',
            field=models.ManyToManyField(blank=True, related_name='studies', through='emgapi.StudySample', to='emgapi.Sample'),
        ),

        migrations.AlterField(
            model_name='pipeline',
            name='pipeline_id',
            field=models.SmallIntegerField(db_column='PIPELINE_ID', primary_key=True, serialize=False),
        ),

        migrations.CreateModel(
            name='AnalysisJobDownload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subdir', models.CharField(db_column='SUBDIR', max_length=255)),
                ('realname', models.CharField(db_column='REAL_NAME', max_length=255)),
                ('alias', models.CharField(db_column='ALIAS', max_length=255)),
                ('description', models.TextField(db_column='DESCRIPTION')),
            ],
            options={
                'db_table': 'ANALYSIS_JOB_DOWNLOAD',
            },
        ),
        migrations.CreateModel(
            name='DownloadGroupType',
            fields=[
                ('group_id', models.AutoField(db_column='GROUP_ID', primary_key=True, serialize=False)),
                ('group_type', models.CharField(db_column='GROUP_TYPE', max_length=30)),
            ],
            options={
                'db_table': 'DOWNLOAD_GROUP_TYPE',
            },
        ),
        migrations.CreateModel(
            name='FileFormat',
            fields=[
                ('format_id', models.AutoField(db_column='FORMAT_ID', primary_key=True, serialize=False)),
                ('format_name', models.CharField(db_column='FORMAT_NAME', max_length=30)),
                ('format_extention', models.CharField(db_column='FORMAT_EXTENTION', max_length=30)),
            ],
            options={
                'db_table': 'FILE_FORMAT',
            },
        ),
        migrations.CreateModel(
            name='StudyDownload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subdir', models.CharField(db_column='SUBDIR', max_length=255)),
                ('realname', models.CharField(db_column='REAL_NAME', max_length=255)),
                ('alias', models.CharField(db_column='ALIAS', max_length=255)),
                ('description', models.TextField(db_column='DESCRIPTION')),
                ('file_format', models.ForeignKey(blank=True, db_column='FORMAT_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.FileFormat')),
                ('group_type', models.ForeignKey(blank=True, db_column='GROUP_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadGroupType')),
                ('parent_id', models.ForeignKey(blank=True, db_column='PARENT_DOWNLOAD_ID', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='emgapi.StudyDownload')),
            ],
            options={
                'db_table': 'STUDY_DOWNLOAD',
            },
        ),

        migrations.AddField(
            model_name='studydownload',
            name='pipeline',
            field=models.ForeignKey(blank=True, db_column='PIPELINE_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.Pipeline'),
        ),
        migrations.AddField(
            model_name='studydownload',
            name='study',
            field=models.ForeignKey(db_column='STUDY_ID', on_delete=django.db.models.deletion.CASCADE, related_name='study_download', to='emgapi.Study'),
        ),
        migrations.AddField(
            model_name='analysisjobdownload',
            name='file_format',
            field=models.ForeignKey(blank=True, db_column='FORMAT_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.FileFormat'),
        ),
        migrations.AddField(
            model_name='analysisjobdownload',
            name='group_type',
            field=models.ForeignKey(blank=True, db_column='GROUP_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.DownloadGroupType'),
        ),
        migrations.AddField(
            model_name='analysisjobdownload',
            name='job',
            field=models.ForeignKey(db_column='JOB_ID', on_delete=django.db.models.deletion.CASCADE, related_name='analysis_download', to='emgapi.AnalysisJob'),
        ),
        migrations.AddField(
            model_name='analysisjobdownload',
            name='parent_id',
            field=models.ForeignKey(blank=True, db_column='PARENT_DOWNLOAD_ID', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='emgapi.AnalysisJobDownload'),
        ),
        migrations.AddField(
            model_name='analysisjobdownload',
            name='pipeline',
            field=models.ForeignKey(blank=True, db_column='PIPELINE_ID', null=True, on_delete=django.db.models.deletion.CASCADE, to='emgapi.Pipeline'),
        ),
        migrations.AlterUniqueTogether(
            name='studydownload',
            unique_together=set([('realname', 'alias')]),
        ),
        migrations.AlterUniqueTogether(
            name='analysisjobdownload',
            unique_together=set([('realname', 'alias')]),
        ),
    ]

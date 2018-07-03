#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create,
#     modify, and delete the table
# Feel free to rename the models, but don't rename db_table values
# or field names.

from __future__ import unicode_literals

from django.db import models
from django.db.models import Count
from django.db.models import CharField, Value
from django.db.models.functions import Concat, Cast
from django.db.models import Q
from django.db.models import Prefetch


class Resource(object):

    def __init__(self, **kwargs):
        for field in ('id', 'resource', 'count'):
            setattr(self, field, kwargs.get(field, None))


class Token(object):

    def __init__(self, **kwargs):
        for field in ('id', 'token'):
            setattr(self, field, kwargs.get(field, None))


class BaseQuerySet(models.QuerySet):

    def available(self, request=None):
        _query_filters = {
            'StudyQuerySet': {
                'all': [Q(is_public=1), ],
            },
            'StudyDownloadQuerySet': {
                'all': [Q(study__is_public=1), ],
            },
            'SampleQuerySet': {
                'all': [Q(is_public=1), ],
            },
            'RunQuerySet': {
                'all': [
                    Q(status_id=4),
                ],
            },
            'AnalysisJobQuerySet': {
                'all': [
                    Q(run__status_id=4),
                    Q(analysis_status_id=3) | Q(analysis_status_id=6)
                ],
            },
            'AnalysisJobDownloadQuerySet': {
                'all': [
                    Q(job__run__status_id=4),
                    Q(job__analysis_status_id=3) | Q(job__analysis_status_id=6)
                ],
            },
        }

        if request is not None and request.user.is_authenticated():
            _username = request.user.username
            _query_filters['StudyQuerySet']['authenticated'] = \
                [Q(submission_account_id=_username) | Q(is_public=1)]
            _query_filters['StudyDownloadQuerySet']['authenticated'] = \
                [Q(study__submission_account_id=_username) |
                 Q(study__is_public=1)]
            _query_filters['SampleQuerySet']['authenticated'] = \
                [Q(submission_account_id=_username) | Q(is_public=1)]
            _query_filters['RunQuerySet']['authenticated'] = \
                [Q(study__submission_account_id=_username, status_id=2) |
                 Q(status_id=4)]
            _query_filters['AnalysisJobQuerySet']['authenticated'] = \
                [Q(study__submission_account_id=_username, run__status_id=2) |
                 Q(run__status_id=4)]
            _query_filters['AnalysisJobDownloadQuerySet']['authenticated'] = \
                [Q(job__study__submission_account_id=_username,
                   job__run__status_id=2) |
                 Q(job__run__status_id=4)]

        q = list()
        try:
            _instance = _query_filters[self.__class__.__name__]
            if isinstance(self, self.__class__):
                if request is not None and request.user.is_authenticated():
                    if not request.user.is_superuser:
                        q.extend(_instance['authenticated'])
                else:
                    q.extend(_instance['all'])
            return self.distinct().filter(*q)
        except KeyError:
            pass
        # TODO: should return nothing
        return self


class PipelineTool(models.Model):
    tool_id = models.SmallIntegerField(
        db_column='TOOL_ID', primary_key=True)
    tool_name = models.CharField(
        db_column='TOOL_NAME', max_length=30, blank=True, null=True)
    description = models.TextField(
        db_column='DESCRIPTION', blank=True, null=True)
    web_link = models.CharField(
        db_column='WEB_LINK', max_length=500, blank=True, null=True)
    version = models.CharField(
        db_column='VERSION', max_length=30, blank=True, null=True)
    exe_command = models.CharField(
        db_column='EXE_COMMAND', max_length=500, blank=True, null=True)
    installation_dir = models.CharField(
        db_column='INSTALLATION_DIR', max_length=200, blank=True, null=True)
    configuration_file = models.TextField(
        db_column='CONFIGURATION_FILE', blank=True, null=True)
    notes = models.TextField(
        db_column='NOTES', blank=True, null=True)

    class Meta:
        db_table = 'PIPELINE_TOOL'
        unique_together = ('tool_name', 'version',)
        ordering = ('tool_name',)

    def __str__(self):
        return "%s:%s" % (self.tool_name, self.version)

    def multiple_pk(self):
        return "%s/%s" % (self.tool_name, self.version)


class PipelineQuerySet(BaseQuerySet):
    pass


class PipelineManager(models.Manager):

    def get_queryset(self):
        return PipelineQuerySet(self.model, using=self._db) \
            .annotate(
                analyses_count=Count(
                    'analyses', filter=(
                        Q(analyses__analysis_status_id=3) |
                        Q(analyses__analysis_status_id=6)
                    ), distinct=True)
            ) \
            .annotate(
                samples_count=Count(
                    'analyses__sample', filter=(
                        Q(analyses__analysis_status_id=3) |
                        Q(analyses__analysis_status_id=6)
                    ), distinct=True)
            )


class Pipeline(models.Model):
    pipeline_id = models.SmallIntegerField(
        db_column='PIPELINE_ID', primary_key=True)
    description = models.TextField(
        db_column='DESCRIPTION', blank=True, null=True)
    changes = models.TextField(
        db_column='CHANGES')
    release_version = models.CharField(
        db_column='RELEASE_VERSION', max_length=20)
    release_date = models.DateField(
        db_column='RELEASE_DATE')

    tools = models.ManyToManyField(
        PipelineTool, through='PipelineReleaseTool', related_name='pipelines')

    objects = PipelineManager()

    class Meta:
        db_table = 'PIPELINE_RELEASE'
        unique_together = ('pipeline_id', 'release_version',)
        ordering = ('release_version',)

    def __str__(self):
        return self.release_version


class PipelineReleaseTool(models.Model):
    pipeline = models.ForeignKey(
        Pipeline, db_column='PIPELINE_ID',
        primary_key=True, on_delete=models.CASCADE)
    tool = models.ForeignKey(
        PipelineTool, db_column='TOOL_ID', on_delete=models.CASCADE)
    tool_group_id = models.DecimalField(
        db_column='TOOL_GROUP_ID', max_digits=6, decimal_places=3)
    how_tool_used_desc = models.TextField(
        db_column='HOW_TOOL_USED_DESC', blank=True, null=True)

    class Meta:
        db_table = 'PIPELINE_RELEASE_TOOL'
        unique_together = (
            ('pipeline', 'tool'),
            ('pipeline', 'tool_group_id'),
        )


class AnalysisStatus(models.Model):
    analysis_status_id = models.AutoField(
        db_column='ANALYSIS_STATUS_ID', primary_key=True)
    analysis_status = models.CharField(
        db_column='ANALYSIS_STATUS', max_length=25)

    class Meta:
        db_table = 'ANALYSIS_STATUS'
        ordering = ('analysis_status_id',)

    def __str__(self):
        return self.analysis_status


class BiomeQuerySet(models.QuerySet):
    pass


class BiomeManager(models.Manager):

    def get_queryset(self):
        return BiomeQuerySet(self.model, using=self._db) \
            .annotate(samples_count=Count('samples', distinct=True))


class Biome(models.Model):
    biome_id = models.SmallIntegerField(
        db_column='BIOME_ID', primary_key=True)
    biome_name = models.CharField(
        db_column='BIOME_NAME', max_length=60,
        help_text="Biome name")
    lft = models.SmallIntegerField(
        db_column='LFT')
    rgt = models.SmallIntegerField(
        db_column='RGT')
    depth = models.IntegerField(
        db_column='DEPTH')
    lineage = models.CharField(
        db_column='LINEAGE', max_length=500,
        help_text="Biome lineage")

    objects = BiomeManager()

    class Meta:
        db_table = 'BIOME_HIERARCHY_TREE'
        ordering = ('biome_id',)
        unique_together = (
            ('biome_id', 'biome_name'),
        )

    def __str__(self):
        return self.lineage


class PublicationQuerySet(BaseQuerySet):
    pass


class PublicationManager(models.Manager):

    def get_queryset(self):
        return PublicationQuerySet(self.model, using=self._db) \
            .annotate(studies_count=Count('studies', distinct=True)) \
            .annotate(samples_count=Count('studies__samples', distinct=True))


class Publication(models.Model):
    pub_id = models.AutoField(
        db_column='PUB_ID', primary_key=True)
    authors = models.CharField(
        db_column='AUTHORS', max_length=4000, blank=True, null=True,
        help_text='Publication authors')
    doi = models.CharField(
        db_column='DOI', max_length=1500, blank=True, null=True,
        help_text='DOI')
    isbn = models.CharField(
        db_column='ISBN', max_length=100, blank=True, null=True,
        help_text='ISBN')
    iso_journal = models.CharField(
        db_column='ISO_JOURNAL', max_length=255, blank=True, null=True,
        help_text='ISO journal')
    issue = models.CharField(
        db_column='ISSUE', max_length=55, blank=True, null=True,
        help_text='Publication issue')
    medline_journal = models.CharField(
        db_column='MEDLINE_JOURNAL', max_length=255, blank=True, null=True,)
    pub_abstract = models.TextField(
        db_column='PUB_ABSTRACT', blank=True, null=True,
        help_text='Publication abstract')
    pubmed_central_id = models.IntegerField(
        db_column='PUBMED_CENTRAL_ID', blank=True, null=True,
        help_text='Pubmed Central Identifier')
    pubmed_id = models.IntegerField(
        db_column='PUBMED_ID', blank=True, null=True,
        help_text='Pubmed ID')
    pub_title = models.CharField(
        db_column='PUB_TITLE', max_length=740,
        help_text='Publication title')
    raw_pages = models.CharField(
        db_column='RAW_PAGES', max_length=30, blank=True, null=True)
    pub_url = models.CharField(
        db_column='URL', max_length=740, blank=True, null=True,
        help_text='Publication url')
    volume = models.CharField(
        db_column='VOLUME', max_length=55, blank=True, null=True,
        help_text='Publication volume')
    published_year = models.SmallIntegerField(
        db_column='PUBLISHED_YEAR', blank=True, null=True,
        help_text='Published year')
    pub_type = models.CharField(
        db_column='PUB_TYPE', max_length=150, blank=True, null=True)

    objects = PublicationManager()

    class Meta:
        db_table = 'PUBLICATION'
        ordering = ('pubmed_id',)

    def __str__(self):
        return self.pubmed_id


class DownloadGroupType(models.Model):
    group_id = models.AutoField(
        db_column='GROUP_ID', primary_key=True,)
    group_type = models.CharField(
        db_column='GROUP_TYPE', max_length=30)

    class Meta:
        db_table = 'DOWNLOAD_GROUP_TYPE'

    def __str__(self):
        return self.group_label


class FileFormat(models.Model):
    format_id = models.AutoField(
        db_column='FORMAT_ID', primary_key=True)
    format_name = models.CharField(
        db_column='FORMAT_NAME', max_length=30)
    format_extension = models.CharField(
        db_column='FORMAT_EXTENSION', max_length=30)
    compression = models.BooleanField(
        db_column='COMPRESSION', default=True)

    class Meta:
        db_table = 'FILE_FORMAT'

    def __str__(self):
        return self.format_name


class DownloadSubdir(models.Model):
    subdir_id = models.AutoField(
        db_column='SUBDIR_ID', primary_key=True)
    subdir = models.CharField(
        db_column='SUBDIR', max_length=100)

    class Meta:
        db_table = 'DOWNLOAD_SUBDIR'

    def __str__(self):
        return self.subdir


class DownloadDescriptionLabel(models.Model):
    description_id = models.AutoField(
        db_column='DESCRIPTION_ID', primary_key=True)
    description = models.CharField(
        db_column='DESCRIPTION', max_length=255)
    description_label = models.CharField(
        db_column='DESCRIPTION_LABEL', max_length=100)

    class Meta:
        db_table = 'DOWNLOAD_DESCRIPTION_LABEL'

    def __str__(self):
        return self.description_label


class BaseDownload(models.Model):
    parent_id = models.ForeignKey(
        'self', db_column='PARENT_DOWNLOAD_ID', related_name='parent',
        blank=True, null=True)
    realname = models.CharField(
        db_column='REAL_NAME', max_length=255)
    alias = models.CharField(
        db_column='ALIAS', max_length=255)
    group_type = models.ForeignKey(
        'DownloadGroupType', db_column='GROUP_ID',
        on_delete=models.CASCADE, blank=True, null=True)
    subdir = models.ForeignKey(
        'DownloadSubdir', db_column='SUBDIR_ID',
        on_delete=models.CASCADE, blank=True, null=True)
    description = models.ForeignKey(
        'DownloadDescriptionLabel', db_column='DESCRIPTION_ID',
        on_delete=models.CASCADE, blank=True, null=True)
    file_format = models.ForeignKey(
        'FileFormat', db_column='FORMAT_ID',
        on_delete=models.CASCADE, blank=True, null=True)
    pipeline = models.ForeignKey(
        'Pipeline', db_column='PIPELINE_ID',
        on_delete=models.CASCADE, blank=True, null=True)

    @property
    def release_version(self):
        return self.pipeline.release_version

    class Meta:
        abstract = True


class AnalysisJobDownloadQuerySet(BaseQuerySet):
    pass


class AnalysisJobDownloadManager(models.Manager):

    def get_queryset(self):
        return AnalysisJobDownloadQuerySet(self.model, using=self._db)

    def available(self, request):
        return self.get_queryset().available(request)


class AnalysisJobDownload(BaseDownload):
    job = models.ForeignKey(
        'AnalysisJob', db_column='JOB_ID', related_name='analysis_download',
        on_delete=models.CASCADE)

    @property
    def accession(self):
        return self.job.accession

    objects = AnalysisJobDownloadManager()

    class Meta:
        db_table = 'ANALYSIS_JOB_DOWNLOAD'
        unique_together = (('realname', 'alias', 'pipeline'),)
        ordering = ('pipeline', 'group_type', 'alias',)


class StudyDownloadQuerySet(BaseQuerySet):
    pass


class StudyDownloadManager(models.Manager):

    def get_queryset(self):
        return StudyDownloadQuerySet(self.model, using=self._db) \
            .select_related(
                'group_type',
                'subdir',
                'file_format',
                'description',
                'pipeline',
                'study',
            )

    def available(self, request):
        return self.get_queryset().available(request)


class StudyDownload(BaseDownload):
    study = models.ForeignKey(
        'Study', db_column='STUDY_ID', related_name='study_download',
        on_delete=models.CASCADE)

    @property
    def accession(self):
        return self.study.accession

    objects = StudyDownloadManager()

    class Meta:
        db_table = 'STUDY_DOWNLOAD'
        unique_together = (('realname', 'alias', 'pipeline'),)
        ordering = ('pipeline', 'group_type', 'alias',)


class StudyQuerySet(BaseQuerySet):

    def mydata(self, request):
        if request.user.is_authenticated():
            _username = request.user.username
            return self.distinct() \
                .filter(Q(submission_account_id=_username))
        return ()

    def recent(self):
        return self.order_by('-last_update')


class StudyManager(models.Manager):

    def get_queryset(self):
        # TODO: remove biome when schema updated
        return StudyQuerySet(self.model, using=self._db) \
            .defer('biome') \
            .annotate(samples_count=Count('samples'))

    def available(self, request):
        return self.get_queryset().available(request)

    def recent(self, request):
        return self.get_queryset().available(request).recent()

    def mydata(self, request):
        return self.get_queryset().mydata(request)


class Study(models.Model):

    def __init__(self, *args, **kwargs):
        super(Study, self).__init__(*args, **kwargs)
        setattr(self, 'accession', kwargs.get('accession', self._custom_pk()))

    def _custom_pk(self):
        return "MGYS{pk:0>{fill}}".format(pk=self.study_id, fill=8)

    study_id = models.AutoField(
        db_column='STUDY_ID', primary_key=True)
    secondary_accession = models.CharField(
        db_column='EXT_STUDY_ID', max_length=20, unique=True)
    centre_name = models.CharField(
        db_column='CENTRE_NAME', max_length=255, blank=True, null=True)
    experimental_factor = models.CharField(
        db_column='EXPERIMENTAL_FACTOR', max_length=255, blank=True, null=True)
    is_public = models.IntegerField(
        db_column='IS_PUBLIC', blank=True, null=True)
    public_release_date = models.DateField(
        db_column='PUBLIC_RELEASE_DATE', blank=True, null=True)
    study_abstract = models.TextField(
        db_column='STUDY_ABSTRACT', blank=True, null=True)
    study_name = models.CharField(
        db_column='STUDY_NAME', max_length=255, blank=True, null=True)
    study_status = models.CharField(
        db_column='STUDY_STATUS', max_length=30, blank=True, null=True)
    data_origination = models.CharField(
        db_column='DATA_ORIGINATION', max_length=20, blank=True, null=True)
    author_email = models.CharField(
        db_column='AUTHOR_EMAIL', max_length=100, blank=True, null=True)
    author_name = models.CharField(
        db_column='AUTHOR_NAME', max_length=100, blank=True, null=True)
    last_update = models.DateTimeField(
        db_column='LAST_UPDATE')
    submission_account_id = models.CharField(
        db_column='SUBMISSION_ACCOUNT_ID',
        max_length=15, blank=True, null=True)
    biome = models.ForeignKey(
        Biome, db_column='BIOME_ID', related_name='studies',
        on_delete=models.CASCADE)
    result_directory = models.CharField(
        db_column='RESULT_DIRECTORY', max_length=100, blank=True, null=True)
    first_created = models.DateTimeField(
        db_column='FIRST_CREATED')
    project_id = models.CharField(
        db_column='PROJECT_ID', max_length=18, blank=True, null=True)

    publications = models.ManyToManyField(
        Publication, through='StudyPublication', related_name='studies')

    samples = models.ManyToManyField(
        'Sample', through='StudySample', related_name='studies', blank=True)

    @property
    def downloads(self):
        return self.study_download.all()

    @property
    def pipelines(self):
        return [download.pipeline for download in self.study_download.all()]

    objects = StudyManager()

    class Meta:
        db_table = 'STUDY'
        unique_together = (('study_id', 'secondary_accession'),)
        ordering = ('study_id',)

    def __str__(self):
        return self._custom_pk()


class StudyPublication(models.Model):
    study = models.ForeignKey(
        Study, db_column='STUDY_ID',
        primary_key=True, on_delete=models.CASCADE)
    pub = models.ForeignKey(
        Publication, db_column='PUB_ID', on_delete=models.CASCADE)

    class Meta:
        db_table = 'STUDY_PUBLICATION'
        unique_together = (('study', 'pub'),)


class StudySample(models.Model):
    study = models.ForeignKey(
        'Study', db_column='STUDY_ID', on_delete=models.CASCADE)
    sample = models.ForeignKey(
        'Sample', db_column='SAMPLE_ID', on_delete=models.CASCADE)

    class Meta:
        db_table = 'STUDY_SAMPLE'
        unique_together = (('study', 'sample'),)


class SampleQuerySet(BaseQuerySet):
    pass


class SampleManager(models.Manager):

    def get_queryset(self):
        return SampleQuerySet(self.model, using=self._db)

    def available(self, request, prefetch=False):
        queryset = self.get_queryset().available(request)
        if prefetch:
            queryset = queryset.prefetch_related(
                Prefetch('biome', queryset=Biome.objects.all()),
                Prefetch('studies', queryset=Study.objects.available(request)),
                Prefetch('metadata', queryset=SampleAnn.objects.all())
            ).defer(
                'is_public',
                'metadata_received',
                'sequencedata_received',
                'sequencedata_archived',
                'submission_account_id',
            )
        return queryset


class Sample(models.Model):
    sample_id = models.AutoField(
        db_column='SAMPLE_ID', primary_key=True)
    accession = models.CharField(
        db_column='EXT_SAMPLE_ID', max_length=20, unique=True,
        help_text='Secondary accession')
    primary_accession = models.CharField(
        db_column='PRIMARY_ACCESSION', max_length=20,
        help_text='Primary accession')
    analysis_completed = models.DateField(
        db_column='ANALYSIS_COMPLETED', blank=True, null=True)
    collection_date = models.DateField(
        db_column='COLLECTION_DATE', blank=True, null=True,
        help_text='Collection date')
    geo_loc_name = models.CharField(
        db_column='GEO_LOC_NAME', max_length=255, blank=True, null=True,
        help_text='Name of geographical location')
    is_public = models.IntegerField(
        db_column='IS_PUBLIC', blank=True, null=True)
    metadata_received = models.DateTimeField(
        db_column='METADATA_RECEIVED', blank=True, null=True)
    sample_desc = models.TextField(
        db_column='SAMPLE_DESC', blank=True, null=True,
        help_text='Sample description')
    sequencedata_archived = models.DateTimeField(
        db_column='SEQUENCEDATA_ARCHIVED', blank=True, null=True)
    sequencedata_received = models.DateTimeField(
        db_column='SEQUENCEDATA_RECEIVED', blank=True, null=True)
    environment_biome = models.CharField(
        db_column='ENVIRONMENT_BIOME', max_length=255, blank=True, null=True,
        help_text='Environment biome')
    environment_feature = models.CharField(
        db_column='ENVIRONMENT_FEATURE', max_length=255, blank=True, null=True,
        help_text='Environment feature')
    environment_material = models.CharField(
        db_column='ENVIRONMENT_MATERIAL', max_length=255,
        blank=True, null=True,
        help_text='Environment material')
    sample_name = models.CharField(
        db_column='SAMPLE_NAME', max_length=255, blank=True, null=True,
        help_text='Sample name')
    sample_alias = models.CharField(
        db_column='SAMPLE_ALIAS', max_length=255, blank=True, null=True,
        help_text='Sample alias')
    host_tax_id = models.IntegerField(
        db_column='HOST_TAX_ID', blank=True, null=True,
        help_text='Sample host tax id')
    species = models.CharField(
        db_column='SPECIES', max_length=255, blank=True, null=True,
        help_text='Species')
    latitude = models.DecimalField(
        db_column='LATITUDE', max_digits=7, decimal_places=4,
        blank=True, null=True,
        help_text='Latitude')
    longitude = models.DecimalField(
        db_column='LONGITUDE', max_digits=7, decimal_places=4,
        blank=True, null=True,
        help_text='Longitude')
    last_update = models.DateTimeField(
        db_column='LAST_UPDATE')
    submission_account_id = models.CharField(
        db_column='SUBMISSION_ACCOUNT_ID', max_length=15,
        blank=True, null=True)
    biome = models.ForeignKey(
        Biome, db_column='BIOME_ID', related_name='samples',
        on_delete=models.CASCADE)

    @property
    def biosample(self):
        return self.primary_accession

    @property
    def sample_metadata(self):
        return [
            {
                'key': v.var.var_name,
                'value': v.var_val_ucv,
                'unit': v.units or None
            } for v in self.metadata.all()
        ]

    objects = SampleManager()

    class Meta:
        unique_together = (('sample_id', 'accession'),)
        db_table = 'SAMPLE'
        ordering = ('accession',)

    def __str__(self):
        return self.accession


class SampleGeoCoordinateQuerySet(BaseQuerySet):
    pass


class SampleGeoCoordinateManager(models.Manager):

    def get_queryset(self):
        return SampleGeoCoordinateQuerySet(self.model, using=self._db) \
            .annotate(lon_lat_pk=Concat(
                Cast('longitude', CharField()), Value(','),
                Cast('latitude', CharField())
            ))

    def available(self, request):
        queryset = self.get_queryset().available(request)
        return queryset


class SampleGeoCoordinate(Sample):

    objects = SampleGeoCoordinateManager()

    class Meta:
        proxy = True

    def __str__(self):
        return self.latitude, self.longitude


class SamplePublication(models.Model):
    sample = models.ForeignKey(
        Sample, db_column='SAMPLE_ID',
        on_delete=models.CASCADE, primary_key=True)
    pub = models.ForeignKey(
        Publication, db_column='PUB_ID', on_delete=models.CASCADE)

    class Meta:
        db_table = 'SAMPLE_PUBLICATION'
        unique_together = (('sample', 'pub'),)


class ExperimentTypeQuerySet(BaseQuerySet):
    pass


class ExperimentTypeManager(models.Manager):

    def get_queryset(self):
        return ExperimentTypeQuerySet(self.model, using=self._db) \
            .annotate(
                samples_count=Count(
                    'runs__sample', filter=Q(runs__status_id=4), distinct=True)
            ) \
            .annotate(
                runs_count=Count(
                    'runs', filter=Q(runs__status_id=4), distinct=True)
            )


class ExperimentType(models.Model):
    experiment_type_id = models.SmallIntegerField(
        db_column='EXPERIMENT_TYPE_ID', primary_key=True,)
    experiment_type = models.CharField(
        db_column='EXPERIMENT_TYPE', max_length=30,
        help_text="Experiment type, e.g. metagenomic")

    objects = ExperimentTypeManager()

    class Meta:
        db_table = 'EXPERIMENT_TYPE'

    def __str__(self):
        return self.experiment_type


class Status(models.Model):
    status_id = models.SmallIntegerField(
        db_column='STATUS_ID', primary_key=True)
    status = models.CharField(
        db_column='STATUS', max_length=25)

    class Meta:
        db_table = 'STATUS'
        ordering = ('status_id',)

    def __str__(self):
        return self.status


class RunQuerySet(BaseQuerySet):
    pass


class RunManager(models.Manager):

    def get_queryset(self):
        return RunQuerySet(self.model, using=self._db)

    def available(self, request):
        return self.get_queryset().available(request) \
            .select_related(
                'experiment_type',
                'study', 'sample'
            )


class Run(models.Model):
    run_id = models.BigAutoField(
        db_column='RUN_ID', primary_key=True)
    accession = models.CharField(
        db_column='ACCESSION', max_length=80, blank=True, null=True)
    secondary_accession = models.CharField(
        db_column='SECONDARY_ACCESSION', max_length=100, blank=True, null=True)
    status_id = models.ForeignKey(
        'Status', db_column='STATUS_ID', related_name='runs',
        on_delete=models.CASCADE, default=2)
    sample = models.ForeignKey(
        'Sample', db_column='SAMPLE_ID', related_name='runs',
        on_delete=models.CASCADE, blank=True, null=True)
    study = models.ForeignKey(
        'Study', db_column='STUDY_ID', related_name='runs',
        on_delete=models.CASCADE, blank=True, null=True)
    # TODO: not consistant, schema changes may be needed
    experiment_type = models.ForeignKey(
        ExperimentType, db_column='EXPERIMENT_TYPE_ID',
        related_name='runs',
        on_delete=models.CASCADE, blank=True, null=True)
    instrument_platform = models.CharField(
        db_column='INSTRUMENT_PLATFORM', max_length=100,
        blank=True, null=True)
    instrument_model = models.CharField(
        db_column='INSTRUMENT_MODEL', max_length=100,
        blank=True, null=True)

    objects = RunManager()

    class Meta:
        db_table = 'RUN'
        ordering = ('accession',)
        unique_together = (
            ('run_id', 'accession'),
            ('accession', 'secondary_accession')
        )

    def __str__(self):
        return self.accession


class AnalysisJobQuerySet(BaseQuerySet):
    pass


class AnalysisJobManager(models.Manager):

    def get_queryset(self):
        _qs = AnalysisJobAnn.objects.all() \
            .select_related('var')
        return AnalysisJobQuerySet(self.model, using=self._db) \
            .select_related(
                'pipeline',
                'analysis_status',
                'experiment_type',
            ) \
            .prefetch_related(
                Prefetch('analysis_metadata', queryset=_qs),
            )

    def available(self, request):
        return self.get_queryset().available(request) \
            .prefetch_related(
                Prefetch(
                    'study',
                    queryset=Study.objects.available(request)
                ),
                Prefetch(
                    'sample',
                    queryset=Sample.objects.available(
                        request)
                ),
                Prefetch(
                    'run',
                    queryset=Run.objects.available(
                        request)
                )
            )


class AnalysisJob(models.Model):

    def __init__(self, *args, **kwargs):
        super(AnalysisJob, self).__init__(*args, **kwargs)
        setattr(self, 'accession',
                kwargs.get('accession', self._custom_pk()))

    def _custom_pk(self):
        if self.job_id is not None:
            return "MGYA{pk:0>{fill}}".format(pk=self.job_id, fill=8)
        return None

    job_id = models.BigAutoField(
        db_column='JOB_ID', primary_key=True)
    external_run_ids = models.CharField(
        db_column='EXTERNAL_RUN_IDS', max_length=100,
        blank=True, null=True)
    secondary_accession = models.CharField(
        db_column='SECONDARY_ACCESSION', max_length=100,
        blank=True, null=True)
    job_operator = models.CharField(
        db_column='JOB_OPERATOR', max_length=15, blank=True, null=True)
    pipeline = models.ForeignKey(
        Pipeline, db_column='PIPELINE_ID', blank=True, null=True,
        related_name='analyses', on_delete=models.CASCADE)
    submit_time = models.DateTimeField(
        db_column='SUBMIT_TIME', blank=True, null=True)
    complete_time = models.DateTimeField(
        db_column='COMPLETE_TIME', blank=True, null=True)
    analysis_status = models.ForeignKey(
        AnalysisStatus, db_column='ANALYSIS_STATUS_ID',
        on_delete=models.CASCADE)
    re_run_count = models.IntegerField(
        db_column='RE_RUN_COUNT', blank=True, null=True)
    input_file_name = models.CharField(
        db_column='INPUT_FILE_NAME', max_length=50)
    result_directory = models.CharField(
        db_column='RESULT_DIRECTORY', max_length=100)
    run = models.ForeignKey(
        Run, db_column='RUN_ID', related_name='analyses',
        on_delete=models.CASCADE, blank=True, null=True)
    sample = models.ForeignKey(
        Sample, db_column='SAMPLE_ID', related_name='analyses',
        on_delete=models.CASCADE, blank=True, null=True)
    study = models.ForeignKey(
        Study, db_column='STUDY_ID', related_name='analyses',
        on_delete=models.CASCADE, blank=True, null=True)
    is_production_run = models.TextField(
        db_column='IS_PRODUCTION_RUN', blank=True, null=True)
    experiment_type = models.ForeignKey(
        ExperimentType, db_column='EXPERIMENT_TYPE_ID',
        related_name='analyses',
        on_delete=models.CASCADE)
    run_status_id = models.IntegerField(
        db_column='RUN_STATUS_ID', blank=True, null=True)
    instrument_platform = models.CharField(
        db_column='INSTRUMENT_PLATFORM', max_length=50,
        blank=True, null=True)
    instrument_model = models.CharField(
        db_column='INSTRUMENT_MODEL', max_length=50,
        blank=True, null=True)

    @property
    def release_version(self):
        return self.pipeline.release_version

    @property
    def analysis_summary(self):
        return [
            {
                'key': v.var.var_name,
                'value': v.var_val_ucv
            } for v in self.analysis_metadata.all()
        ]

    @property
    def downloads(self):
        return self.analysis_download.all()

    objects = AnalysisJobManager()

    class Meta:
        db_table = 'ANALYSIS_JOB'
        ordering = ('job_id',)

    def __str__(self):
        return self.accession


class StudyErrorType(models.Model):
    error_id = models.IntegerField(
        db_column='ERROR_ID', primary_key=True)
    error_type = models.CharField(
        db_column='ERROR_TYPE', max_length=50)
    description = models.TextField(
        db_column='DESCRIPTION')

    class Meta:
        managed = False
        db_table = 'STUDY_ERROR_TYPE'

    def __str__(self):
        return self.error_type


class BlacklistedStudy(models.Model):
    ext_study_id = models.CharField(
        db_column='EXT_STUDY_ID', primary_key=True, max_length=18)
    error_type = models.ForeignKey(
        'StudyErrorType', models.DO_NOTHING, db_column='ERROR_TYPE_ID')
    analyzer = models.CharField(
        db_column='ANALYZER', max_length=15)
    pipeline_id = models.IntegerField(
        db_column='PIPELINE_ID', blank=True, null=True)
    date_blacklisted = models.DateField(
        db_column='DATE_BLACKLISTED')
    comment = models.TextField(
        db_column='COMMENT', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'BLACKLISTED_STUDY'

    def __str__(self):
        return self.ext_study_id


class VariableNames(models.Model):
    var_id = models.SmallIntegerField(
        db_column='VAR_ID', primary_key=True)
    var_name = models.CharField(
        db_column='VAR_NAME', unique=True, max_length=50)
    definition = models.TextField(
        db_column='DEFINITION', blank=True, null=True)
    value_syntax = models.CharField(
        db_column='VALUE_SYNTAX', max_length=250, blank=True, null=True)
    alias = models.CharField(
        db_column='ALIAS', max_length=30, blank=True, null=True)
    authority = models.CharField(
        db_column='AUTHORITY', max_length=30, blank=True, null=True)
    sra_xml_attribute = models.CharField(
        db_column='SRA_XML_ATTRIBUTE', max_length=30, blank=True, null=True)
    required_for_mimarks_complianc = models.CharField(
        db_column='REQUIRED_FOR_MIMARKS_COMPLIANC', max_length=1,
        blank=True, null=True)
    required_for_mims_compliance = models.CharField(
        db_column='REQUIRED_FOR_MIMS_COMPLIANCE', max_length=1,
        blank=True, null=True)
    gsc_env_packages = models.CharField(
        db_column='GSC_ENV_PACKAGES', max_length=250,
        blank=True, null=True)
    comments = models.CharField(
        db_column='COMMENTS', max_length=250,
        blank=True, null=True)

    class Meta:
        db_table = 'VARIABLE_NAMES'
        unique_together = (('var_id', 'var_name'), ('var_id', 'var_name'),)

    def __str__(self):
        return self.var_name


class SampleAnnQuerySet(BaseQuerySet):
    pass


class SampleAnnManager(models.Manager):

    def get_queryset(self):
        return SampleAnnQuerySet(self.model, using=self._db) \
            .select_related('var')


class SampleAnn(models.Model):
    sample = models.ForeignKey(
        Sample, db_column='SAMPLE_ID', primary_key=True,
        related_name="metadata")
    units = models.CharField(
        db_column='UNITS', max_length=25, blank=True, null=True)
    var = models.ForeignKey(
        'VariableNames', db_column='VAR_ID')
    var_val_ucv = models.CharField(
        db_column='VAR_VAL_UCV', max_length=4000, blank=True, null=True)

    objects = SampleAnnManager()

    class Meta:
        db_table = 'SAMPLE_ANN'
        unique_together = (('sample', 'var'), ('sample', 'var'),)

    def __str__(self):
        return "%s %s:%r" % (self.sample, self.var.var_name, self.var_val_ucv)

    def multiple_pk(self):
        return "%s/%s" % (self.var.var_name, self.var_val_ucv)


class AnalysisMetadataVariableNames(models.Model):
    var_name = models.CharField(
        db_column='VAR_NAME', unique=True, max_length=100)
    description = models.CharField(
        db_column='DESCRIPTION', max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'SUMMARY_VARIABLE_NAMES'
        unique_together = (('var_name', 'description'),)

    def __str__(self):
        return self.var_name


class AnalysisJobAnn(models.Model):
    job = models.ForeignKey(
        AnalysisJob, db_column='JOB_ID',
        related_name="analysis_metadata")
    units = models.CharField(
        db_column='UNITS', max_length=25, blank=True, null=True)
    var = models.ForeignKey(AnalysisMetadataVariableNames)
    var_val_ucv = models.CharField(
        db_column='VAR_VAL_UCV', max_length=4000, blank=True, null=True)

    class Meta:
        db_table = 'ANALYSIS_JOB_ANN'
        unique_together = (('job', 'var'), ('job', 'var'),)

    def __str__(self):
        return "%s %s" % (self.job, self.var)

    def multiple_pk(self):
        return "%s/%s" % (self.var.var_name, self.var_val_ucv)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

import os

from django.conf import settings
from enum import Enum

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
    """Auth mechanism to filter private models
    """

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
            'AssemblyQuerySet': {
                'all': [
                    Q(status_id=4),
                ],
            },
            'AnalysisJobQuerySet': {
                'all': [
                    # TMP: IS_PUBLIC = 5 is suppressed
                    ~Q(sample__is_public=5),
                    Q(run__status_id=4) | Q(assembly__status_id=4),
                    Q(analysis_status_id=3) | Q(analysis_status_id=6)
                ],
            },
            'AnalysisJobDownloadQuerySet': {
                'all': [
                    # TMP: IS_PUBLIC = 5 is suppressed
                    ~Q(job__sample__is_public=5),
                    Q(job__run__status_id=4) | Q(job__assembly__status_id=4),
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
            _query_filters['AssemblyQuerySet']['authenticated'] = \
                [Q(samples__studies__submission_account_id=_username,
                   status_id=2) |
                 Q(status_id=4)]
            _query_filters['AnalysisJobQuerySet']['authenticated'] = \
                [Q(study__submission_account_id=_username,
                   run__status_id=2) |
                 Q(study__submission_account_id=_username,
                   assembly__status_id=2) |
                 Q(run__status_id=4) | Q(assembly__status_id=4)]
            _query_filters['AnalysisJobDownloadQuerySet']['authenticated'] = \
                [Q(job__study__submission_account_id=_username,
                   job__run__status_id=2) |
                 Q(job__study__submission_account_id=_username,
                   job__assembly__status_id=2) |
                 Q(job__run__status_id=4) | Q(job__assembly__status_id=4)]

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
        db_column='MEDLINE_JOURNAL', max_length=255, blank=True, null=True, )
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
        db_column='GROUP_ID', primary_key=True, )
    group_type = models.CharField(
        db_column='GROUP_TYPE', max_length=30)

    class Meta:
        db_table = 'DOWNLOAD_GROUP_TYPE'

    def __str__(self):
        return self.group_type


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

    class Meta:
        abstract = True


class BaseAnnotationPipelineDownload(BaseDownload):
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


class AnalysisJobDownload(BaseAnnotationPipelineDownload):
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


class StudyDownload(BaseAnnotationPipelineDownload):
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
        if self.study_id and isinstance(self.study_id, int):
            return "MGYS{pk:0>{fill}}".format(pk=self.study_id, fill=8)
        return None

    study_id = models.AutoField(
        db_column='STUDY_ID', primary_key=True)
    secondary_accession = models.CharField(
        db_column='EXT_STUDY_ID', max_length=20, unique=True)
    centre_name = models.CharField(
        db_column='CENTRE_NAME', max_length=255, blank=True, null=True)
    experimental_factor = models.CharField(
        db_column='EXPERIMENTAL_FACTOR', max_length=255, blank=True, null=True)
    is_public = models.BooleanField(
        db_column='IS_PUBLIC', default=False)
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
        verbose_name_plural = 'studies'

    def __str__(self):
        return self._custom_pk()


class StudyPublication(models.Model):
    id = models.AutoField(primary_key=True)
    study = models.ForeignKey(
        Study, db_column='STUDY_ID', on_delete=models.CASCADE)
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


class SuperStudyQuerySet(BaseQuerySet):
    pass


class SuperStudyManager(models.Manager):

    def get_queryset(self):
        return SuperStudyQuerySet(self.model, using=self._db) \
            .annotate(biomes_count=Count('biomes', distinct=True))

    def available(self, request, prefetch=False):
        queryset = self.get_queryset()
        if prefetch:
            queryset = queryset.prefetch_related(
                Prefetch('flagship_studies', queryset=Study.objects.available(request)),
                Prefetch('biome', queryset=Biome.objects.all()),
            )
        return queryset


class SuperStudy(models.Model):
    """
    Aggregation of studies.
    Each Super Study will have multiples Studies under 2 categories:
    - Flagship Projects, those that are directly related to the Super Study
    - Related Projects, the studies that share the biome with the Super Study
    """
    super_study_id = models.AutoField(db_column='STUDY_ID',
                                      primary_key=True)
    title = models.CharField(db_column='TITLE', max_length=100)
    description = models.TextField(db_column='DESCRIPTION', blank=True, null=True)

    flagship_studies = models.ManyToManyField(
        'Study', through='SuperStudyStudy', related_name='super_studies', blank=True
    )

    biomes = models.ManyToManyField(
        'Biome', through='SuperStudyBiome', related_name='super_studies', blank=True
    )

    image = models.CharField(db_column='IMAGE', max_length=100, blank=True, null=True)

    objects = SuperStudyManager()

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return os.path.join(settings.IMG_FOLDER, str(self.image))
        else:
            return ''

    class Meta:
        db_table = 'SUPER_STUDY'
        verbose_name_plural = 'super studies'


class SuperStudyStudy(models.Model):
    """
    Relation between a Super Study and a Study
    """
    study = models.ForeignKey(
        'Study', db_column='STUDY_ID',
        on_delete=models.CASCADE)
    super_study = models.ForeignKey(
        'SuperStudy', db_column='SUPER_STUDY_ID',
        on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.super_study, self.study)

    class Meta:
        db_table = 'SUPER_STUDY_STUDY'
        unique_together = (('study', 'super_study'),)
        verbose_name_plural = 'super studies studies'


class SuperStudyBiome(models.Model):
    """
    Relation between a Super Study and a Biome
    """
    biome = models.ForeignKey(
        'Biome', db_column='BIOME_ID',
        on_delete=models.CASCADE)
    super_study = models.ForeignKey(
        'SuperStudy', db_column='SUPER_STUDY_ID',
        on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.super_study, self.biome)

    class Meta:
        db_table = 'SUPER_STUDY_BIOME'
        unique_together = (('biome', 'super_study'),)
        verbose_name_plural = 'super studies biomes'


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
    # possible values
    # 1 - public
    # 0 - private
    # 5 - suppressed
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
            .annotate(lon_lat_pk=Concat(Cast('longitude', CharField()), Value(','),
                                        Cast('latitude', CharField())))

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
        db_column='EXPERIMENT_TYPE_ID', primary_key=True, )
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


class AssemblyQuerySet(BaseQuerySet):
    pass


class AssemblyManager(models.Manager):
    def get_queryset(self):
        return AssemblyQuerySet(self.model, using=self._db)

    def available(self, request):
        return self.get_queryset().available(request) \
            .select_related(
            'experiment_type',
        )


class Assembly(models.Model):
    assembly_id = models.BigAutoField(
        db_column='ASSEMBLY_ID', primary_key=True)
    accession = models.CharField(
        db_column='ACCESSION', max_length=80, blank=True, null=True)
    wgs_accession = models.CharField(
        db_column='WGS_ACCESSION', max_length=100, blank=True, null=True)
    legacy_accession = models.CharField(
        db_column='LEGACY_ACCESSION', max_length=100, blank=True, null=True)
    status_id = models.ForeignKey(
        'Status', db_column='STATUS_ID', related_name='assemblies',
        on_delete=models.CASCADE, default=2)
    experiment_type = models.ForeignKey(
        ExperimentType, db_column='EXPERIMENT_TYPE_ID',
        related_name='assemblies',
        on_delete=models.CASCADE, blank=True, null=True)

    runs = models.ManyToManyField(
        'Run', through='AssemblyRun', related_name='assemblies', blank=True)
    samples = models.ManyToManyField(
        'Sample', through='AssemblySample', related_name='assemblies',
        blank=True)

    objects = AssemblyManager()

    class Meta:
        db_table = 'ASSEMBLY'
        ordering = ('accession',)
        unique_together = (
            ('assembly_id', 'accession'),
            ('accession', 'wgs_accession', 'legacy_accession')
        )

    def __str__(self):
        return self.accession


class AssemblyRun(models.Model):
    assembly = models.ForeignKey(
        'Assembly', db_column='ASSEMBLY_ID', on_delete=models.CASCADE)
    run = models.ForeignKey(
        'Run', db_column='RUN_ID', on_delete=models.CASCADE)

    class Meta:
        db_table = 'ASSEMBLY_RUN'
        unique_together = (('assembly', 'run'),)


class AssemblySample(models.Model):
    assembly = models.ForeignKey(
        'Assembly', db_column='ASSEMBLY_ID', on_delete=models.CASCADE)
    sample = models.ForeignKey(
        'Sample', db_column='SAMPLE_ID', on_delete=models.CASCADE)

    class Meta:
        db_table = 'ASSEMBLY_SAMPLE'
        unique_together = (('assembly', 'sample'),)


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
            return 'MGYA{pk:0>{fill}}'.format(pk=self.job_id, fill=8)
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
    assembly = models.ForeignKey(
        Assembly, db_column='ASSEMBLY_ID', related_name='analyses',
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
        unique_together = (('job_id', 'external_run_ids'),
                           ('pipeline', 'external_run_ids'),)
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
    id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(
        Sample, db_column='SAMPLE_ID',
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
        unique_together = (('sample', 'var'), )

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
    job = models.ForeignKey(AnalysisJob, db_column='JOB_ID', related_name='analysis_metadata')
    units = models.CharField(db_column='UNITS', max_length=25, blank=True, null=True)
    var = models.ForeignKey(AnalysisMetadataVariableNames)
    var_val_ucv = models.CharField(db_column='VAR_VAL_UCV', max_length=4000, blank=True, null=True)

    class Meta:
        db_table = 'ANALYSIS_JOB_ANN'
        unique_together = (('job', 'var'), ('job', 'var'),)

    def __str__(self):
        return '%s %s' % (self.job, self.var)

    def multiple_pk(self):
        return '%s/%s' % (self.var.var_name, self.var_val_ucv)


class GenomeTypes(Enum):
    ISOLATE = 'isolate'
    MAG = 'mag'


class CogCat(models.Model):

    name = models.CharField(db_column='NAME', max_length=80, unique=True)
    description = models.CharField(db_column='DESCRIPTION', max_length=80)

    class Meta:
        db_table = 'COG'


class AntiSmashGC(models.Model):
    name = models.CharField(db_column='NAME', max_length=80)
    description = models.CharField(db_column='DESCRIPTION', max_length=80)

    class Meta:
        db_table = 'ANTISMASH_GENECLUSTER'


class GeographicLocation(models.Model):

    name = models.CharField(db_column='CONTINENT', max_length=80, unique=True)

    class Meta:
        db_table = 'GEOGRAPHIC_RANGE'


class GenomeSet(models.Model):

    name = models.CharField(db_column='NAME', max_length=40, unique=True)

    class Meta:
        db_table = 'GENOME_SET'


class Genome(models.Model):

    genome_id = models.AutoField(
        db_column='GENOME_ID', primary_key=True)
    accession = models.CharField(db_column='GENOME_ACCESSION', max_length=40, unique=True)

    ena_genome_accession = models.CharField(db_column='ENA_GENOME_ACCESSION', max_length=20, unique=True, null=True)
    ena_sample_accession = models.CharField(db_column='ENA_SAMPLE_ACCESSION', max_length=20, null=True)
    ena_study_accession = models.CharField(db_column='ENA_STUDY_ACCESSION', max_length=20, null=True)

    ncbi_genome_accession = models.CharField(db_column='NCBI_GENOME_ACCESSION', max_length=20, unique=True, null=True)
    ncbi_sample_accession = models.CharField(db_column='NCBI_SAMPLE_ACCESSION', max_length=20, null=True)
    ncbi_study_accession = models.CharField(db_column='NCBI_STUDY_ACCESSION', max_length=20, null=True)

    img_genome_accession = models.CharField(db_column='IMG_GENOME_ACCESSION', max_length=20, unique=True, null=True)
    patric_genome_accession = models.CharField(db_column='PATRIC_GENOME_ACCESSION', max_length=20, unique=True,
                                               null=True)

    genome_set = models.ForeignKey(GenomeSet,
                                   db_column='GENOME_SET_ID',
                                   on_delete=models.CASCADE, null=True)
    biome = models.ForeignKey(
        Biome, db_column='BIOME_ID',
        on_delete=models.CASCADE)

    length = models.IntegerField(db_column='LENGTH')
    num_contigs = models.IntegerField(db_column='N_CONTIGS')
    n_50 = models.IntegerField(db_column='N50')
    gc_content = models.FloatField(db_column='GC_CONTENT')
    type = models.CharField(db_column='TYPE',
                            choices=[(tag, tag.value) for tag in GenomeTypes],
                            max_length=80)
    completeness = models.FloatField(db_column='COMPLETENESS')
    contamination = models.FloatField(db_column='CONTAMINATION')
    rna_5s = models.FloatField(db_column='RNA_5S')
    rna_16s = models.FloatField(db_column='RNA_16S')
    rna_23s = models.FloatField(db_column='RNA_23S')
    trnas = models.FloatField(db_column='T_RNA')
    nc_rnas = models.IntegerField(db_column='NC_RNA')
    num_proteins = models.IntegerField(db_column='NUM_PROTEINS')
    eggnog_coverage = models.FloatField(db_column='EGGNOG_COVERAGE')
    ipr_coverage = models.FloatField(db_column='IPR_COVERAGE')
    taxon_lineage = models.CharField(db_column='TAXON_LINEAGE', max_length=400)
    cmseq = models.FloatField(db_column='CMSEQ', null=True)
    taxincons = models.FloatField(db_column='TAXINCONS')

    num_genomes_total = models.IntegerField(db_column='PANGENOME_TOTAL_GENOMES', null=True)
    num_genomes_non_redundant = models.IntegerField(db_column='PANGENOME_NON_RED_GENOMES', null=True)
    pangenome_size = models.IntegerField(db_column='PANGENOME_SIZE', null=True)
    pangenome_core_size = models.IntegerField(db_column='PANGENOME_CORE_PROP', null=True)
    pangenome_accessory_size = models.IntegerField(db_column='PANGENOME_ACCESSORY_PROP', null=True)
    pangenome_eggnog_coverage = models.FloatField(db_column='PANGENOME_EGGNOG_COV', null=True)
    pangenome_ipr_coverage = models.FloatField(db_column='PANGENOME_IPR_COV', null=True)

    last_update = models.DateTimeField(db_column='LAST_UPDATE', auto_now=True)
    first_created = models.DateTimeField(db_column='FIRST_CREATED', auto_now_add=True)

    geo_origin = models.ForeignKey('GeographicLocation', db_column='GEOGRAPHIC_ORIGIN', null=True)

    pangenome_geographic_range = models.ManyToManyField('GeographicLocation',
                                                        db_table='GENOME_PANGENOME_GEOGRAPHIC_RANGE',
                                                        related_name='geographic_range')

    cog_matches = models.ManyToManyField('CogCat',
                                         through='emgapi.GenomeCogCounts')
    kegg_classes = models.ManyToManyField('KeggClass',
                                          through='emgapi.GenomeKeggClassCounts')
    kegg_modules = models.ManyToManyField('KeggModule',
                                          through='emgapi.GenomeKeggModuleCounts')
    antismash_geneclusters = models.ManyToManyField('AntiSmashGC', through='emgapi.GenomeAntiSmashGCCounts')

    result_directory = models.CharField(
        db_column='RESULT_DIRECTORY', max_length=100, blank=True, null=True)

    releases = models.ManyToManyField('Release', through='ReleaseGenomes')

    @property
    def geographic_range(self):
        """TODO: improve this, this is making len(pangenome_geographic_range) queries each time
        """
        return [v.name for v in self.pangenome_geographic_range.all()]

    @property
    def geographic_origin(self):
        if self.geo_origin:
            name = self.geo_origin.name
        else:
            name = None
        return name

    class Meta:
        db_table = 'GENOME'

    def __str__(self):
        return self.accession


class GenomeGeographicLocation(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID',
                               on_delete=models.CASCADE)
    GeographicLocation = models.ForeignKey(GeographicLocation,
                                           db_column='COG_ID',
                                           on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'GENOME_GEOGRAPHIC_RANGE'


class ReleaseManager(models.Manager):

    def get_queryset(self):
        qs = BaseQuerySet(self.model, using=self._db)
        return qs.annotate(genome_count=Count('genomes'))

    def available(self, request):
        return self.get_queryset().available(request)


class Release(models.Model):
    """Genome (MAGs) Release
    """
    version = models.CharField(db_column='VERSION', max_length=20)
    last_update = models.DateTimeField(db_column='LAST_UPDATE', auto_now=True)
    first_created = models.DateTimeField(db_column='FIRST_CREATED', auto_now_add=True)

    genomes = models.ManyToManyField(Genome, through='ReleaseGenomes')
    result_directory = models.CharField(db_column='RESULT_DIRECTORY', max_length=100)

    objects = ReleaseManager()

    class Meta:
        db_table = 'RELEASE'


class ReleaseGenomes(models.Model):

    genome = models.ForeignKey('Genome', db_column='GENOME_ID')
    release = models.ForeignKey('Release', db_column='RELEASE_ID')

    class Meta:
        db_table = 'RELEASE_GENOMES'
        unique_together = ('genome', 'release')


class GenomeCogCounts(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID',
                               on_delete=models.CASCADE, db_index=True)
    cog = models.ForeignKey(CogCat, db_column='COG_ID',
                            on_delete=models.DO_NOTHING)
    genome_count = models.IntegerField(db_column='GENOME_COUNT')
    pangenome_count = models.IntegerField(db_column='PANGENOME_COUNT')

    class Meta:
        db_table = 'GENOME_COG_COUNTS'
        unique_together = ('genome', 'cog')


class KeggClass(models.Model):

    class_id = models.CharField(db_column='CLASS_ID', max_length=10,
                                unique=True)
    name = models.CharField(db_column='NAME', max_length=80)
    parent = models.ForeignKey('self', db_column='PARENT', null=True)

    class Meta:
        db_table = 'KEGG_CLASS'


class GenomeKeggClassCounts(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID',
                               on_delete=models.CASCADE, db_index=True)
    kegg_class = models.ForeignKey(KeggClass, db_column='KEGG_ID',
                                   on_delete=models.DO_NOTHING)
    genome_count = models.IntegerField(db_column='GENOME_COUNT')
    pangenome_count = models.IntegerField(db_column='PANGENOME_COUNT')

    class Meta:
        db_table = 'GENOME_KEGG_CLASS_COUNTS'
        unique_together = ('genome', 'kegg_class')


class KeggModule(models.Model):

    name = models.CharField(db_column='MODULE_NAME', max_length=10,
                            unique=True)
    description = models.CharField(db_column='DESCRIPTION', max_length=200)

    class Meta:
        db_table = 'KEGG_MODULE'


class GenomeKeggModuleCounts(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID',
                               on_delete=models.CASCADE, db_index=True)
    kegg_module = models.ForeignKey(KeggModule, db_column='KEGG_MODULE',
                                    on_delete=models.DO_NOTHING)
    genome_count = models.IntegerField(db_column='GENOME_COUNT')
    pangenome_count = models.IntegerField(db_column='PANGENOME_COUNT')

    class Meta:
        db_table = 'GENOME_KEGG_MODULE_COUNTS'
        unique_together = ('genome', 'kegg_module')


class GenomeAntiSmashGCCounts(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID', on_delete=models.CASCADE, db_index=True)
    antismash_genecluster = models.ForeignKey(AntiSmashGC, db_column='ANTISMASH_GENECLUSTER',
                                              on_delete=models.DO_NOTHING)
    genome_count = models.IntegerField(db_column='GENOME_COUNT')

    class Meta:
        db_table = 'GENOME_ANTISMASH_GENECLUSTER_COUNTS'
        unique_together = ('genome', 'antismash_genecluster')


class GenomeDownloadManager(models.Manager):
    
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db) \
            .select_related(
                'group_type',
                'subdir',
                'file_format',
                'description')

    def available(self, request):
        return self.get_queryset().available(request)


class GenomeDownload(BaseDownload):
    genome = models.ForeignKey(
        'Genome', db_column='GENOME_ID',
        on_delete=models.CASCADE, db_index=True)

    @property
    def accession(self):
        return self.genome.accession

    objects = GenomeDownloadManager()

    class Meta:
        db_table = 'GENOME_DOWNLOAD'
        unique_together = (('realname', 'alias', 'genome'),)
        ordering = ('group_type', 'alias')


class ReleaseDownloadManager(models.Manager):

    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db) \
            .select_related(
                'group_type',
                'subdir',
                'file_format',
                'description')

    def available(self, request):
        return self.get_queryset().available(request)


class ReleaseDownload(BaseDownload):
    release = models.ForeignKey('Release',
                                db_column='RELEASE_ID',
                                on_delete=models.CASCADE)

    @property
    def accession(self):
        return self.release.version

    objects = ReleaseDownloadManager()

    class Meta:
        db_table = 'RELEASE_DOWNLOAD'
        unique_together = (('realname', 'alias'),)
        ordering = ('group_type', 'alias')

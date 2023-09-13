#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2022 EMBL - European Bioinformatics Institute
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

import logging

from django.conf import settings
from django.db import models
from django.db.models import (CharField, Count, OuterRef, Prefetch, Q,
                              Subquery, Value)
from django.db.models.functions import Cast, Concat
from django.utils import timezone

from rest_framework.generics import get_object_or_404

from django_mysql.models import QuerySet as MySQLQuerySet

from emgapi.validators import validate_ena_study_accession

from emgena.models import Status as ENAStatus


logger = logging.getLogger(__name__)

MARKDOWN_HELP = 'Use <a href="https://commonmark.org/help/" target="_newtab">markdown</a> for links and rich text.'


class Resource(object):
    def __init__(self, **kwargs):
        for field in ('id', 'resource', 'count'):
            setattr(self, field, kwargs.get(field, None))


class Token(object):
    def __init__(self, **kwargs):
        for field in ('id', 'token'):
            setattr(self, field, kwargs.get(field, None))


class PrivacyControlledModel(models.Model):
    is_private = models.BooleanField(db_column='IS_PRIVATE', default=True)

    class Meta:
        abstract = True


class SuppressQuerySet(models.QuerySet):
    def suppress(self, reason):
        return self.update(is_suppressed=True, suppressed_at=timezone.now(), suppression_reason=reason)

    def unsuppress(self, reason):
        return self.update(is_suppressed=False, suppressed_at=None, suppression_reason=None)


class SuppressManager(models.Manager):
    def get_queryset(self):
        return SuppressQuerySet(self.model, self._db).filter(is_suppressed=False)


class SuppressibleModel(models.Model):
    
    class Reason(models.IntegerChoices):
        DRAFT = 1
        CANCELLED = 3
        SUPPRESSED = 5
        KILLED = 6
        TEMPORARY_SUPPRESSED = 7
        TEMPORARY_KILLED = 8

    is_suppressed = models.BooleanField(db_column='IS_SUPPRESSED', default=False)
    suppressed_at = models.DateTimeField(db_column='SUPPRESSED_AT', blank=True, null=True)
    suppression_reason = models.IntegerField(db_column='SUPPRESSION_REASON', blank=True, null=True, choices=Reason.choices)

    def suppress(self, suppression_reason=None, save=True):
        self.is_suppressed = True
        self.suppressed_at = timezone.now()
        self.suppression_reason = suppression_reason
        if save:
            self.save()
        return self

    def unsuppress(self, suppression_reason=None, save=True):
        self.is_suppressed = False
        self.suppressed_at = None
        self.suppression_reason = None
        if save:
            self.save()
        return self

    class Meta:
        abstract = True


class ENASyncableModel(SuppressibleModel, PrivacyControlledModel):

    def sync_with_ena_status(self, ena_model_status: ENAStatus):
        """Sync the model with the ENA status accordingly.
        Fields that are updated: is_supppressed, suppressed_at, reason and is_private
        """
        if ena_model_status == ENAStatus.PRIVATE and not self.is_private:
            self.is_private = True
            logging.info(f"{self} marked as private")
        if ena_model_status == ENAStatus.PUBLIC and self.is_private:
            self.is_private = False
            logging.info(f"{self} marked as public")

        if ena_model_status == ENAStatus.DRAFT:
            logging.warning(
                f"{self} will not be updated due to the study status being 'draft'"
            )

        if (
            ena_model_status
            in [
                ENAStatus.SUPPRESSED,
                ENAStatus.KILLED,
                ENAStatus.TEMPORARY_SUPPRESSED,
                ENAStatus.TEMPORARY_KILLED,
                ENAStatus.CANCELLED,
            ]
            and not self.is_suppressed
        ):
            reason = None
            if ena_model_status == ENAStatus.SUPPRESSED:
                reason = SuppressibleModel.Reason.SUPPRESSED
            if ena_model_status == ENAStatus.KILLED:
                reason = SuppressibleModel.Reason.KILLED
            elif ena_model_status == ENAStatus.CANCELLED:
                reason = SuppressibleModel.Reason.CANCELLED
            elif ena_model_status == ENAStatus.TEMPORARY_SUPPRESSED:
                reason = (
                    SuppressibleModel.Reason.TEMPORARY_SUPPRESSED
                )
            elif ena_model_status == ENAStatus.TEMPORARY_KILLED:
                reason = SuppressibleModel.Reason.TEMPORARY_KILLED
            elif ena_model_status == ENAStatus.CANCELLED:
                reason = SuppressibleModel.Reason.CANCELLED

            self.suppress(suppression_reason=reason, save=False)

            logging.info(
                f"{self} was suppressed, status on ENA {ena_model_status}"
            )

        return self

    class Meta:
        abstract = True


class BaseQuerySet(models.QuerySet):
    """Auth mechanism to filter private / suppressed models
    """
    # TODO: the QuerySet should not have to handle the request
    #       if should recieve the username
    #       move the requests bits to the filters and serializers as needed

    def available(self, request=None):
        """
        Filter data based on the status or other properties.
        Status table:
        1	draft
        2	private
        3	cancelled
        4	public
        5	suppressed
        6	killed
        7	temporary_suppressed
        8	temporary_killed
        """
        _query_filters = {
            'StudyQuerySet': {
                'all': [Q(is_private=False),],
            },
            'StudyDownloadQuerySet': {
                'all': [Q(study__is_private=False),],
            },
            'SampleQuerySet': {
                'all': [Q(is_private=False),],
            },
            'RunQuerySet': {
                'all': [
                    Q(is_private=False),
                ],
            },
            'AssemblyQuerySet': {
                'all': [
                    Q(is_private=False),
                ],
            },
            'AnalysisJobDownloadQuerySet': {
                'all': [
                    Q(job__sample__isnull=True) | Q(job__sample__is_suppressed=False),
                    Q(job__study__is_private=False),
                    Q(job__run__is_private=False) | Q(job__assembly__is_private=False),
                    Q(job__analysis_status_id=AnalysisStatus.COMPLETED) | Q(job__analysis_status_id=AnalysisStatus.QC_NOT_PASSED)
                ],
            },
            'AssemblyExtraAnnotationQuerySet': {
                'all': [
                    Q(assembly__is_private=False),
                ],
            },
            'RunExtraAnnotationQuerySet': {
                'all': [
                    Q(run__is_private=False),
                ],
            },
        }

        if request is not None and request.user.is_authenticated:
            _username = request.user.username
            _query_filters['StudyQuerySet']['authenticated'] = \
                [Q(submission_account_id__iexact=_username) | Q(is_private=False)]
            _query_filters['StudyDownloadQuerySet']['authenticated'] = \
                [Q(study__submission_account_id__iexact=_username) |
                 Q(study__is_private=False)]
            _query_filters['SampleQuerySet']['authenticated'] = \
                [Q(submission_account_id__iexact=_username) | Q(is_private=False)]
            _query_filters['RunQuerySet']['authenticated'] = \
                [Q(study__submission_account_id__iexact=_username, is_private=True) |
                 Q(is_private=False)]
            _query_filters['AssemblyQuerySet']['authenticated'] = \
                [Q(samples__studies__submission_account_id__iexact=_username,
                   is_private=True) |
                 Q(is_private=False)]
            _query_filters['AnalysisJobDownloadQuerySet']['authenticated'] = \
                [Q(job__study__submission_account_id__iexact=_username,
                   job__is_private=True) |
                 Q(job__study__submission_account_id__iexact=_username,
                   job__assembly__is_private=True) |
                 Q(job__run__is_private=False) | Q(job__assembly__is_private=False)]
            _query_filters['AssemblyExtraAnnotationQuerySet']['authenticated'] = \
                [Q(assembly__samples__studies__submission_account_id__iexact=_username,
                   is_private=True) |
                 Q(assembly__is_private=False)]
            _query_filters['RunExtraAnnotationQuerySet']['authenticated'] = \
                [Q(sun__samples__studies__submission_account_id__iexact=_username,
                   is_private=True) |
                 Q(run__is_private=False)]

        filters = _query_filters.get(self.__class__.__name__)

        if filters:
            return self._apply_filters(filters, request)
        return self

    def _apply_filters(self, filters, request):
        """Apply the QS filters for "all" and "authenticated" users
        """
        q = list()
        if request is not None and request.user.is_authenticated:
            if not request.user.is_superuser:
                q.extend(filters['authenticated'])
        else:
            q.extend(filters['all'])
        return self.filter(*q)


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


class PipelineManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class PipelineAnnotatedManager(models.Manager):
    def get_queryset(self):
        return super() \
            .get_queryset() \
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
    objects_annotated = PipelineAnnotatedManager()

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
    """
    Current values:
        1	scheduled
        2	running
        3	completed
        4	failed
        5	suppressed
        6	QC not passed
        7	Unable to process
        8	unknown
    """
    SCHEDULED = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    SUPPRESSED = 5
    QC_NOT_PASSED = 6
    UNABLE_TO_PROCESS = 7
    UNKNOWN = 8

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
        # TODO: When production MySQL is updated or when Python3.6 is dropped and
        #  so Django4 adopted, change this constraint to lineage + biome_name.
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
        return str(self.pubmed_id)


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
        blank=True, null=True, on_delete=models.CASCADE)
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
    file_checksum = models.CharField(
        db_column='CHECKSUM', max_length=255,
        null=False, blank=True)
    checksum_algorithm = models.ForeignKey(
        'ChecksumAlgorithm', db_column='CHECKSUM_ALGORITHM',
        blank=True, null=True, on_delete=models.CASCADE
    )

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


class ChecksumAlgorithm(models.Model):
    """Checksum for download files
    """
    name = models.CharField(
        db_column='NAME',
        max_length=255,
        unique=True)

    class Meta:
        db_table = 'CHECKSUM_ALGORITHM'

    def __str__(self):
        return self.name


class BaseDownloadManager(models.Manager):

    select_related = []
    default_select_related = [
        'group_type',
        'subdir',
        'file_format',
        'description',
        'checksum_algorithm',
    ]

    def __init__(self, select_related, *args, **kwargs):
        self.select_related = self.default_select_related + select_related or []
        super(BaseDownloadManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db) \
            .select_related(*self.select_related)

    def available(self, request):
        return self.get_queryset().available(request)


class AnalysisJobDownloadQuerySet(BaseQuerySet):
    pass


class AnalysisJobDownloadManager(models.Manager):
    def get_queryset(self):
        return AnalysisJobDownloadQuerySet(self.model, using=self._db) \
            .select_related(
                'job',
                'pipeline',
                'group_type',
                'subdir',
                'file_format',
                'description')

    def available(self, request):
        return self.get_queryset()\
            .select_related(
                'group_type',
                'subdir',
                'file_format',
                'description',
                'checksum_algorithm',
                'job') \
            .available(request)


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


class AssemblyExtraAnnotationQuerySet(BaseQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AssemblyExtraAnnotationManager(BaseDownloadManager):
    pass



class AssemblyExtraAnnotation(BaseDownload):
    assembly = models.ForeignKey(
        'Assembly', db_column='ASSEMBLY_ID', related_name='extra_annotations',
        on_delete=models.CASCADE)

    @property
    def accession(self):
        return self.assembly.accession

    objects = AssemblyExtraAnnotationManager(select_related=[])

    class Meta:
        db_table = 'ASSEMBLY_DOWNLOAD'
        unique_together = (('realname', 'alias', 'assembly'),)
        ordering = ('group_type', 'alias',)

    def __str__(self):
        return f'AssemblyExtraAnnotation: {self.id} {self.alias}'

class RunExtraAnnotationQuerySet(BaseQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class RunExtraAnnotationManager(BaseDownloadManager):
    pass

class RunExtraAnnotation(BaseDownload):
    run = models.ForeignKey(
        'Run', db_column='RUN_ID', related_name='extra_annotations',
        on_delete=models.CASCADE)

    @property
    def accession(self):
        return self.run.accession

    objects = RunExtraAnnotationManager(select_related=[])

    class Meta:
        db_table = 'RUN_DOWNLOAD'
        unique_together = (('realname', 'alias', 'run'),)
        ordering = ('group_type', 'alias',)

    def __str__(self):
        return f'RunExtraAnnotation: {self.id} {self.alias}'


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
            'checksum_algorithm'
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


class StudyQuerySet(BaseQuerySet, SuppressQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mydata(self, request):
        if request.user.is_authenticated:
            _username = request.user.username
            return self.distinct() \
                .filter(Q(submission_account_id__iexact=_username))
        return ()

    def recent(self):
        return self.order_by('-last_update')


class StudyManager(models.Manager):
    def get_queryset(self):
        # TODO: remove biome when schema updated
        study_samples = StudySample.objects.filter(study=OuterRef('study_id'))
        samples_count_subq = study_samples.values('study') \
            .annotate(samples_count=Count('study_id')).values('samples_count')
        return StudyQuerySet(self.model, using=self._db) \
            .annotate(samples_count=Subquery(samples_count_subq)) \
            .defer('biome')

    def available(self, request):
        return self.get_queryset().available(request)

    def recent(self, request):
        return self.get_queryset().available(request).recent()

    def mydata(self, request):
        return self.get_queryset().mydata(request)


class Study(ENASyncableModel):

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
    public_release_date = models.DateField(
        db_column='PUBLIC_RELEASE_DATE', blank=True, null=True)
    study_abstract = models.TextField(
        db_column='STUDY_ABSTRACT', blank=True, null=True)
    study_name = models.CharField(
        db_column='STUDY_NAME', max_length=4000, blank=True, null=True)
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
                Prefetch('studies', queryset=Study.objects.available(request)),
                Prefetch('biome', queryset=Biome.objects.all()),
            )
        return queryset

    def get_by_id_or_slug_or_404(self, id_or_slug):
        if type(id_or_slug) is int or (type(id_or_slug) is str and id_or_slug.isnumeric()):
            return get_object_or_404(self.get_queryset(), super_study_id=int(id_or_slug))
        return get_object_or_404(self.get_queryset(), url_slug=id_or_slug)


class SuperStudy(models.Model):
    """
    Aggregation of studies.
    Each Super Study will have multiples Studies.
        - each study might be tagged as a "flagship" study or not.
    Each Super Study may also have multiple Genome Catalogues linked to it.
    """
    super_study_id = models.AutoField(db_column='STUDY_ID',
                                      primary_key=True)
    title = models.CharField(db_column='TITLE', max_length=100)
    url_slug = models.SlugField(db_column='URL_SLUG', max_length=100)
    description = models.TextField(db_column='DESCRIPTION', blank=True, null=True, help_text=MARKDOWN_HELP)

    studies = models.ManyToManyField(
        'Study', through='SuperStudyStudy', related_name='super_studies', blank=True
    )

    biomes = models.ManyToManyField(
        'Biome', through='SuperStudyBiome', related_name='super_studies', blank=True
    )

    genome_catalogues = models.ManyToManyField(
        'GenomeCatalogue', through='SuperStudyGenomeCatalogue', related_name='super_studies', blank=True
    )

    logo = models.TextField(db_column='LOGO', max_length=100000, blank=True, null=True)

    objects = SuperStudyManager()

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.logo:
            return self.logo
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
    is_flagship = models.BooleanField(
        default=True
    )

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


class SuperStudyGenomeCatalogue(models.Model):
    """
    Relationship between a Super Study and a MAG Catalogue
    """
    genome_catalogue = models.ForeignKey(
        'GenomeCatalogue',
        db_column='GENOME_CATALOGUE_ID',
        on_delete=models.CASCADE,
    )
    super_study = models.ForeignKey(
        'SuperStudy',
        db_column='SUPER_STUDY_ID',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.super_study} - {self.genome_catalogue}'

    class Meta:
        db_table = 'SUPER_STUDY_GENOME_CATALOGUE'
        unique_together = (('genome_catalogue', 'super_study'),)
        verbose_name_plural = 'super studies genome catalogues'


class SampleQuerySet(BaseQuerySet, SuppressQuerySet):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SampleManager(models.Manager):
    def get_queryset(self):
        return SampleQuerySet(self.model, using=self._db) \
            .select_related(
                'biome'
            )

    def available(self, request, prefetch=False):
        queryset = self.get_queryset().available(request)
        if prefetch:
            queryset = queryset.prefetch_related(
                Prefetch('biome', queryset=Biome.objects.all()),
                Prefetch('studies', queryset=Study.objects.available(request)),
                Prefetch('metadata', queryset=SampleAnn.objects.all())
            ).defer(
                'is_private',
                'metadata_received',
                'sequencedata_received',
                'sequencedata_archived',
                'submission_account_id',
            )
        return queryset


class Sample(ENASyncableModel):
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
                'runs__sample', filter=Q(runs__is_private=False), distinct=True)
        ) \
            .annotate(
            runs_count=Count(
                'runs', filter=Q(runs__is_private=False), distinct=True)
        )


class ExperimentType(models.Model):
    experiment_type_id = models.SmallIntegerField(
        db_column='EXPERIMENT_TYPE_ID', primary_key=True)
    experiment_type = models.CharField(
        db_column='EXPERIMENT_TYPE', max_length=30,
        help_text="Experiment type, e.g. metagenomic")

    objects = ExperimentTypeManager()

    class Meta:
        db_table = 'EXPERIMENT_TYPE'

    def __str__(self):
        return self.experiment_type


class Status(models.Model):
    """Status
    Current values as constants to make
    the code easier to read
    """
    DRAFT = 1
    PRIVATE = 2
    CANCELLED = 3
    PUBLIC = 4
    SUPPRESSED = 5
    KILLED = 6
    TEMPORARY_SUPPRESSED = 7
    TEMPORARY_KILLED = 8

    status_id = models.SmallIntegerField(
        db_column='STATUS_ID', primary_key=True)
    status = models.CharField(
        db_column='STATUS', max_length=25)

    class Meta:
        db_table = 'STATUS'
        ordering = ('status_id',)

    def __str__(self):
        return self.status


class RunQuerySet(BaseQuerySet, SuppressQuerySet):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RunManager(models.Manager):
    def get_queryset(self):
        return RunQuerySet(self.model, using=self._db) \
            .select_related(
                'sample',
                'study',
                'experiment_type'
            )

    def available(self, request):
        return self.get_queryset().available(request)


class Run(ENASyncableModel):
    run_id = models.BigAutoField(
        db_column='RUN_ID', primary_key=True)
    accession = models.CharField(
        db_column='ACCESSION', max_length=80, blank=True, null=True)
    secondary_accession = models.CharField(
        db_column='SECONDARY_ACCESSION', max_length=100, blank=True, null=True)
    sample = models.ForeignKey(
        'Sample', db_column='SAMPLE_ID', related_name='runs',
        on_delete=models.CASCADE, blank=True, null=True)
    study = models.ForeignKey(
        'Study', db_column='STUDY_ID', related_name='runs',
        on_delete=models.CASCADE, blank=True, null=True)
    # We use this field to link to the study if we haven't analyzed the study, hence
    # there is no Study linked (`study` fk is none)
    ena_study_accession = models.CharField(
        db_column='ENA_STUDY_ACCESSION', validators=[validate_ena_study_accession],
        help_text='ENA Study accession.',
        max_length=20, blank=True, null=True)
    # TODO: not consistent, schema changes may be needed
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


class AssemblyQuerySet(BaseQuerySet, SuppressQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AssemblyManager(models.Manager):
    def get_queryset(self):
        return AssemblyQuerySet(self.model, using=self._db)

    def available(self, request):
        return self.get_queryset().available(request) \
            .select_related(
            'experiment_type',
        )


class Assembly(ENASyncableModel):

    assembly_id = models.BigAutoField(
        db_column='ASSEMBLY_ID', primary_key=True)
    accession = models.CharField(
        db_column='ACCESSION', max_length=80, blank=True, null=True)
    wgs_accession = models.CharField(
        db_column='WGS_ACCESSION', max_length=100, blank=True, null=True)
    legacy_accession = models.CharField(
        db_column='LEGACY_ACCESSION', max_length=100, blank=True, null=True)
    experiment_type = models.ForeignKey(
        ExperimentType, db_column='EXPERIMENT_TYPE_ID',
        related_name='assemblies',
        on_delete=models.CASCADE, blank=True, null=True)
    runs = models.ManyToManyField(
        'Run', through='AssemblyRun', related_name='assemblies', blank=True)
    samples = models.ManyToManyField(
        'Sample', through='AssemblySample', related_name='assemblies',
        blank=True)
    study = models.ForeignKey("emgapi.Study", db_column="STUDY_ID",
        on_delete=models.SET_NULL, null=True, blank=True)

    coverage = models.IntegerField(db_column="COVERAGE", null=True, blank=True)

    min_gap_length = models.IntegerField(db_column="MIN_GAP_LENGTH", null=True, blank=True)

    objects = AssemblyManager()

    class Meta:
        db_table = 'ASSEMBLY'
        ordering = ('accession',)
        unique_together = (
            ('assembly_id', 'accession'),
            ('accession', 'wgs_accession', 'legacy_accession')
        )
        verbose_name_plural = 'assemblies'

    def __str__(self):
        return self.accession or str(self.assembly_id)


class AssemblyRun(models.Model):
    assembly = models.ForeignKey(
        'Assembly', db_column='ASSEMBLY_ID', on_delete=models.CASCADE)
    run = models.ForeignKey(
        'Run', db_column='RUN_ID', on_delete=models.CASCADE)

    class Meta:
        db_table = 'ASSEMBLY_RUN'
        unique_together = (('assembly', 'run'),)
        verbose_name_plural = 'assembly runs'

    def __str__(self):
        return 'Assembly:{} - Run: {}'.format(self.assembly, self.run)


class AssemblySample(models.Model):
    assembly = models.ForeignKey(
        'Assembly', db_column='ASSEMBLY_ID', on_delete=models.CASCADE)
    sample = models.ForeignKey(
        'Sample', db_column='SAMPLE_ID', on_delete=models.CASCADE)

    class Meta:
        db_table = 'ASSEMBLY_SAMPLE'
        unique_together = (('assembly', 'sample'),)
        verbose_name_plural = 'assembly samples'

    def __str__(self):
        return 'Assembly:{} - Sample:{}'.format(self.assembly, self.sample)


class AnalysisJobQuerySet(BaseQuerySet, MySQLQuerySet, SuppressQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def available(self, request=None):
        """Override BaseQuerySet with the AnalysisJob auth rules
        Use cases
        - all           | has access to public analyses
        - authenticated | has access to public and private analyses they own

        Filtered out analyses for SUPPRESSED samples
        """
        query_filters = {
            "all": [
                Q(study__is_private=False),
                Q(sample__isnull=True) | Q(sample__is_suppressed=False),
                Q(run__is_private=False) | Q(assembly__is_private=False),
                Q(analysis_status_id=AnalysisStatus.COMPLETED)
                | Q(analysis_status_id=AnalysisStatus.QC_NOT_PASSED),
            ],
        }

        if request is not None and request.user.is_authenticated:
            username = request.user.username
            query_filters["authenticated"] = [
                Q(sample__isnull=True) | Q(sample__is_suppressed=False),
                Q(study__submission_account_id__iexact=username, run__is_private=True)
                | Q(
                    study__submission_account_id__iexact=username,
                    assembly__is_private=True,
                )
                | Q(run__is_private=False)
                | Q(assembly__is_private=False)
            ]

        return self._apply_filters(query_filters, request)


class AnalysisJobManager(models.Manager):
    def get_queryset(self):
        """Customized Analysis Job QS.
        There are 2 very custom bits here:
        
        straight_join
        -------------
        This one is needed because of a mysql bug that causes the optimizer
        to https://code.djangoproject.com/ticket/22438

        force_index
        -----------
        This one is more of a mistery to me. The join with PIPELINE_RELEASE 
        is causing a full table scan on PIPELINE_RELEASE.

        | id | select\_type | table | type | possible\_keys | key | key\_len | ref | rows | filtered | Extra |
        | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
        | 1 | SIMPLE | PIPELINE\_RELEASE | ALL | PRIMARY,PIPELINE\_RELEASE\_PIPELINE\_ID\_RELEASE\_VERSION\_d40fe384\_uniq,PIPELINE\_RELEASE\_PIPELINE\_ID\_index | NULL | NULL | NULL | 6 | 83.33 | Using where; Using join buffer \(Block Nested Loop\) |

        By forcing the index PRIMARY on the JOIN the query is faster:

        | id | select\_type | table | type | possible\_keys | key | key\_len | ref | rows | filtered | Extra |
        | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
        | 1 | SIMPLE | PIPELINE\_RELEASE | eq\_ref | PRIMARY | PRIMARY | 2 | emg.ANALYSIS\_JOB.PIPELINE\_ID | 1 | 100 | NULL |

        IMPORTANT: it is also required that the ordering of the query set is done by ANALYSIS_JOB.PIPELINE_ID and not a 
                   field of PIPELINE_RELEASE. This was changes in emgapi.viewsets.BaseAnalysisGenericViewSet.ordering

        TODO: figure our what is going on with this query.
        """
        _qs = AnalysisJobAnn.objects.all() \
            .select_related('var')
        return AnalysisJobQuerySet(self.model, using=self._db) \
            .straight_join() \
            .force_index("PRIMARY", table_name="PIPELINE_RELEASE", for_="JOIN") \
            .select_related(
                'analysis_status',
                'experiment_type',
                'run',
                'study',
                'assembly',
                'pipeline',
                'sample') \
            .prefetch_related(
                Prefetch('analysis_metadata', queryset=_qs),)

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


class AnalysisJob(SuppressibleModel, PrivacyControlledModel):
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
    analysis_summary_json = models.JSONField(
        db_column='ANALYSIS_SUMMARY_JSON', blank=True, null=True)
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
        # if self.analysis_summary_json:
        #     return self.analysis_summary_json

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
    objects_admin = models.Manager()

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
        verbose_name_plural = 'blacklisted study'
        verbose_name_plural = 'blacklisted studies'

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
        verbose_name = 'variable name'                

    def __str__(self):
        return self.var_name


class SampleAnnQuerySet(BaseQuerySet):
    pass


class SampleAnnManager(models.Manager):
    def get_queryset(self):
        return SampleAnnQuerySet(self.model, using=self._db) \
            .select_related('sample', 'var')


class SampleAnn(models.Model):
    id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(
        Sample, db_column='SAMPLE_ID',
        related_name="metadata", on_delete=models.CASCADE)
    units = models.CharField(
        db_column='UNITS', max_length=25, blank=True, null=True)
    var = models.ForeignKey(
        'VariableNames', db_column='VAR_ID', on_delete=models.CASCADE)
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
        verbose_name = 'analysis meta variable name'

    def __str__(self):
        return self.var_name


class AnalysisJobAnnManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().select_related('job', 'var')


class AnalysisJobAnn(models.Model):
    job = models.ForeignKey(AnalysisJob, db_column='JOB_ID', related_name='analysis_metadata', on_delete=models.CASCADE)
    units = models.CharField(db_column='UNITS', max_length=25, blank=True, null=True)
    var = models.ForeignKey(AnalysisMetadataVariableNames, on_delete=models.CASCADE)
    var_val_ucv = models.CharField(db_column='VAR_VAL_UCV', max_length=4000, blank=True, null=True)

    objects = AnalysisJobAnnManager()

    class Meta:
        db_table = 'ANALYSIS_JOB_ANN'
        unique_together = (('job', 'var'), ('job', 'var'),)

    def __str__(self):
        return '%s %s' % (self.job, self.var)

    def multiple_pk(self):
        return '%s/%s' % (self.var.var_name, self.var_val_ucv)


class CogCat(models.Model):

    name = models.CharField(db_column='NAME', max_length=80, unique=True)
    description = models.CharField(db_column='DESCRIPTION', max_length=80)

    class Meta:
        db_table = 'COG'
        verbose_name_plural = 'COG categories'


class AntiSmashGC(models.Model):
    name = models.CharField(db_column='NAME', max_length=80)
    description = models.CharField(db_column='DESCRIPTION', max_length=80)

    class Meta:
        db_table = 'ANTISMASH_GENECLUSTER'
        verbose_name_plural = 'antiSMASH clusters'


class GeographicLocation(models.Model):

    name = models.CharField(db_column='CONTINENT', max_length=80, unique=True)

    class Meta:
        db_table = 'GEOGRAPHIC_RANGE'

    def __str__(self):
        return self.name


class GenomeSet(models.Model):

    name = models.CharField(db_column='NAME', max_length=40, unique=True)

    class Meta:
        db_table = 'GENOME_SET'

    def __str__(self):
        return self.name


class GenomeCatalogue(models.Model):
    catalogue_id = models.SlugField(
        db_column='CATALOGUE_ID', max_length=100)
    version = models.CharField(db_column='VERSION', max_length=20)
    name = models.CharField(db_column='NAME', max_length=100, unique=True)
    description = models.TextField(db_column='DESCRIPTION', null=True, blank=True,
                                   help_text=MARKDOWN_HELP)
    protein_catalogue_name = models.CharField(db_column='PROTEIN_CATALOGUE_NAME', max_length=100, null=True, blank=True)
    protein_catalogue_description = models.TextField(db_column='PROTEIN_CATALOGUE_DESCRIPTION', null=True, blank=True,
                                                     help_text=MARKDOWN_HELP)
    last_update = models.DateTimeField(db_column='LAST_UPDATE', default=timezone.now)
    result_directory = models.CharField(db_column='RESULT_DIRECTORY', max_length=100, null=True, blank=True)
    biome = models.ForeignKey(
        Biome, db_column='BIOME_ID',
        on_delete=models.CASCADE,
        null=True, blank=True)
    genome_count = models.IntegerField(
        db_column='GENOME_COUNT',
        null=True,
        blank=True,
        help_text='Number of genomes available in the web database (species-level cluster reps only)')
    unclustered_genome_count = models.IntegerField(
        db_column='UNCLUSTERED_GENOME_COUNT',
        null=True,
        blank=True,
        help_text='Total number of genomes in the catalogue (including cluster reps and members)'
    )
    ftp_url = models.CharField(
        db_column='FTP_URL',
        max_length=200,
        default=settings.MAGS_FTP_SITE
    )
    pipeline_version_tag = models.CharField(
        db_column='PIPELINE_VERSION_TAG',
        max_length=20,
        default=settings.LATEST_MAGS_PIPELINE_TAG
    )

    class Meta:
        unique_together = ('biome', 'version')
        db_table = 'GENOME_CATALOGUE'

    def __str__(self):
        return self.name

    def calculate_genome_count(self):
        self.genome_count = self.genomes.count()
        self.save()


class GenomeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'biome',
            'geo_origin',
            'catalogue'
        ).prefetch_related(
            'pangenome_geographic_range'
        )


class Genome(models.Model):

    ISOLATE = 'isolate'
    MAG = 'mag'
    TYPE_CHOICES = (
        (MAG, 'MAG'),
        (ISOLATE, 'Isolate'),
    )

    objects = GenomeManager()

    genome_id = models.AutoField(
        db_column='GENOME_ID', primary_key=True)
    accession = models.CharField(db_column='GENOME_ACCESSION', max_length=40, unique=True)

    ena_genome_accession = models.CharField(db_column='ENA_GENOME_ACCESSION',
                                            max_length=20, unique=True, null=True, blank=True)
    ena_sample_accession = models.CharField(db_column='ENA_SAMPLE_ACCESSION', max_length=20,
                                            null=True, blank=True)
    ena_study_accession = models.CharField(db_column='ENA_STUDY_ACCESSION', max_length=20, null=True)

    ncbi_genome_accession = models.CharField(db_column='NCBI_GENOME_ACCESSION',
                                             max_length=20, unique=True, null=True, blank=True)
    ncbi_sample_accession = models.CharField(db_column='NCBI_SAMPLE_ACCESSION', max_length=20, null=True, blank=True)
    ncbi_study_accession = models.CharField(db_column='NCBI_STUDY_ACCESSION', max_length=20, null=True, blank=True)

    img_genome_accession = models.CharField(db_column='IMG_GENOME_ACCESSION', max_length=20,
                                            unique=True, null=True, blank=True)
    patric_genome_accession = models.CharField(db_column='PATRIC_GENOME_ACCESSION', max_length=20, unique=True,
                                               blank=True, null=True)

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
                            choices=TYPE_CHOICES,
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

    num_genomes_total = models.IntegerField(db_column='PANGENOME_TOTAL_GENOMES', null=True, blank=True)
    pangenome_size = models.IntegerField(db_column='PANGENOME_SIZE', null=True, blank=True)
    pangenome_core_size = models.IntegerField(db_column='PANGENOME_CORE_PROP', null=True, blank=True)
    pangenome_accessory_size = models.IntegerField(db_column='PANGENOME_ACCESSORY_PROP', null=True, blank=True)

    last_update = models.DateTimeField(db_column='LAST_UPDATE', auto_now=True)
    first_created = models.DateTimeField(db_column='FIRST_CREATED', auto_now_add=True)

    geo_origin = models.ForeignKey('GeographicLocation', db_column='GEOGRAPHIC_ORIGIN', null=True, blank=True, on_delete=models.CASCADE)

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

    catalogue = models.ForeignKey('GenomeCatalogue', db_column='GENOME_CATALOGUE', on_delete=models.CASCADE,
                                  related_name='genomes')

    @property
    def geographic_range(self):
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


class GenomeCogCounts(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID',
                               on_delete=models.CASCADE, db_index=True)
    cog = models.ForeignKey(CogCat, db_column='COG_ID',
                            on_delete=models.DO_NOTHING)
    genome_count = models.IntegerField(db_column='GENOME_COUNT')

    class Meta:
        db_table = 'GENOME_COG_COUNTS'
        unique_together = ('genome', 'cog')


class KeggClass(models.Model):

    class_id = models.CharField(db_column='CLASS_ID', max_length=10,
                                unique=True)
    name = models.CharField(db_column='NAME', max_length=80)
    parent = models.ForeignKey('self', db_column='PARENT', null=True, on_delete=models.CASCADE)

    class Meta:
        db_table = 'KEGG_CLASS'

    def __str__(self):
        return self.name


class GenomeKeggClassCounts(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID',
                               on_delete=models.CASCADE, db_index=True)
    kegg_class = models.ForeignKey(KeggClass, db_column='KEGG_ID',
                                   on_delete=models.DO_NOTHING)
    genome_count = models.IntegerField(db_column='GENOME_COUNT')

    class Meta:
        db_table = 'GENOME_KEGG_CLASS_COUNTS'
        unique_together = ('genome', 'kegg_class')


class KeggModule(models.Model):

    name = models.CharField(db_column='MODULE_NAME', max_length=10,
                            unique=True)
    description = models.CharField(db_column='DESCRIPTION', max_length=200)

    class Meta:
        db_table = 'KEGG_MODULE'

    def __str__(self):
        return self.name


class GenomeKeggModuleCounts(models.Model):

    genome = models.ForeignKey(Genome, db_column='GENOME_ID',
                               on_delete=models.CASCADE, db_index=True)
    kegg_module = models.ForeignKey(KeggModule, db_column='KEGG_MODULE',
                                    on_delete=models.DO_NOTHING)
    genome_count = models.IntegerField(db_column='GENOME_COUNT')

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


class GenomeDownload(BaseDownload):
    genome = models.ForeignKey(
        'Genome', db_column='GENOME_ID',
        on_delete=models.CASCADE, db_index=True)

    @property
    def accession(self):
        return self.genome.accession

    objects = BaseDownloadManager(['genome'])

    class Meta:
        db_table = 'GENOME_DOWNLOAD'
        unique_together = (('realname', 'alias', 'genome'),)
        ordering = ('group_type', 'alias')


class GenomeCatalogueDownload(BaseDownload):
    genome_catalogue = models.ForeignKey('GenomeCatalogue',
                                         db_column='GENOME_CATALOGUE_ID',
                                         on_delete=models.CASCADE)

    @property
    def accession(self):
        return self.genome_catalogue.catalogue_id

    objects = BaseDownloadManager(['genome_catalogue'])

    class Meta:
        db_table = 'GENOME_CATALOGUE_DOWNLOAD'
        unique_together = (('realname', 'alias', 'genome_catalogue'),)
        ordering = ('group_type', 'alias')


class Search(models.Lookup):
    lookup_name = 'search'

    def as_mysql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return 'MATCH (%s) AGAINST (%s IN BOOLEAN MODE)' % (lhs, rhs), params


class LegacyAssembly(models.Model):
    """Assemblies that were re-uploaded and got new ERZ accessions.
    This table has the mapping between the old accessions and the new ones.
    It's used to keep the "old" accessions live.
    """
    legacy_accession = models.CharField(
        "Legacy assembly", db_column="LEGACY_ACCESSION", db_index=True, max_length=80)
    new_accession = models.CharField(
        "New accession", db_column="NEW_ACCESSION", max_length=80)
    legacy_date = models.DateField("Legacy date", db_column="LEGACY_DATE", null=True, blank=True)
    comments = models.CharField("Comments", db_column="COMMENTS", max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'LEGACY_ASSEMBLY'
        unique_together = (('legacy_accession', 'new_accession'),)


    def __str__(self):
        return f"Legacy Assembly:{self.legacy_accession} - New Accession:{self.new_accession}"

models.CharField.register_lookup(Search)
models.TextField.register_lookup(Search)

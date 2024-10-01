#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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
import os
import logging
from json import JSONDecodeError

import inflection
import csv
import math

import requests

from django.conf import settings
from django.db.models import Prefetch, Count, Q
from django.http import Http404, HttpResponseBadRequest, HttpResponse, StreamingHttpResponse
from django.middleware import csrf
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.clickjacking import xframe_options_exempt

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from rest_framework import filters, viewsets, mixins, permissions, renderers, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_csv.misc import Echo
from rest_framework.reverse import reverse

from rest_framework_json_api import filters as drfja_filters
from rest_framework_json_api.django_filters import DjangoFilterBackend as DRFJADjangoFilterBackend
from rest_framework_json_api.views import ReadOnlyModelViewSet

from . import models as emg_models
from . import serializers as emg_serializers
from . import mixins as emg_mixins
from . import permissions as emg_perms
from . import viewsets as emg_viewsets
from . import utils as emg_utils
from . import renderers as emg_renderers
from . import filters as emg_filters
from . import third_party_metadata
from .sourmash import validate_sourmash_signature, save_signature, send_sourmash_jobs, get_sourmash_job_status, \
    get_result_file

from emgcli.pagination import FasterCountPagination

from emgena import models as ena_models
from emgena import serializers as ena_serializers

logger = logging.getLogger(__name__)


class DataViewSet(viewsets.ViewSet):
    def list(self, request):
        data = {
            "study_accession": "MGYS00006708",
            "run_accession": "SRR12560534",
            "sample_accession": "MGYS00006708",
            "assembly_accession": None,
            "accession": "MGYA00779423",
            "experiment_type": "Amplicon",
            "instrument_model": "Illumina MiSeq",
            "instrument_platform": "Illumina",
            "pipeline_version": "5",
            "downloads": [
                {
                    "alias": "SRR12560534_MERGED_FASTQ.fasta.gz",
                    "download_type": "Sequence data",
                    "file_type": "fasta",
                    "long_description": "Processed nucleotide reads",
                    "short_description": "Processed nucleotide reads",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ.fasta.gz",
                    "compression:":  True
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_SSU_MAPSeq.mseq.gz",
                    "download_type": "Taxonomic analysis",
                    "file_type": "tsv",
                    "long_description": "MAPSeq output file for SSU",
                    "short_description": "MAPseq SSU assignments",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_SSU_MAPSeq.mseq.gz",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_LSU_MAPSeq.mseq.gz",
                    "download_type": "Taxonomic analysis",
                    "file_type": "tsv",
                    "long_description": "MAPSeq output file for LSU",
                    "short_description": "MAPseq LSU assignments",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_LSU_MAPSeq.mseq.gz",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_SSU_OTU.tsv",
                    "download_type": "Taxonomic analysis",
                    "file_type": "tsv",
                    "long_description": "OTUs and taxonomic assignments for SSU rRNA",
                    "short_description": "OTUs, counts and taxonomic assignments for SSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_SSU_OTU.tsv",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_LSU_OTU.tsv",
                    "download_type": "Taxonomic analysis",
                    "file_type": "tsv",
                    "long_description": "OTUs and taxonomic assignments for LSU rRNA",
                    "short_description": "OTUs, counts and taxonomic assignments for LSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_LSU_OTU.tsv",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_SSU_OTU_TABLE_HDF5.biom",
                    "download_type": "Taxonomic analysis",
                    "file_type": "biom",
                    "long_description": "OTUs and taxonomic assignments for SSU rRNA",
                    "short_description": "OTUs, counts and taxonomic assignments for SSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_SSU_OTU_TABLE_HDF5.biom",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_LSU_OTU_TABLE_HDF5.biom",
                    "download_type": "Taxonomic analysis",
                    "file_type": "biom",
                    "long_description": "OTUs and taxonomic assignments for LSU rRNA",
                    "short_description": "OTUs, counts and taxonomic assignments for LSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_LSU_OTU_TABLE_HDF5.biom",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_SSU_OTU_TABLE_JSON.biom",
                    "download_type": "Taxonomic analysis",
                    "file_type": "biom",
                    "long_description": "OTUs and taxonomic assignments for SSU rRNA",
                    "short_description": "OTUs, counts and taxonomic assignments for SSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_SSU_OTU_TABLE_JSON.biom",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_LSU_OTU_TABLE_JSON.biom",
                    "download_type": "Taxonomic analysis",
                    "file_type": "biom",
                    "long_description": "OTUs and taxonomic assignments for LSU rRNA",
                    "short_description": "OTUs, counts and taxonomic assignments for LSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_LSU_OTU_TABLE_JSON.biom",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_SSU.fasta.gz",
                    "download_type": "Taxonomic analysis",
                    "file_type": "fasta",
                    "long_description": "All reads encoding SSU rRNA",
                    "short_description": "Reads encoding SSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_SSU.fasta.gz",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_LSU.fasta.gz",
                    "download_type": "Taxonomic analysis",
                    "file_type": "fasta",
                    "long_description": "All reads encoding LSU rRNA",
                    "short_description": "Reads encoding LSU rRNA",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_LSU.fasta.gz",
                    "compression:": False
                },
                {
                    "alias": "SRR12560534_MERGED_FASTQ_5.8S.fasta.gz",
                    "download_type": "non-coding RNAs",
                    "file_type": "fasta",
                    "long_description": "All reads encoding 5.8S",
                    "short_description": "Reads encoding 5.8S",
                    "url": "https://www.ebi.ac.uk/metagenomics/api/v1/analyses/MGYA00779423/file/SRR12560534_MERGED_FASTQ_5.8S.fasta.gz",
                    "compression:": False
                }
            ]
        }
        return Response(data)


class UtilsViewSet(viewsets.GenericViewSet):
    schema = None

    def get_queryset(self):
        return ()

    @action(
        detail=False,
        methods=['get', ],
        serializer_class=emg_serializers.TokenSerializer
    )
    def csrf_token(self, request):
        """
        Retrieves csrf token
        """
        token = csrf.get_token(request)
        csrf_token = emg_models.Token(id=token, token=token)
        serializer = self.get_serializer(csrf_token)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', ],
        serializer_class=emg_serializers.ResourceSerializer
    )
    def resources(self, request):
        """
        Retrieves list of resources
        """
        stats = list()
        for m in [
            emg_models.Study, emg_models.Sample, emg_models.Run,
            emg_models.AnalysisJob
        ]:
            c = m.objects.available(self.request).count()
            r = emg_models.Resource(
                id=inflection.pluralize(m._meta.model_name),
                count=c
            )
            stats.append(r)
        serializer = self.get_serializer(stats, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', ],
        serializer_class=ena_serializers.SubmitterSerializer,
        permission_classes=[permissions.IsAuthenticated, emg_perms.IsSelf]
    )
    def myaccounts(self, request, pk=None):
        submitter = ena_models.Submitter.objects.using('era_pro') \
            .filter(
            submission_account__submission_account__iexact=self
            .request.user.username
        ) \
            .select_related('submission_account')

        serializer = self.get_serializer(submitter, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'post', ],
        serializer_class=ena_serializers.NotifySerializer,
        permission_classes=[permissions.IsAuthenticated, emg_perms.IsSelf]
    )
    def notify(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                status_code = serializer.save()
                if status_code == 200 or status_code == 201:
                    return Response("Created", status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(e, exc_info=True)
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                "Request cannot be processed.",
                status=status.HTTP_409_CONFLICT
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get', 'post', ],
        serializer_class=ena_serializers.EmailSerializer,
        permission_classes=[permissions.IsAuthenticated, emg_perms.IsSelf]
    )
    def sendemail(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(e, exc_info=True)
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyDataViewSet(emg_mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = emg_serializers.StudySerializer
    permission_classes = (
        permissions.IsAuthenticated,
        emg_perms.IsSelf,
    )

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        ('study_id', 'accession'),
        'study_name',
        'last_update',
        'samples_count',
    )

    ordering = ('-last_update',)

    search_fields = (
        '@study_name',
        '@study_abstract',
        'centre_name',
        'project_id',
    )

    def get_queryset(self):
        queryset = emg_models.Study.objects \
            .mydata(self.request)
        return queryset

    def get_serializer_class(self):
        return super(MyDataViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieve studies owned by the logged in user
        Example:
        ---
        `/mydata` retrieve own studies
        """
        return super(MyDataViewSet, self).list(request, *args, **kwargs)


class BiomeViewSet(mixins.RetrieveModelMixin,
                   emg_mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = emg_serializers.BiomeSerializer

    filter_backends = (
        emg_filters.JsonApiPlusSearchQueryParameterValidationFilter,
        filters.OrderingFilter,
        DRFJADjangoFilterBackend,
        filters.SearchFilter,
    )

    filterset_fields = (
        'biome_id',
        'biome_name',
        'depth',
        'lineage',
    )

    search_fields = (
        '@biome_name',
        'lineage',
    )

    ordering_fields = (
        'biome_name',
        'lineage',
        'samples_count',
    )

    ordering = ('biome_id',)

    lookup_field = 'lineage'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(BiomeViewSet, self).get_serializer_class()

    def get_queryset(self):
        if self.action == 'retrieve':
            queryset = emg_models.Biome.objects.all()
        else:
            queryset = emg_models.Biome.objects.filter(depth__gt=1)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves top level Biome nodes
        Example:
        ---
        `/biomes`
        """
        return super(BiomeViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves children for the given lineage
        Example:
        ---
        `/biomes/root:Environmental:Aquatic:Freshwater`
        """
        return super(BiomeViewSet, self).retrieve(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['get', ],
        serializer_class=emg_serializers.Top10BiomeSerializer
    )
    def top10(self, request):
        """
        Retrieve 10 most popular biomes
        ---
        `/biomes/top10`
        """
        sql = f"""
        SELECT
            parent.BIOME_ID,
            COUNT(distinct sample.SAMPLE_ID) as samples_count
        FROM BIOME_HIERARCHY_TREE AS node,
            BIOME_HIERARCHY_TREE AS parent,
            SAMPLE as sample
        WHERE node.lft BETWEEN parent.lft AND parent.rgt
            AND node.BIOME_ID = sample.BIOME_ID
            AND parent.BIOME_ID in {tuple(settings.TOP10BIOMES)}
        GROUP BY parent.BIOME_ID
        ORDER BY samples_count DESC
        LIMIT 10;
        """

        queryset = emg_models.Biome.objects.raw(sql)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudyViewSet(mixins.RetrieveModelMixin,
                   emg_mixins.ListModelMixin,
                   emg_viewsets.BaseStudyGenericViewSet):
    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        queryset = emg_models.Study.objects.available(self.request)
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request, prefetch=True)
            queryset = queryset.prefetch_related(
                Prefetch('samples', queryset=_qs)
            )
        if 'analysis' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.AnalysisJob.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('analysis', queryset=_qs)
            )
        if 'downloads' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.StudyDownload.objects.all()
            queryset = queryset.prefetch_related(
                Prefetch('study_download', queryset=_qs)
            )
        return queryset

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            *emg_utils.study_accession_query(self.kwargs['accession'])
        )

    def get_serializer_class(self):
        f = self.request.GET.get('format', None)
        if f in ('ldjson',):
            return emg_serializers.LDStudySerializer
        if self.action == 'retrieve':
            return emg_serializers.RetrieveStudySerializer
        return super(StudyViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of studies
        Example:
        ---
        `/studies`

        `/studies?fields[studies]=accession,study_name,samples_count,biomes`
        retrieve only selected fields

        `/studies?include=biomes` with biomes

        Filter by:
        ---
        `/studies?lineage=root:Environmental:Terrestrial:Soil`

        `/studies?centre_name=BioProject`

        Search for:
        ---
        name, abstract, author and centre name etc.

        `/studies?search=microbial%20fuel%20cells`

        """
        return super(StudyViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves study for the given accession
        Example:
        ---
        `/studies/ERP009004` retrieve study ERP009004

        `/studies/ERP009004?include=samples,biomes,publications`
        with samples, biomes and publications
        """
        return super(StudyViewSet, self).retrieve(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['get', ],
        serializer_class=emg_serializers.StudySerializer
    )
    def recent(self, request):
        """
        Retrieve 20 most recent studies
        Example:
        ---
        `/studies/recent`
        """
        limit = settings.EMG_DEFAULT_LIMIT
        queryset = emg_models.Study.objects.recent(self.request)[:limit]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get', ],
        url_name='biomes-list',
        serializer_class=emg_serializers.BiomeSerializer
    )
    def biomes(self, request, accession=None):
        """
        Retrieves list of biomes for the given study accession
        Example:
        ---
        `/studies/ERP009004/biomes` retrieve linked samples
        """

        obj = self.get_object()
        biomes = obj.samples.values('biome_id').distinct()
        queryset = emg_models.Biome.objects \
            .filter(pk__in=biomes)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)


class StudiesDownloadsViewSet(emg_mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    serializer_class = emg_serializers.StudyDownloadSerializer

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        return emg_models.StudyDownload.objects.available(self.request) \
            .filter(
            *emg_utils.related_study_accession_query(
                self.kwargs['accession'])
        )

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            Q(alias=self.kwargs['alias']),
            Q(pipeline__release_version=self.kwargs['release_version']),
        )

    def get_serializer_class(self):
        return super(StudiesDownloadsViewSet, self).get_serializer_class()

    def list(self, request, accession, *args, **kwargs):
        """
        Retrieves list of static summary files
        Example:
        ---
        `/studies/ERP009004/downloads`
        """
        return super(StudiesDownloadsViewSet, self) \
            .list(request, *args, **kwargs)


class SuperStudyViewSet(mixins.RetrieveModelMixin,
                        emg_mixins.ListModelMixin,
                        emg_viewsets.BaseSuperStudyViewSet):
    """
    Retrieves the Super Studies.
    """
    serializer_class = emg_serializers.SuperStudySerializer

    lookup_field = 'super_study_id'
    lookup_url_kwarg = 'super_study_id'

    def get_queryset(self):
        return emg_models.SuperStudy.objects.available(self.request)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of super studies
        Example:
        `/super-studies`

        `/super-studies?fields[super-studies]=super_study_id,title`
        retrieve only selected fields

        `/super-studies?include=biomes` with biomes

        Filter by:
        ---
        `/super-studies?lineage=root:Environmental:Terrestrial:Soil`

        `/studies?title=Human`

        Search for:
        ---
        title, description etc.

        `/super-studies?search=%20micriobiome`
        ---
        """
        return super(SuperStudyViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves super study for the given super_study_id
        Example:
        ---
        `/super-studies/1`
        `/super-studies/tara`
        """
        instance = emg_models.SuperStudy.objects.get_by_id_or_slug_or_404(
            kwargs.get(self.lookup_url_kwarg)
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get', ],
        url_name='biomes-list',
        serializer_class=emg_serializers.BiomeSerializer
    )
    def biomes(self, request, super_study_id=None):
        """
        Retrieves list of biomes for the given super study id
        Example:
        ---
        `/super-studies/1/biomes` retrieve linked biomes
        """

        obj = emg_models.SuperStudy.objects.get_by_id_or_slug_or_404(
            super_study_id
        )
        biomes = obj.biomes.all()
        page = self.paginate_queryset(biomes)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            biomes, many=True, context={'request': request})
        return Response(serializer.data)


class SampleViewSet(mixins.RetrieveModelMixin,
                    emg_mixins.ListModelMixin,
                    emg_viewsets.BaseSampleGenericViewSet):
    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'
    pagination_class = FasterCountPagination

    def get_queryset(self):
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        if 'analysis' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.AnalysisJob.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('analysis', queryset=_qs))
        return queryset

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            Q(accession=self.kwargs['accession']) |
            Q(primary_accession=self.kwargs['accession'])
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.RetrieveSampleSerializer
        return super(SampleViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves sample for the given accession
        Example:
        ---
        `/samples/ERS1015417`
        """
        return super(SampleViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples
        Example:
        ---
        `/samples` retrieves list of samples

        `/samples?fields[samples]=accession,runs_count,biome`
        retrieve only selected fields

        `/samples?include=runs` with related runs

        `/samples?ordering=accession` ordered by accession

        Filter by:
        ---
        `/samples?experiment_type=metagenomic`

        `/samples?species=sapiens`

        `/samples?biome=root:Environmental:Aquatic:Marine`

        Search for:
        ---
        name, descriptions, metadata, species, environment feature and material

        `/samples?search=continuous%20culture`

        """
        return super(SampleViewSet, self).list(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['get', ]
    )
    def studies_publications_annotations_existence(self, request, accession=None):
        """
        Get a summary of whether a Sample's linked Studies have any Publications which are annotated by Europe PMC.

        Example:
        ---
        `/samples/ERS1015417/check_studies_publications_for_annotations`
        """
        sample = self.get_object()
        return Response(data=third_party_metadata.get_epmc_publication_annotations_existence_for_sample(sample))

    @action(
        detail=True,
        methods=['get', ]
    )
    def contextual_data_clearing_house_metadata(self, request, accession=None):
        """
        Get additional metadata for a Sample, from Elixir's Contextual Data Clearing House.

        Example:
        ---
        `/samples/ERS235564/contextual_data_clearing_house_metadata`
        """
        sample = self.get_object()
        return Response(data=third_party_metadata.get_contextual_data_clearing_house_metadata(sample))


class RunViewSet(mixins.RetrieveModelMixin,
                 emg_mixins.ListModelMixin,
                 emg_viewsets.BaseRunGenericViewSet):
    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        queryset = emg_models.Run.objects.available(self.request)
        if 'assemblies' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Assembly.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('assemblies', queryset=_qs))
        return queryset

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            Q(accession=self.kwargs['accession']) |
            Q(secondary_accession=self.kwargs['accession'])
        )

    def get_serializer_class(self):
        return super(RunViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs
        Example:
        ---
        `/runs`

        `/runs?fields[runs]=accession,experiment_type` retrieve only
        selected fields

        Filter by:
        ---
        `/runs?experiment_type=metagenomic`

        `/runs?biome=root:Environmental:Aquatic:Marine`
        """
        return super(RunViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves run for the given accession
        Example:
        ---
        `/runs/SRR062157`
        """
        return super(RunViewSet, self).retrieve(request, *args, **kwargs)


class AssemblyViewSet(mixins.RetrieveModelMixin,
                      emg_mixins.ListModelMixin,
                      emg_viewsets.BaseAssemblyGenericViewSet):
    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        return emg_models.Assembly.objects.available(self.request)

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            Q(accession=self.kwargs['accession']) |
            Q(wgs_accession=self.kwargs['accession']) |
            Q(legacy_accession=self.kwargs['accession'])
        )

    def get_serializer_class(self):
        return super(AssemblyViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs
        Example:
        ---
        `/assembly`

        `/assembly?fields[assembly]=accession` retrieve only
        selected fields

        Filter by:
        ---
        `/assembly?biome=root:Environmental:Aquatic:Marine`
        """
        return super(AssemblyViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves run for the given accession
        Example:
        ---
        `/assembly/ERZ477576`
        """
        try:
            self.object = self.get_object()
        except Http404:
            # This code handles the Legacy assemblies. Those assemblies had their accessions
            # re-assigned to new ERZ. This code handles the legacy accessions, to prevent
            # users from getting 404 errors.
            try:
                legacy_entry = emg_models.LegacyAssembly.objects. \
                    get(legacy_accession=self.kwargs['accession'])
                return redirect("emgapi_v1:assemblies-detail",
                                accession=legacy_entry.new_accession,
                                permanent=True)
            except emg_models.LegacyAssembly.DoesNotExist:
                raise Http404()
        return super(AssemblyViewSet, self).retrieve(request, *args, **kwargs)


class AssemblyExtraAnnotationViewSet(
    emg_mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = emg_serializers.AssemblyExtraAnnotationSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'alias',
    )

    ordering = ('alias',)

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        try:
            accession = self.kwargs['accession']
        except ValueError:
            raise Http404()
        return emg_models.AssemblyExtraAnnotation.objects.available(self.request) \
            .filter(assembly__accession=accession)

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias'])
        )

    def get_serializer_class(self):
        return super(AssemblyExtraAnnotationViewSet, self) \
            .get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Assembly Extra Annotation downloads
        Example:
        ---
        `/assembly/<accession>/extra-annotations`
        """
        return super(AssemblyExtraAnnotationViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, accession, alias,
                 *args, **kwargs):
        obj = self.get_object()
        if obj.subdir is not None:
            file_path = f'{obj.subdir}/{obj.realname}'
        else:
            file_path = obj.realname
        return emg_utils.prepare_results_file_download_response(file_path, alias)


class RunExtraAnnotationViewSet(
    emg_mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = emg_serializers.RunExtraAnnotationSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'alias',
    )

    ordering = ('alias',)

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        try:
            accession = self.kwargs['accession']
        except ValueError:
            raise Http404()
        return emg_models.RunExtraAnnotation.objects.available(self.request) \
            .filter(run__accession=accession)

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias'])
        )

    def get_serializer_class(self):
        return super(RunExtraAnnotationViewSet, self) \
            .get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Run Extra Annotation downloads
        Example:
        ---
        `/run/<accession>/extra-annotations`
        """
        return super(RunExtraAnnotationViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, accession, alias,
                 *args, **kwargs):
        obj = self.get_object()
        if obj.subdir is not None:
            file_path = f'{obj.subdir}/{obj.realname}'
        else:
            file_path = obj.realname
        return emg_utils.prepare_results_file_download_response(file_path, alias)


class AnalysisJobViewSet(mixins.RetrieveModelMixin,
                         emg_mixins.ListModelMixin,
                         emg_viewsets.BaseAnalysisGenericViewSet):
    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        f = self.request.GET.get('format', None)
        if f in ('ldjson',):
            return emg_serializers.LDAnalysisSerializer
        return super(AnalysisJobViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(self.get_queryset(), Q(pk=pk))

    def get_queryset(self):
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves analysis results for the given accession
        Example:
        ---
        `/analyses`
        """
        return super(AnalysisJobViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession
        Example:
        ---
        `/analyses/MGYA00135572`
        """
        return super(AnalysisJobViewSet, self) \
            .retrieve(request, *args, **kwargs)


class AnalysisQCChartViewSet(mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = emg_serializers.AnalysisSerializer

    schema = None

    renderer_classes = (emg_renderers.TSVRenderer,)

    lookup_field = 'chart'
    lookup_value_regex = (
        'gc-distribution|'
        'nucleotide-distribution|'
        'seq-length|'
        'summary'
    )

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(self.get_queryset(), Q(pk=pk))

    def _build_path(self, name):
        return os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            self.get_object().result_directory,
            'qc-statistics', name))

    def retrieve(self, request, chart=None, *args, **kwargs):
        """
        Retrieves QC data given accession
        Example:
        ---
        `/analyses/MGYA00102827/gc-distribution`
        """
        mapping = {
            "gc-distribution": "GC-distribution",
            "nucleotide-distribution": "nucleotide-distribution",
            "seq-length": "seq-length",
            "summary": "summary",
        }

        filepath = self._build_path(
            "{name}.out".format(name=mapping[chart]))
        if not os.path.isfile(filepath):
            filepath = self._build_path(
                "{name}.out.full".format(name=mapping[chart]))
            if not os.path.isfile(filepath):
                filepath = self._build_path(
                    "{name}.out.sub-set".format(name=mapping[chart]))
        if os.path.isfile(filepath):
            logger.info("Path %r" % filepath)
            with open(filepath, "r") as f:
                return Response(f.read())
        raise Http404()


class KronaViewSet(emg_mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = emg_serializers.AnalysisSerializer

    schema = None

    renderer_classes = (renderers.StaticHTMLRenderer,)

    lookup_field = 'subdir'
    lookup_value_regex = 'lsu|ssu|unite|itsonedb'

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(self.get_queryset(), Q(pk=pk))

    def get_serializer_class(self):
        return super(KronaViewSet, self).get_serializer_class()

    @xframe_options_exempt
    def list(self, request, **kwargs):
        """
        Retrieves krona chart for the given accession and pipeline version
        Example:
        ---
        `/analyses/MGYA00102827/krona`
        """
        obj = self.get_object()
        # FIXME: Introduce sub directory structure in the taxonomy folder for new ITS results
        # e.g. taxonomy/{lsu|ssu|its}/
        krona = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            'taxonomy-summary',
            'krona.html')
        )
        if os.path.isfile(krona):
            with open(krona, "r") as k:
                return Response(k.read())
        raise Http404('No krona chart.')

    @xframe_options_exempt
    def retrieve(self, request, subdir=None, **kwargs):
        """
        Retrieves krona chart for the given accession and pipeline version
        Example:
        ---
        `/runs/GCA_900216095/pipelines/4.0/krona/lsu`
        """
        obj = self.get_object()
        base_path = os.path.join(settings.RESULTS_DIR, obj.result_directory, 'taxonomy-summary')
        if subdir in ['unite', 'itsonedb']:
            path = os.path.join(base_path, 'its', subdir)
        else:
            path = os.path.join(base_path, subdir.upper())

        if subdir == 'ssu' and not os.path.exists(path):
            # Older pipelines (1, 2...?) have SSU-only Krona in un-nested directory.
            path = base_path

        krona = os.path.abspath(os.path.join(path, 'krona.html'))
        if os.path.isfile(krona):
            with open(krona, 'r') as k:
                return Response(k.read())
        raise Http404('No krona chart.')


class AnalysisResultDownloadsViewSet(emg_mixins.ListModelMixin,
                                     viewsets.GenericViewSet):
    serializer_class = emg_serializers.AnalysisJobDownloadSerializer

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return emg_models.AnalysisJobDownload.objects.available(self.request) \
            .filter(job__pk=pk)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias']), Q(job__pk=pk)
        )

    def get_serializer_class(self):
        return super(AnalysisResultDownloadsViewSet, self) \
            .get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of static summary files
        Example:
        ---
        `/analyses/MGYA00102827/downloads`
        """
        return super(AnalysisResultDownloadsViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisResultDownloadViewSet(emg_mixins.MultipleFieldLookupMixin,
                                    mixins.RetrieveModelMixin,
                                    viewsets.GenericViewSet):
    serializer_class = emg_serializers.AnalysisJobDownloadSerializer

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'
    lookup_fields = ('accession', 'alias')

    def get_queryset(self):
        return emg_models.AnalysisJobDownload.objects.available(self.request)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias']), Q(job__pk=pk)
        )

    def get_serializer_class(self):
        return super(AnalysisResultDownloadViewSet, self) \
            .get_serializer_class()

    def retrieve(self, request, accession, alias, *args, **kwargs):
        """
        Retrieves static summary file
        Example:
        ---
        `/analyses/MGYA00102827/file/
        ERR1701760_MERGED_FASTQ_otu_table_hdf5.biom`
        """
        obj = self.get_object()
        if obj.subdir is not None:
            file_path = \
                '{0}/{1}/{2}'.format(
                    obj.job.result_directory, obj.subdir, obj.realname
                )
        else:
            file_path = \
                '{0}/{1}'.format(
                    obj.job.result_directory, obj.realname
                )
        return emg_utils.prepare_results_file_download_response(file_path, alias)


class PipelineViewSet(mixins.RetrieveModelMixin,
                      emg_mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = emg_serializers.PipelineSerializer
    queryset = emg_models.Pipeline.objects_annotated.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'release_version',
        'samples_count',
        'analysis_count',
    )

    ordering = ('release_version',)

    lookup_field = 'release_version'
    lookup_value_regex = '[0-9.]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.PipelineSerializer
        return super(PipelineViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves pipeline for the given version
        Example:
        ---
        `/pipelines/3.0`

        `/pipelines/3.0?include=tools` with tools
        """
        return super(PipelineViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of available pipeline versions
        Example:
        ---
        `/pipeline`

        `/pipeline?include=tools` with tools
        """
        return super(PipelineViewSet, self).list(request, *args, **kwargs)


class PipelineToolViewSet(emg_mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    serializer_class = emg_serializers.PipelineToolSerializer
    queryset = emg_models.PipelineTool.objects.all()

    def get_serializer_class(self):
        return super(PipelineToolViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of pipeline tools
        Example:
        ---
        `/pipeline-tools` retrieves list of pipeline tools
        """
        return super(PipelineToolViewSet, self).list(request, *args, **kwargs)


class PipelineToolVersionViewSet(mixins.RetrieveModelMixin,
                                 viewsets.GenericViewSet):
    serializer_class = emg_serializers.PipelineToolSerializer
    queryset = emg_models.PipelineTool.objects.all()

    lookup_field = 'version'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(PipelineToolVersionViewSet, self).get_serializer_class()

    def get_object(self):
        tool_name = self.kwargs['tool_name']
        version = self.kwargs['version']
        return get_object_or_404(
            emg_models.PipelineTool,
            tool_name__iexact=tool_name, version=version)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves pipeline tool details for the given pipeline version
        Example:
        ---
        `/pipeline-tools/interproscan/5.19-58.0`
        """
        return super(PipelineToolVersionViewSet, self) \
            .retrieve(request, *args, **kwargs)


class ExperimentTypeViewSet(mixins.RetrieveModelMixin,
                            emg_mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = emg_serializers.ExperimentTypeSerializer
    queryset = emg_models.ExperimentType.objects.all()

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'experiment_type',
    )

    ordering = ('experiment_type',)

    lookup_field = 'experiment_type'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.ExperimentTypeSerializer
        return super(ExperimentTypeViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves experiment type for the given id
        """
        return super(ExperimentTypeViewSet, self) \
            .retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of experiment types
        """
        return super(ExperimentTypeViewSet, self) \
            .list(request, *args, **kwargs)


class PublicationViewSet(mixins.RetrieveModelMixin,
                         emg_mixins.ListModelMixin,
                         emg_viewsets.BasePublicationGenericViewSet):
    lookup_field = 'pubmed_id'

    lookup_value_regex = '[0-9\.]+'  # noqa: W605

    def get_queryset(self):
        queryset = emg_models.Publication.objects.all()
        if 'studies' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Study.objects \
                .available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('studies', queryset=_qs))
        return queryset

    def get_serializer_class(self):
        return super(PublicationViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves publication for the given Pubmed ID
        Example:
        ---
        `/publications/{pubmed}`

        `/publications/{pubmed}?include=studies` with studies
        """
        return super(PublicationViewSet, self) \
            .retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of publications
        Example:
        ---
        `/publications` retrieves list of publications

        `/publications?include=studies` with studies

        `/publications?ordering=published_year` ordered by year

        Search for:
        ---
        title, abstract, authors, etc.

        `/publications?search=text`
        """
        return super(PublicationViewSet, self).list(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['get', ]
    )
    def europe_pmc_annotations(self, request, pubmed_id=None):
        """
        Retrieve Europe PMC Metagenomics annotations for a publication.

        Example:
        ---
        `/publications/{pubmed}/europe_pmc_annotations`
        """
        if not pubmed_id:
            raise Http404
        return Response(data=third_party_metadata.get_epmc_publication_annotations(pubmed_id))


class GenomeCatalogueViewSet(mixins.RetrieveModelMixin,
                             emg_mixins.ListModelMixin,
                             emg_viewsets.BaseGenomeCatalogueGenericViewSet):
    filterset_class = emg_filters.GenomeCatalogueFilter

    lookup_field = 'catalogue_id'
    lookup_value_regex = '[^/]+'

    queryset = emg_models.GenomeCatalogue.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves Genome Catalogues for the given Catalogue ID
        Example:
        ---
        `/genome-catalogues/{catalogue_id}`
        """
        return super(GenomeCatalogueViewSet, self) \
            .retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of genome catalogues
        Example:
        ---
        `/genome-catalogues` retrieves list of all genome catalogues

        `/genome-catalogues?ordering=last_update` ordered by age of catalogue

        Filter by:
        ---
        `/genome-catalogues?last_update__gt=2021-01-01`

        Biome lineage:
        `/genome-catalogues?lineage=root:Environmental:Aquatic:Marine`

        Case-insensitive search of biome name:
        `/genome-catalogues?biome__biome_name__icontains=marine`

        `/genome-catalogues?description__icontains=arctic`

        Search for:
        ---
        name, description, biome name, etc.

        `/genome-catalogues?search=intestine`
        """
        return super(GenomeCatalogueViewSet, self).list(request, *args, **kwargs)


class GenomeViewSet(mixins.RetrieveModelMixin,
                    emg_mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeSerializer
    filterset_class = emg_filters.GenomeFilter

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
        'length',
        'num_contigs',
        'completeness',
        'contamination',
        'num_genomes_total',
        'num_proteins',
        'last_update',
        'type'
    )

    ordering = ('-accession',)

    search_fields = (
        'accession',
        'taxon_lineage',
        'type',
        'genome_set__name',
        'catalogue__name'
    )

    queryset = emg_models.Genome.objects.all() \
        .select_related('biome', 'geo_origin', 'catalogue')


class GenomeFragmentSearchViewSet(viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeFragmentSearchSerializer
    permission_classes = [AllowAny]
    parser_classes = [FormParser, MultiPartParser]

    def get_queryset(self):
        return None

    def list(self, request):
        return Response("You need to use the POST method to send a search sequence to the API")

    def create(self, request):
        # Find repeated catalogues_filter entries in form data:
        forward_data = request.data.copy()
        if 'catalogues_filter' in forward_data:
            forward_data['catalogues_filter'] = request.POST.getlist('catalogues_filter')

        try:
            response = requests.post(settings.GENOME_SEARCH_PROXY, data=forward_data)
        except requests.exceptions.RequestException:
            logger.error(f'Failed to talk to genome search backend at {settings.GENOME_SEARCH_PROXY}')
            raise Http404('Genome search failed. Please try later.')
        try:
            response = response.json()
        except (JSONDecodeError, ValueError):
            logging.error(f'Failed to decode JSON from genome search backend')
            logging.error(response.text)
            raise Http404('Genome search failed. Please try later.')

        results = response.get('results', [])
        logger.info(f'Got {len(results)} search results')

        genomes = emg_models.Genome.objects.filter(
            accession__in=map(lambda result: result.get('genome'), results)
        ).all()

        matches = {
            result['genome']: result
            for result in results
        }
        logger.debug(matches)

        annotated_results = []
        for genome in genomes:
            if not genome.accession in matches:
                continue
            mgnify_data = emg_serializers.GenomeSerializer(genome, context={'request': request})
            annotated_results.append({'mgnify': mgnify_data.data, 'cobs': matches[genome.accession]})
        response['results'] = sorted(
            annotated_results,
            key=lambda result: result.get('cobs', {}).get('percent_kmers_found', 0),
            reverse=True
        )
        return Response(response)


class GenomeSearchGatherViewSet(viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeUploadSearchSerializer
    permission_classes = [AllowAny]
    parser_classes = [FormParser, MultiPartParser]

    def list(self, request):
        return Response("You need to use the POST method to submit a sourmash job")

    def create(self, request):
        names = {}
        mag_catalogues = set(request.POST.getlist('mag_catalogues', []))

        if not mag_catalogues:
            raise Exception("A list of mag_catalogues to search against must be provided")

        catalogue_choices = dict(emg_serializers.get_mag_catalogue_choices())

        bad_catalogues = mag_catalogues.difference(catalogue_choices.keys())

        if bad_catalogues:
            raise Exception(
                f"The provided mag_catalogues are not valid. "
                f"Available: {catalogue_choices.keys()}; "
                f"Unavailable: {bad_catalogues}"
            )

        for file_uploaded in request.FILES.getlist('file_uploaded'):
            try:
                validate_sourmash_signature(
                    file_uploaded.file.read().decode('utf-8')
                )
            except Exception:
                raise Exception("Unable to parse the uploaded file")

            names[file_uploaded.name] = save_signature(file_uploaded)
        job_id, children_ids = send_sourmash_jobs(names, mag_catalogues)
        response = {
            "message": "Your files {} were successfully uploaded. "
                       "Use the given URL to check the status of the new job".format(",".join(names.keys())),
            "job_id": job_id,
            "children_ids": children_ids,
            "signatures_received": names.keys(),
            "status_URL": reverse('genomes-status', args=[job_id], request=request)
        }
        return Response(response)


class GenomeSearchStatusView(APIView):

    def get(self, request, job_id):
        response = get_sourmash_job_status(job_id, request)
        if response is None:
            raise Http404()
        return Response(response)


class GenomeSearchResultsView(APIView):

    def get(self, request, job_id):
        file, content_type = get_result_file(job_id)
        if file is None:
            raise Http404()
        if content_type == 'text/csv':
            return HttpResponse(file, headers={
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename={job_id}.csv',
            })
        if content_type == 'application/gzip':
            return HttpResponse(file, headers={
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename={job_id}.tgz',
            })
        return None


class GenomeDownloadViewSet(emg_mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeDownloadSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'alias',
    )

    ordering = ('alias',)

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        try:
            accession = self.kwargs['accession']
        except ValueError:
            raise Http404()
        return emg_models.GenomeDownload.objects.available(self.request) \
            .filter(genome__accession=accession)

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias'])
        )

    def get_serializer_class(self):
        return super(GenomeDownloadViewSet, self) \
            .get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of genome downloads
        Example:
        ---
        `/biomes`
        """
        return super(GenomeDownloadViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, accession, alias,
                 *args, **kwargs):
        obj = self.get_object()
        if obj.subdir is not None:
            file_path = '{0}/{1}/{2}'.format(
                obj.genome.result_directory, obj.subdir, obj.realname
            )
        else:
            file_path = '{0}/{1}'.format(
                obj.genome.result_directory, obj.realname
            )
        return emg_utils.prepare_results_file_download_response(file_path, alias)


class GenomeSetViewSet(mixins.RetrieveModelMixin,
                       emg_mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeSetSerializer
    queryset = emg_models.GenomeSet.objects.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
    )

    ordering = ('-name',)

    lookup_field = 'name'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        genome_set = emg_models.GenomeSet.objects.all()

        if self.kwargs.get('name'):
            genome_set = genome_set.filter(name=self.kwargs['name'])

        genome_set.annotate(genome_count=Count('genome'))
        return genome_set

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.GenomeSetSerializer
        return super(GenomeSetViewSet, self).get_serializer_class()


class GenomeCatalogueDownloadViewSet(emg_mixins.ListModelMixin,
                                     viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeCatalogueDownloadSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'alias',
    )

    ordering = ('alias',)

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        try:
            genome_catalogue = self.kwargs['catalogue_id']
        except ValueError:
            raise Http404()
        return emg_models.GenomeCatalogueDownload.objects \
            .filter(genome_catalogue__catalogue_id=genome_catalogue)

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias'])
        )

    def get_serializer_class(self):
        return super(GenomeCatalogueDownloadViewSet, self) \
            .get_serializer_class()

    def list(self, request, *args, **kwargs):
        return super(GenomeCatalogueDownloadViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, catalogue_id, alias,
                 *args, **kwargs):
        """
        Retrieves a downloadable file for the genome catalogue
        Example:
        ---
        `
        /genome-catalogues/hgut-v1-0/downloads/phylo_tree.json`
        """
        obj = self.get_object()
        if obj.subdir is not None:
            file_path = '{0}/{1}/{2}'.format(
                obj.genome_catalogue.result_directory, obj.subdir, obj.realname
            )
        else:
            file_path = '{0}/{1}'.format(
                obj.genome_catalogue.result_directory, obj.realname
            )
        return emg_utils.prepare_results_file_download_response(file_path, alias)


class CogCatViewSet(mixins.RetrieveModelMixin,
                    emg_mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = emg_serializers.CogCatSerializer
    queryset = emg_models.CogCat.objects.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
    )

    ordering = ('-name',)


class KeggModuleViewSet(mixins.RetrieveModelMixin,
                        emg_mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = emg_serializers.KeggModuleSerializer
    queryset = emg_models.KeggModule.objects.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
    )

    ordering = ('-name',)


class KeggClassViewSet(mixins.RetrieveModelMixin,
                       emg_mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = emg_serializers.KeggClassSerializer
    queryset = emg_models.KeggClass.objects.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
    )

    ordering = ('-name',)


class AntiSmashGeneClustersViewSet(mixins.RetrieveModelMixin,
                                   emg_mixins.ListModelMixin,
                                   viewsets.GenericViewSet):
    serializer_class = emg_serializers.AntiSmashGCSerializer
    queryset = emg_models.AntiSmashGC.objects.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
    )

    ordering = ('-name',)


class BannerMessageView(APIView):

    def get(self, request):
        """Get the content of the banner message if any
        """
        message = ""
        if settings.BANNER_MESSAGE_FILE and os.path.isfile(settings.BANNER_MESSAGE_FILE):
            with open(settings.BANNER_MESSAGE_FILE, 'r') as msg_file:
                message = msg_file.read().strip()
        return Response({"message": message})


class EBISearchCSVDownload(APIView):
    """Download an EBI Search query
    """

    def get(self, request, domain):
        """Stream the CSV from EBI Search
        """
        page_size = 100

        if "total" not in request.GET:
            return HttpResponseBadRequest(
                content="Missing 'total' pages params.",
                status=status.HTTP_400_BAD_REQUEST
            )
        total = int(request.GET.get("total"))
        total_pages = math.ceil(total / page_size)
        fields = request.GET.get("fields", "").split(",")
        base = settings.EBI_SEARCH_URL + domain

        csv_buffer = Echo()
        csv_writer = csv.writer(csv_buffer)

        query = {
            "format": "json",
            "fields": request.GET.get("fields", ""),
            "query": request.GET.get("query", ""),
            "facets": request.GET.get("facets", "")
        }

        def get_data():
            # header
            yield fields
            for page in range(total_pages + 1):
                query["size"] = page_size
                start = page * page_size
                if start >= total:
                    return
                query["start"] = start
                response = requests.get(base, params=query)
                if not response.ok:
                    raise Exception("There was an error downloading the data from EBI Search" +
                                    "Status Code: " + str(response.status_code) +
                                    " Content: " +
                                    response.content)
                else:
                    data = response.json()
                    for entry in data.get("entries"):
                        yield emg_utils.parse_ebi_search_entry(entry, fields)

        stream_res = StreamingHttpResponse((csv_writer.writerow(row) for row in get_data()),
                                           content_type="text/csv")
        stream_res["Content-Disposition"] = "attachment; filename=search_download.csv"
        return stream_res


class BiomePrediction(APIView):

    def get(self, request):
        url = settings.BIOME_PREDICTION_URL
        response = requests.get(url, params={"text": request.GET.get("text", "")})
        if not response.ok:
            raise Exception("Error with the biome prediction API." +
                            "Status Code: " + str(response.status_code))
        predicted_biomes = response.json()
        biomes_results = []
        for hit in predicted_biomes:
            try:
                biome = emg_models.Biome.objects.get(lineage=hit.get("biome"))
                biomes_results.append({
                    "biome_id": biome.pk,
                    "lineage": biome.lineage,
                    "score": hit.get("score")
                })
            except emg_models.Biome.DoesNotExist:
                logger.error("Biome prediction match is not a valid: " + str(hit))
                pass
        return Response(biomes_results)

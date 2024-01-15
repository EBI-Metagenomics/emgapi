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

import logging

from rest_framework import viewsets
from rest_framework import filters

from django_filters.rest_framework import DjangoFilterBackend

from . import serializers as emg_serializers
from . import filters as emg_filters

logger = logging.getLogger(__name__)


# Base classes
class BaseSuperStudyViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.SuperStudySerializer

    filterset_class = emg_filters.SuperStudyFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('super_study_id'),
    )

    ordering_fields = (
        'super_study_id',
        'title'
    )

    ordering = ('super_study_id',)

    search_fields = (
        '@title',
        '@description',
        'url_slug'
    )


class BaseStudyGenericViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudySerializer

    filterset_class = emg_filters.StudyFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('study_id'),
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
        'study_id',
        'secondary_accession',
        'project_id',
        'centre_name',
    )


class BaseSampleGenericViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.SampleSerializer

    filterset_class = emg_filters.SampleFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('accession'),
    )

    ordering_fields = (
        'accession',
        'sample_name',
        'last_update',
    )

    ordering = ('-last_update',)

    search_fields = (
        'accession',
        'primary_accession',
        '@sample_name',
        '@sample_desc',
        'sample_alias',
        'species',
        'environment_feature',
        'environment_biome',
        'environment_feature',
        'environment_material',
        '@metadata__var_val_ucv',
    )


class BaseRunGenericViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.RunSerializer

    filterset_class = emg_filters.RunFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('run_id'),
    )

    ordering_fields = (
        'accession',
    )

    ordering = ('-accession',)

    search_fields = (
        'accession',
        'secondary_accession',
        'instrument_platform',
        'instrument_model',
        'experiment_type__experiment_type',
        '@sample__metadata__var_val_ucv',
    )


class BaseAssemblyGenericViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.AssemblySerializer

    filterset_class = emg_filters.AssemblyFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('assembly_id'),
    )

    ordering_fields = (
        'accession',
    )

    ordering = ('-accession',)

    search_fields = (
        'accession',
        'wgs_accession',
        'legacy_accession',
        '@samples__metadata__var_val_ucv',
    )


class BaseAnalysisGenericViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    filterset_class = emg_filters.AnalysisJobFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('job_id'),
    )

    ordering_fields = (
        ('job_id', 'accession'),
        'pipeline',
        'run__accession',
        'sample__accession',
        'pipeline__release_version',
        'experiment_type__experiment_type',
    )
    ordering = ('-pipeline_id',)

    search_fields = (
        'job_id',
        'instrument_platform',
        'instrument_model',
        'run__accession',
        'sample__accession',
        'pipeline__release_version',
        'experiment_type__experiment_type',
    )


class BasePublicationGenericViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.PublicationSerializer

    filterset_class = emg_filters.PublicationFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('pubmed_id'),
    )

    ordering_fields = (
        'pubmed_id',
        'published_year',
        'studies_count',
    )

    ordering = ('-pubmed_id',)

    search_fields = (
        '@pub_title',
        '@pub_abstract',
        'pub_type',
        'authors',
        'doi',
        'isbn',
        'pubmed_id',
        'published_year',
    )


class BaseGenomeGenericViewSet(viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeSerializer

    filter_backends = (
        filters.SearchFilter,
        emg_filters.getUnambiguousOrderingFilterByField('accession'),
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

    ordering = ('accession',)

    search_fields = (
        'accession',
    )


class BaseGenomeCatalogueGenericViewSet(viewsets.GenericViewSet):
    serializer_class = emg_serializers.GenomeCatalogueSerializer

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
        emg_filters.getUnambiguousOrderingFilterByField('catalogue_id'),
    )

    ordering_fields = (
        'catalogue_id',
        'name',
        'last_update',
        'genome_count',
        'unclustered_genome_count',
    )

    ordering = ('catalogue_id',)

    search_fields = (
        'catalogue_id',
        'name',
        'biome__biome_name',
    )
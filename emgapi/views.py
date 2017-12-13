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

import logging

from django.conf import settings
from django.db.models import Q
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.http import Http404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.response import Response

from rest_framework import filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route, list_route
# from rest_framework import authentication
from rest_framework import permissions

from . import models as emg_models
from . import serializers as emg_serializers
from . import filters as emg_filters
from . import mixins as emg_mixins
from . import permissions as emg_perms
from . import viewsets as emg_viewsets

logger = logging.getLogger(__name__)


class MyDataViewSet(emg_mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudySerializer
    permission_classes = (
        permissions.IsAuthenticated,
        emg_perms.IsSelf,
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
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    search_fields = (
        'biome_name',
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

    @list_route(
        methods=['get', ],
        serializer_class=emg_serializers.Top10BiomeSerializer
    )
    def top10(self, request):
        """
        Retrieve 10 most popular biomes
        ---
        `/biomes/top10`
        """

        sql = """
        SELECT
            parent.BIOME_ID,
            COUNT(distinct sample.SAMPLE_ID) as samples_count
        FROM BIOME_HIERARCHY_TREE AS node,
            BIOME_HIERARCHY_TREE AS parent,
            SAMPLE as sample
        WHERE node.lft BETWEEN parent.lft AND parent.rgt
            AND node.BIOME_ID = sample.BIOME_ID
            AND sample.IS_PUBLIC = 1
            AND parent.DEPTH > 2
        GROUP BY parent.BIOME_ID
        ORDER BY 2 DESC
        LIMIT 10;
        """

        res = emg_models.Biome.objects.raw(sql)
        biomes = {b.biome_id: b.samples_count for b in res}
        queryset = emg_models.Biome.objects.filter(
            biome_id__in=list(biomes))
        queryset = self.filter_queryset(queryset)
        for q in queryset:
            q.samples_count = biomes[q.biome_id]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudyViewSet(mixins.RetrieveModelMixin,
                   emg_mixins.ListModelMixin,
                   emg_viewsets.BaseStudyGenericViewSet):

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_queryset(self):
        queryset = emg_models.Study.objects.available(self.request)
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request, prefetch=True)
            queryset = queryset.prefetch_related(
                Prefetch('samples', queryset=_qs)
            )
        return queryset

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            Q(accession=self.kwargs['accession']) |
            Q(project_id=self.kwargs['accession'])
        )

    def get_serializer_class(self):
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
        retrieve only selected fileds

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

    @list_route(
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
        queryset = emg_models.Study.objects \
            .recent(self.request)[:limit]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=['get', ],
        url_name='publications-list',
        serializer_class=emg_serializers.PublicationSerializer
    )
    def publications(self, request, accession=None):
        """
        Retrieves list of publications for the given study accession
        Example:
        ---
        `/studies/SRP000183/publications` retrieve linked publications
        """

        obj = self.get_object()
        queryset = obj.publications.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @detail_route(
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


class SampleViewSet(mixins.RetrieveModelMixin,
                    emg_mixins.ListModelMixin,
                    emg_viewsets.BaseSampleGenericViewSet):

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9\-\_]+'

    def get_queryset(self):
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects \
                .available(self.request) \
                .select_related(
                    'analysis_status', 'experiment_type'
                )
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
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
        retrieve only selected fileds

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


class RunViewSet(mixins.RetrieveModelMixin,
                 emg_mixins.ListModelMixin,
                 emg_viewsets.BaseRunGenericViewSet):

    serializer_class = emg_serializers.RunSerializer

    filter_class = emg_filters.RunFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
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
        '@sample__metadata__var_val_ucv',
    )

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9_\-\,\s]+'

    def get_queryset(self):
        queryset = emg_models.Run.objects.available(self.request)
        return queryset

    def get_object(self):
        queryset = self.get_queryset() \
            .filter(
                Q(accession=self.kwargs['accession']) |
                Q(secondary_accession=self.kwargs['accession'])
            ).distinct().last()
        if queryset is None:
            raise Http404(
                ('No %s matches the given query.' %
                 emg_models.Run._meta.object_name)
            )
        return queryset

    def get_serializer_class(self):
        return super(RunViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs
        Example:
        ---
        `/runs`

        `/runs?fields[runs]=accession,experiment_type` retrieve only
        selected fileds

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


class AnalysisResultViewSet(emg_mixins.ListModelMixin,
                            viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    filter_class = emg_filters.AnalysisJobFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
    )

    ordering = ('-accession',)

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9_\-\,\s]+'

    def get_serializer_class(self):
        return super(AnalysisResultViewSet, self).get_serializer_class()

    def get_queryset(self):
        accession = self.kwargs['accession']
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(accession=accession)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession
        Example:
        ---
        `/runs/ERR1385375/analysis`
        """
        return super(AnalysisResultViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisViewSet(mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    lookup_field = 'release_version'
    lookup_value_regex = '[0-9.]+'

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(accession=self.kwargs['accession'])

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            Q(pipeline__release_version=self.kwargs['release_version']),
            Q(accession=self.kwargs['accession']) |
            Q(secondary_accession=self.kwargs['accession'])
        )

    def get_serializer_class(self):
        return super(AnalysisViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession and pipeline version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0`
        """
        return super(AnalysisViewSet, self).retrieve(request, *args, **kwargs)


class PipelineViewSet(mixins.RetrieveModelMixin,
                      emg_mixins.ListModelMixin,
                      viewsets.GenericViewSet):

    serializer_class = emg_serializers.PipelineSerializer
    queryset = emg_models.Pipeline.objects.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'release_version',
        'samples_count',
        'analysis_count',
    )

    ordering = ('release_version',)

    # search_fields = ()

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
    lookup_value_regex = '[a-zA-Z0-9\-\.]+'

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
    lookup_value_regex = '[a-zA-Z]+'

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
                         viewsets.GenericViewSet):

    serializer_class = emg_serializers.PublicationSerializer

    filter_class = emg_filters.PublicationFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'pubmed_id',
        'published_year',
        'studies_count',
    )

    ordering = ('pubmed_id',)

    search_fields = (
        '@pub_title',
        '@pub_abstract',
        'pub_type',
        'authors',
        'doi',
        'isbn',
    )

    lookup_field = 'pubmed_id'
    lookup_value_regex = '[0-9\.]+'

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

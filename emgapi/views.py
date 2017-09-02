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
import operator
from collections import OrderedDict

from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, mixins, generics
from rest_framework.response import Response

from rest_framework import filters
from rest_framework.decorators import detail_route, list_route
# from rest_framework import authentication
from rest_framework import permissions


from . import models as emg_models
from . import serializers as emg_serializers
from . import filters as emg_filters
from . import permissions as emg_perms
from . import mixins as emg_mixins

logger = logging.getLogger(__name__)


class MyDataViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudySerializer
    permission_classes = (
        permissions.IsAuthenticated,
        emg_perms.IsSelf,
    )

    def get_queryset(self):
        queryset = emg_models.Study.objects \
            .mydata(self.request) \
            .select_related('biome')
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
        queryset = emg_models.Study.objects \
            .mydata(self.request) \
            .select_related('biome')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BiomeViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):

    serializer_class = emg_serializers.BiomeSerializer

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    search_fields = (
        'lineage',
        'biome_name',
    )

    ordering_fields = (
        'lineage',
    )
    ordering = ('biome_id',)

    lookup_field = 'lineage'
    lookup_value_regex = '[a-zA-Z0-9\:\-\s\(\)\<\>]+'

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
        Retrieves top level Biome nodes.
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
        Retrieve 10 most popular biomes:
        ---
        `/biomes/top10`
        """

        sql = """
        SELECT parent.BIOME_ID, COUNT(distinct sample.STUDY_ID) as study_count
        FROM BIOME_HIERARCHY_TREE AS node,
            BIOME_HIERARCHY_TREE AS parent,
            SAMPLE as sample
        WHERE node.lft BETWEEN parent.lft AND parent.rgt
            AND node.BIOME_ID = sample.BIOME_ID
            AND parent.DEPTH > 1
            AND sample.IS_PUBLIC = 1
        GROUP BY parent.BIOME_ID
        ORDER BY 2 DESC
        LIMIT 10;"""

        res = emg_models.Biome.objects.raw(sql)
        biomes = {b.biome_id: b.study_count for b in res}
        biomes = OrderedDict(
            sorted(biomes.items(), key=operator.itemgetter(1), reverse=True))
        queryset = emg_models.Biome.objects.filter(
            biome_id__in=list(biomes))
        for q in queryset:
            q.study_count = biomes[q.biome_id]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudyViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudySerializer

    filter_class = emg_filters.StudyFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
        'last_update',
        'samples_count',
        'runs_count',
    )

    ordering = ('-last_update',)

    search_fields = (
        '@study_name',
        '@study_abstract',
        'centre_name',
        'author_name',
        'author_email',
        'project_id',
    )

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_queryset(self):
        queryset = emg_models.Study.objects \
            .available(self.request)
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request) \
                .select_related('biome')
            queryset = queryset.prefetch_related(
                Prefetch('samples', queryset=_qs))
        return queryset

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

        `/studies?fields[studies]=accession,samples_count,biomes`
        retrieve only selected fileds

        `/studies?include=samples` with samples

        Filter by:
        ---
        `/studies?biome=root:Environmental:Terrestrial:Soil`

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
        `/studies/ERP009004` retrieve study SRP001634

        `/studies/ERP009004?include=samples`
        with samples
        """
        return super(StudyViewSet, self).retrieve(request, *args, **kwargs)

    @list_route(
        methods=['get', ],
        serializer_class=emg_serializers.StudySerializer
    )
    def recent(self, request):
        """
        Retrieve 20 latest studies
        Example:
        ---
        `/studies/recent` retrieve recent studies
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
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    serializer_class = emg_serializers.SampleSerializer

    filter_class = emg_filters.SampleFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
        'last_update',
        'runs_count',
    )

    ordering = ('-last_update',)

    search_fields = (
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

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9\-\_]+'

    def get_queryset(self):
        queryset = emg_models.Sample.objects \
            .available(self.request) \
            .prefetch_related('biome', 'study')
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects \
                .available(self.request) \
                .select_related(
                    'analysis_status', 'experiment_type'
                )
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        if 'study' in self.request.GET.get('include', '').split(','):
            queryset = queryset.select_related('study__biome')
        return queryset

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

        `/samples/ERS1015417?include=metadata` with metadata

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

        `/samples?include=metadata,runs,study`
        with related metadata, runs and studies

        `/samples?ordering=accession` ordered by accession

        Filter by:
        ---
        `/samples?experiment_type=metagenomics`

        `/samples?species=sapiens`

        `/samples?biome=root:Environmental:Aquatic:Marine`

        Search for:
        ---
        name, descriptions, metadata, species, environment feature and material

        `/samples?search=continuous%20culture`

        """
        return super(SampleViewSet, self).list(request, *args, **kwargs)


class RunAPIView(emg_mixins.MultipleFieldLookupMixin,
                 generics.RetrieveAPIView):

    serializer_class = emg_serializers.RetrieveRunSerializer

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request) \
            .select_related(
                'sample',
                'pipeline',
                'analysis_status',
            )

    def get(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves run for the given accession and pipeline version
        Example:
        ---
        `/runs/ERR1385375/3.0`
        """
        run = get_object_or_404(
            emg_models.AnalysisJob, accession=accession,
            pipeline__release_version=release_version)
        serializer = self.get_serializer(run)
        return Response(data=serializer.data)


class RunViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):

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
        'instrument_platform',
        'instrument_model',
        '@sample__metadata__var_val_ucv',
    )

    lookup_field = 'accession'

    def get_queryset(self):
        queryset = emg_models.Run.objects \
            .available(self.request) \
            .prefetch_related(
                'analysis_status',
                'experiment_type',
            )
        _qs = emg_models.Sample.objects.available(self.request) \
            .select_related('biome')
        __qs = emg_models.Study.objects.available(self.request) \
            .select_related('biome')
        _qs = _qs.prefetch_related(Prefetch('study', queryset=__qs))
        queryset = queryset.prefetch_related(
            Prefetch('sample', queryset=_qs))
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
        `/runs?experiment_type=metagenomics`

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
        run = emg_models.Run.objects \
            .filter(accession=self.kwargs['accession']) \
            .distinct().last()
        serializer = self.get_serializer(run, context={'request': request})
        return Response(serializer.data)

    @detail_route(
        methods=['get', ],
        url_name='pipelines-list',
        serializer_class=emg_serializers.RetrieveRunSerializer
    )
    def analysis(self, request, accession=None):
        """
        Retrieves list of analysis for the given run
        Example:
        ---
        `/runs/ERR1385375/analysis`
        """
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(accession=accession) \
            .select_related(
                'sample',
                'pipeline',
                'analysis_status',
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)


class PipelineViewSet(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):

    """
    Pipelines endpoint provides detail about each pipeline version were used
    to analyse the data.
    """

    serializer_class = emg_serializers.PipelineSerializer
    queryset = emg_models.Pipeline.objects.all()

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'release_version',
    )

    ordering = ('release_version',)

    # search_fields = ()

    lookup_field = 'release_version'
    lookup_value_regex = '[a-zA-Z0-9.]+'

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


class PipelineToolInstanceView(emg_mixins.MultipleFieldLookupMixin,
                               generics.RetrieveAPIView):

    """
    Pipeline tools endpoint provides detail about the pipeline tools were used
    to analyse the data in each steps.
    """

    serializer_class = emg_serializers.PipelineToolSerializer
    queryset = emg_models.PipelineTool.objects.all()

    lookup_fields = ('tool_name', 'version')

    def get(self, request, tool_name, version, *args, **kwargs):
        """
        Retrieves pipeline tool details for the given pipeline version
        Example:
        ---
        `/pipeline-tools/interproscan/5.19-58.0`
        """
        obj = get_object_or_404(
            emg_models.PipelineTool,
            tool_name__iexact=tool_name, version=version)
        serializer = self.get_serializer(obj)
        return Response(data=serializer.data)


class PipelineToolViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):

    """
    Pipeline tools endpoint provides detail about the pipeline tools were used
    to analyse the data in each steps.
    """

    serializer_class = emg_serializers.PipelineToolSerializer
    queryset = emg_models.PipelineTool.objects.all()

    # lookup_field = 'tool_name'
    # lookup_value_regex = '[0-9a-zA-Z\-\.]+'

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


class ExperimentTypeViewSet(mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):

    """
    Experiment types endpoint provides access to the metagenomic studies
    filteres by various type of experiments. Studies or samples can be
    filtered by many attributes including metadata.
    """

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
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):

    """
    Publications endpoint provides access to the publications linked to
    metagenomic studies. Publications can be filtered by year or searched by:
    title, abstract, authors, DOI, ISBN. Single publication is retrieved by
    PUBMED ID.
    """

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
                .available(self.request) \
                .select_related('biome')
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

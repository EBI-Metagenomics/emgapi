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
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, mixins, generics
from rest_framework.response import Response

from rest_framework import filters
from rest_framework.decorators import detail_route, list_route
# from rest_framework import authentication
from rest_framework import permissions
# from rest_framework_json_api.renderers import JSONRenderer

from emg_api import models as emg_models
from emg_api import serializers as emg_serializers
from emg_api import filters as emg_filters
from emg_api import permissions as emg_perms

logger = logging.getLogger(__name__)


class MultipleFieldLookupMixin(object):

    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field
    filtering.
    Source: http://www.django-rest-framework.org/api-guide/generic-views/
    """

    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]:
                filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)


class MyDataViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudySerializer
    permission_classes = (
        permissions.IsAuthenticated,
        emg_perms.IsSelf,
    )

    def get_serializer_class(self):
        return super(MyDataViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieve studies owned by the logged in user
        Example:
        ---
        `/api/mydata` retrieve own studies
        """
        queryset = emg_models.Study.objects \
            .mydata(self.request) \
            .prefetch_related('biome')
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
    queryset = emg_models.Biome.objects.all()

    filter_backends = (
        # DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'studies_count',
        'samples_count',
        'runs_count',
    )
    ordering = ('-studies_count',)

    search_fields = (
        '@biome_name',
        '@lineage',
    )

    lookup_field = 'lineage'
    lookup_value_regex = '[a-zA-Z0-9\:\-\s\(\)\<\>]+'

    def get_queryset(self):
        return emg_models.Biome.objects.all() \
            .annotate(studies_count=Count('studies')) \
            .annotate(samples_count=Count('studies__samples')) \
            .annotate(runs_count=Count('studies__samples__runs'))

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.BiomeSerializer
        return super(BiomeViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of biomes
        Example:
        ---
        `/api/biomes`

        `/api/biomes?search=soil` search for Soil
        """

        return super(BiomeViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves biome for the given identifier
        Example:
        ---
        `/api/biomes/root:Environmental:Terrestrial:Soil`
        """

        return super(BiomeViewSet, self).retrieve(request, *args, **kwargs)

    @list_route(
        methods=['get', ],
        serializer_class=emg_serializers.BiomeSerializer
    )
    def top10(self, request):
        """
        Retrieve top 10 biomes sorted by number of studies
        Example:
        ---
        `/api/biomes/top10` retrieve top 10 biomes
        """
        limit = settings.EMG_DEFAULT_LIMIT
        queryset = emg_models.Biome.objects.top10()[:limit]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=['get', ],
        url_name='samples-list',
        serializer_class=emg_serializers.SampleSerializer
    )
    def samples(self, request, lineage=None):
        """
        Retrieves list of samples for the given biome
        Example:
        ---
        `/api/biomes/root:Environmental:Terrestrial:Soil/samples
        retrieve` linked samples
        """

        queryset = self.get_object().samples \
            .available(self.request) \
            .select_related('biome')
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
        url_name='studies-list',
        serializer_class=emg_serializers.SimpleStudySerializer
    )
    def studies(self, request, lineage=None):
        """
        Retrieves list of studies for the given biome
        Example:
        ---
        `/api/biomes/root:Environmental:Terrestrial:Soil/studies`
        retrieve linked studies
        """

        queryset = self.get_object().studies \
            .available(self.request) \
            .select_related('biome')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)


class StudyViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):

    serializer_class = emg_serializers.SimpleStudySerializer

    filter_class = emg_filters.StudyFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
        'last_update',
    )

    ordering = ('-last_update',)

    search_fields = (
        # 'study_id',
        'accession',
        '@study_name',
        '@study_abstract',
        'centre_name',
        'author_name',
        'author_email',
        '@biome__biome_name',
        '@biome__lineage',
    )

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9,]+'

    def get_queryset(self):
        queryset = emg_models.Study.objects \
            .available(self.request) \
            .select_related('biome')
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request) \
                .select_related('biome')
            queryset = queryset.prefetch_related(
                Prefetch('samples', queryset=_qs))
        if 'publications' in self.request.GET.get('include', '').split(','):
            queryset = queryset.prefetch_related(
                Prefetch(
                    'publications',
                    queryset=emg_models.Publication.objects.all()))
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.StudySerializer
        return super(StudyViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of studies
        Example:
        ---
        `/api/studies`

        `/api/studies?include=samples` with samples

        Filter by:
        ---
        `/api/studies?biome=root:Environmental:Terrestrial:Soil`
        retrieve all studies for given Biome

        `/api/studies?biome_name=Soil`
        retrieve all studies containing given Biome

        Search:
        ---
        `/api/studies?search=microbial%20fuel%20cells`
        """

        return super(StudyViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves study for the given accession
        Example:
        ---
        `/api/studies/ERP008945` retrieve study ERP008945

        `/api/studies/ERP008945?include=samples,publications`
        with samples and publications
        """
        return super(StudyViewSet, self).retrieve(request, *args, **kwargs)

    @list_route(
        methods=['get', ],
        serializer_class=emg_serializers.SimpleStudySerializer
    )
    def recent(self, request):
        """
        Retrieve latest studies
        Example:
        ---
        `/api/studies/latest` retrieve latest studies
        """
        limit = settings.EMG_DEFAULT_LIMIT
        queryset = emg_models.Study.objects \
            .recent(self.request) \
            .select_related('biome')[:limit]
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
        # url_path='publications(?:/(?P<publications_id>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.SimplePublicationSerializer
    )
    def publications(self, request, accession=None, publications_id=None):
        """
        Retrieves list of publications for the given study accession
        Example:
        ---
        `/api/studies/ERP008945/publications` retrieve linked publications
        """

        obj = self.get_object()
        if publications_id is not None:
            queryset = obj.publications \
                .filter(publications_id=publications_id)
        else:
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
        url_name='samples-list',
        # url_path='samples(?:/(?P<sample_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.SimpleSampleSerializer
    )
    def samples(self, request, accession=None, sample_accession=None):
        """
        Retrieves list of samples for the given study accession
        Example:
        ---
        `/api/studies/ERP008945/samples` retrieve linked samples

        `/api/studies/ERP008945/samples?include=runs` with runs
        """

        obj = self.get_object()
        queryset = obj.samples \
            .available(self.request)
        if sample_accession is not None:
            queryset = queryset \
                .filter(accession=sample_accession) \
                .select_related('biome')
        else:
            queryset = queryset \
                .select_related('biome')
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects \
                .available(self.request) \
                .select_related(
                    'analysis_status', 'pipeline', 'experiment_type'
                )
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
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

    serializer_class = emg_serializers.SimpleSampleSerializer

    filter_class = emg_filters.SampleFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
        'last_update',
    )

    ordering = ('-last_update',)

    search_fields = (
        # 'sample_id',
        'accession',
        '@sample_name',
        '@biome__biome_name',
        '@biome__lineage',
    )

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9,]+'

    def get_queryset(self):
        queryset = emg_models.Sample.objects \
            .available(self.request) \
            .prefetch_related('biome', 'study')
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects \
                .available(self.request) \
                .select_related(
                    'analysis_status', 'pipeline', 'experiment_type'
                )
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        if 'study' in self.request.GET.get('include', '').split(','):
            queryset = queryset.select_related('study__biome')
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.SampleSerializer
        return super(SampleViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves sample for the given accession
        Example:
        ---
        `/api/sammples/accession`

        `/api/sammples/accession?include=runs` with related runs

        """
        return super(SampleViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples
        Example:
        ---
        `/api/samples` retrieves list of samples

        `/api/samples?include=runs,study` with related runs and studies

        `/api/samples?ordering=accession` ordered by accession

        Filter by:
        ---
        `/api/samples?experiment_type=metagenomics`

        `/api/samples?pipeline_version=3.0`

        `/api/samples?biome=root:Environmental:Aquatic:Marine`

        Search for accession, name, biome, etc.:
        ---
        `/api/samples?search=text`
        """
        return super(SampleViewSet, self).list(request, *args, **kwargs)

    @detail_route(
        methods=['get', ],
        url_name='runs-list',
        # url_path='runs(?:/(?P<run_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.RunSerializer
    )
    def runs(self, request, accession=None, run_accession=None):
        """
        Retrieves list of runs for the given sample accession
        Example:
        ---
        `/api/samples/accession/runs`

        `/api/sample/saccession/runs?include=run,study`
        with related runs and studies

        Filter by:
        ---
        `/api/samples/accession/runs?experiment_type=metagenomics`

        `/api/samples/accession/runs?pipeline_version=3.0`

        `/api/samples/accession/runs?biome=root:Environmental:Aquatic:Marine`
        """

        obj = self.get_object()
        if run_accession is not None:
            queryset = obj.runs \
                .available(self.request) \
                .filter(accession=run_accession) \
                .select_related(
                    'sample',
                    'analysis_status',
                    'experiment_type',
                    'pipeline'
                )
        else:
            queryset = obj.runs \
                .available(self.request) \
                .select_related(
                    'sample',
                    'analysis_status',
                    'experiment_type',
                    'pipeline'
                )
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
        url_name='metadata-list',
        serializer_class=emg_serializers.SimpleSampleAnnSerializer
    )
    def metadata(self, request, accession=None):
        """
        Retrieves list of samples for the given study accession
        Example:
        ---
        `/api/samples/accession/metadata` retrieve metadata
        """

        obj = self.get_object()
        queryset = obj.metadata.all() \
            .select_related('sample', 'var') \
            .order_by('var')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)


class SampleAnnAPIView(MultipleFieldLookupMixin, generics.RetrieveAPIView):

    serializer_class = emg_serializers.SampleAnnSerializer

    lookup_fields = ('sample', 'name')

    def get_queryset(self):
        return emg_models.SampleAnn.objects.all()

    def get(self, request, sample_accession, name, *args, **kwargs):
        """
        Retrieves sample annotation for the given sample accession and value
        Example:
        ---
        `/api/metadata/sample_accession/value`
        """
        sa = emg_models.SampleAnn.objects.get(
            sample__accession=sample_accession,
            var__var_name=name)
        serializer = self.get_serializer(sa)
        return Response(data=serializer.data)


class SampleAnnsViewSet(MultipleFieldLookupMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):

    serializer_class = emg_serializers.SimpleSampleAnnSerializer

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'sample',
        'var',
    )

    ordering = (
        'sample',
        'var',
    )

    search_fields = (
        'var__var_name',
    )

    def get_queryset(self):
        queryset = emg_models.SampleAnn.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.SampleAnnSerializer
        return super(SampleAnnsViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of annotaitons
        Example:
        ---
        `/api/metadata` retrieves list of samples
        """
        return super(SampleAnnsViewSet, self).list(request, *args, **kwargs)


class RunAPIView(MultipleFieldLookupMixin, generics.RetrieveAPIView):

    serializer_class = emg_serializers.RunSerializer

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.Run.objects \
            .available(self.request) \
            .select_related(
                'sample',
                'pipeline',
                'analysis_status',
                'experiment_type'
            )

    def get(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves run for the given accession
        Example:
        ---
        `/api/runs/ERR1385375/3.0`

        `/api/runs/ERR1385375/3.0?include=sample` with related sample
        """
        run = emg_models.Run.objects.get(
            accession=accession, pipeline__release_version=release_version)
        serializer = self.get_serializer(run)
        return Response(data=serializer.data)


class RunViewSet(mixins.ListModelMixin,
                 viewsets.GenericViewSet):

    serializer_class = emg_serializers.SimpleRunSerializer

    filter_class = emg_filters.RunFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
    )

    ordering = ('accession',)

    search_fields = (
        'accession',
    )

    def get_queryset(self):
        return emg_models.Run.objects \
            .available(self.request) \
            .select_related(
                'sample',
                'pipeline',
                'analysis_status',
                'experiment_type'
            )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.RunSerializer
        return super(RunViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs
        Example:
        ---
        `/api/runs`

        `/api/runs?include=run,study` with related runs and studies

        Filter by:
        ---
        `/api/runs?experiment_type=metagenomics`

        `/api/runs?pipeline_version=3.0`

        `/api/runs?biome=root:Environmental:Aquatic:Marine`
        """
        return super(RunViewSet, self).list(request, *args, **kwargs)


class PipelineViewSet(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):

    serializer_class = emg_serializers.PipelineSerializer
    queryset = emg_models.Pipeline.objects.all()

    filter_class = emg_filters.PipelineFilter

    filter_backends = (
        DjangoFilterBackend,
        # filters.SearchFilter,
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
        """
        return super(PipelineViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of pipeline versions
        """
        return super(PipelineViewSet, self).list(request, *args, **kwargs)

    @detail_route(
        methods=['get', ],
        url_name='runs-list',
        # url_path='runs(?:/(?P<run_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.RunSerializer
    )
    def runs(self, request, release_version=None, run_accession=None):
        """
        Retrieves list of runs for the given pipeline version
        """

        obj = self.get_object()
        if run_accession is not None:
            queryset = obj.runs \
                .available(self.request) \
                .filter(accession=run_accession) \
                .select_related(
                    'sample',
                    'analysis_status',
                    'experiment_type',
                    'pipeline'
                )
        else:
            queryset = obj.runs \
                .available(self.request) \
                .select_related(
                    'sample',
                    'analysis_status',
                    'experiment_type',
                    'pipeline'
                )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)


class ExperimentTypeViewSet(mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):

    serializer_class = emg_serializers.ExperimentTypeSerializer
    queryset = emg_models.ExperimentType.objects.all()

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'experiment_type',
    )

    ordering = ('experiment_type',)

    search_fields = (
        'experiment_type',
    )

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

    @detail_route(
        methods=['get', ],
        url_name='runs-list',
        # url_path='runs(?:/(?P<run_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.SimpleRunSerializer
    )
    def runs(self, request, experiment_type=None, run_accession=None):
        """
        Retrieves list of runs for the given experiment type
        """

        obj = self.get_object()
        if run_accession is not None:
            queryset = obj.runs \
                .available(self.request) \
                .filter(accession=run_accession) \
                .select_related(
                    'sample',
                    'pipeline',
                    'analysis_status',
                    'experiment_type'
                )
        else:
            queryset = obj.runs \
                .available(self.request) \
                .select_related(
                    'sample',
                    'pipeline',
                    'analysis_status',
                    'experiment_type'
                )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)


class PublicationViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):

    serializer_class = emg_serializers.SimplePublicationSerializer

    filter_class = emg_filters.PublicationFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = ('pub_id',)

    ordering = ('pub_id',)

    search_fields = (
        '@pub_title',
        '@pub_abstract',
        'pub_type',
        'authors',
        'doi',
        'isbn',
    )

    lookup_field = 'pub_id'
    lookup_value_regex = '[a-zA-Z0-9,]+'

    def get_queryset(self):
        queryset = emg_models.Publication.objects.all()
        if 'studies' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.select_related('biome')
            queryset = queryset.prefetch_related(
                Prefetch('studies', queryset=_qs))
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.PublicationSerializer
        return super(PublicationViewSet, self).get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves publication for the given id
        Example:
        ---
        `/api/publications/pub_id`

        `/api/publications/pub_id?include=studies` with studies
        """
        return super(PublicationViewSet, self) \
            .retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of publications
        Example:
        ---
        `/api/publications` retrieves list of publications

        `/api/publications?include=studies` with studies

        `/api/publications?ordering=pub_id` ordered by id

        Search for title, abstract, authors, etc.:
        ---
        `/api/publications?search=text`
        """
        return super(PublicationViewSet, self).list(request, *args, **kwargs)

    @detail_route(
        methods=['get', ],
        url_name='studies-list',
        # url_path='studies(?:/(?P<study_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.SimpleStudySerializer
    )
    def studies(self, request, pub_id=None, study_accession=None):
        """
        Retrieves list of studies for the given publication
        Example:
        ---
        `/api/publications/id/studies`

        Filter by:
        ---
        `/api/publications/id/studies?data_origination=harvested`
        """

        obj = self.get_object()
        queryset = obj.studies \
            .available(self.request) \
            .select_related('biome')
        if study_accession is not None:
            queryset = queryset.filter(accession=study_accession)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)

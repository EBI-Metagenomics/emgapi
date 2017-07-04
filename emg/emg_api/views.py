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

from rest_framework import viewsets, mixins
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import detail_route
# from rest_framework.decorators import list_route

from emg_api import models as emg_models
from emg_api import serializers as emg_serializers
from emg_api import filters as emg_filters

logger = logging.getLogger(__name__)


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

    ordering_fields = ('biome_id',)
    ordering = ('biome_id',)

    search_fields = (
        '@biome_name',
        '@lineage',
    )

    lookup_field = 'biome_id'
    lookup_value_regex = '[a-zA-Z0-9,]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.BiomeSerializer
        return super(BiomeViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='samples-list',
        serializer_class=emg_serializers.SampleSerializer
    )
    def samples(self, request, biome_id=None):
        queryset = self.get_object().samples.public().select_related('biome')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=['get', ],
        url_name='studies-list',
        serializer_class=emg_serializers.SimpleStudySerializer
    )
    def studies(self, request, biome_id=None):
        queryset = self.get_object().studies.public().select_related('biome')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudyViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):

    serializer_class = emg_serializers.SimpleStudySerializer

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

    filter_fields = (
        'biome_id',
    )

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
        return emg_models.Study.objects.public() \
            .select_related('biome')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.StudySerializer
        return super(StudyViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='publications-list',
        url_path='publications(?:/(?P<publications_id>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.SimplePublicationSerializer
    )
    def publications(self, request, accession=None, publications_id=None):
        obj = self.get_object()
        if publications_id is not None:
            queryset = obj.publications \
                .filter(publications_id=publications_id)
        else:
            queryset = obj.publications.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=['get', ],
        url_name='samples-list',
        url_path='samples(?:/(?P<sample_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.SimpleSampleSerializer
    )
    def samples(self, request, accession=None, sample_accession=None):
        obj = self.get_object()
        if sample_accession is not None:
            queryset = obj.samples.public() \
                .filter(accession=sample_accession) \
                .select_related('biome')
        else:
            queryset = obj.samples \
                .public() \
                .select_related('biome')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
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
        return emg_models.Sample.objects.public() \
            .select_related('biome', 'study')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.SampleSerializer
        return super(SampleViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='runs-list',
        url_path='runs(?:/(?P<run_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.RunSerializer
    )
    def runs(self, request, accession=None, run_accession=None):
        obj = self.get_object()
        if run_accession is not None:
            queryset = obj.runs.public() \
                .filter(accession=run_accession) \
                .select_related(
                    'sample',
                    'analysis_status',
                    'experiment_type',
                    'pipeline'
                )
        else:
            queryset = obj.runs.public() \
                .select_related(
                    'sample',
                    'analysis_status',
                    'experiment_type',
                    'pipeline'
                )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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

    ordering = ('accession',)

    search_fields = (
        'accession',
    )

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9,_]+'

    def get_queryset(self):
        return emg_models.Run.objects.public() \
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

    @detail_route(
        methods=['get', ],
        url_name='runs-list',
        url_path='runs(?:/(?P<run_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.RunSerializer
    )
    def runs(self, request, release_version=None, run_accession=None):
        obj = self.get_object()
        if run_accession is not None:
            queryset = obj.runs \
                .filter(accession=run_accession) \
                .select_related(
                    'sample',
                    'pipeline',
                    'analysis_status',
                    'experiment_type'
                )
        else:
            queryset = obj.runs.all() \
                .select_related(
                    'sample',
                    'pipeline',
                    'analysis_status',
                    'experiment_type'
                )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
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

    @detail_route(
        methods=['get', ],
        url_name='runs-list',
        url_path='runs(?:/(?P<run_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.RunSerializer
    )
    def runs(self, request, experiment_type=None, run_accession=None):
        obj = self.get_object()
        if run_accession is not None:
            queryset = obj.runs \
                .filter(accession=run_accession) \
                .select_related(
                    'sample',
                    'pipeline',
                    'analysis_status',
                    'experiment_type'
                )
        else:
            queryset = obj.runs.all() \
                .select_related(
                    'sample',
                    'pipeline',
                    'analysis_status',
                    'experiment_type'
                )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PublicationViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):

    serializer_class = emg_serializers.SimplePublicationSerializer

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    filter_fields = (
        'pub_type',
        'published_year',
    )

    ordering_fields = (
        'pub_id',
    )

    ordering = ('pub_id',)

    search_fields = (
        '@pub_title',
        '@pub_abstract',
        'authors',
        'doi',
        'isbn',
    )

    lookup_field = 'pub_id'
    lookup_value_regex = '[a-zA-Z0-9,]+'

    def get_queryset(self):
        # TODO: select studies - many-to-many
        return emg_models.Publication.objects.all() \
            .select_related()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.PublicationSerializer
        return super(PublicationViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='studies-list',
        url_path='studies(?:/(?P<study_accession>[a-zA-Z0-9,]+))?',
        serializer_class=emg_serializers.SimpleStudySerializer
    )
    def studies(self, request, pub_id=None, study_accession=None):
        obj = self.get_object()
        if study_accession is not None:
            queryset = obj.studies \
                .filter(accession=study_accession) \
                .select_related('biome')
        else:
            queryset = obj.studies.all() \
                .select_related('biome')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

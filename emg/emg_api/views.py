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
        DjangoFilterBackend,
        filters.SearchFilter,
        # filters.OrderingFilter,
    )

    # filter_fields = ()

    search_fields = (
        'biome_name',
        'lineage',
    )

    lookup_field = 'biome_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

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
        queryset = self.get_object().samples.all()
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
        queryset = self.get_object().studies.all()
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
    queryset = emg_models.Study.objects.all()

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
        'last_update',
    )

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
        'biome__biome_name',
        'biome__lineage',
    )

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.StudySerializer
        return super(StudyViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='publications-list',
        url_path='publications(?:/(?P<publications_id>[a-zA-Z0-9]+))?',
        serializer_class=emg_serializers.SimplePublicationSerializer
    )
    def publications(self, request, accession=None, publications_id=None):
        queryset = self.get_object().publications.all()
        if publications_id is not None:
            queryset = self.get_object().publications.filter(
                publications_id=publications_id)
        else:
            queryset = self.get_object().publications.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=['get', ],
        url_name='samples-list',
        url_path='samples(?:/(?P<sample_accession>[a-zA-Z0-9]+))?',
        serializer_class=emg_serializers.SimpleSampleSerializer
    )
    def samples(self, request, accession=None, sample_accession=None):
        if sample_accession is not None:
            queryset = self.get_object().samples.filter(
                accession=sample_accession)
        else:
            queryset = self.get_object().samples.all()
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
    queryset = emg_models.Sample.objects.all()

    filter_class = emg_filters.SampleFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    search_fields = (
        # 'sample_id',
        'accession',
        '@sample_name',
        'biome__biome_name',
    )

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.SampleSerializer
        return super(SampleViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='jobs-list',
        url_path='jobs(?:/(?P<job_id>[a-zA-Z0-9]+))?',
        serializer_class=emg_serializers.AnalysisJobSerializer
    )
    def jobs(self, request, accession=None, job_id=None):
        if job_id is not None:
            queryset = self.get_object().analysis_jobs.filter(job_id=job_id)
        else:
            queryset = self.get_object().analysis_jobs.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AnalysisJobViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisJobSerializer
    queryset = emg_models.AnalysisJob.objects.all()

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    filter_fields = (
        'pipeline__release_version',
        'analysis_status_id',
        'experiment_type_id',
    )

    search_fields = (
        '@pipeline__description',
        '@pipeline__changes',
    )

    lookup_field = 'job_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.AnalysisJobSerializer
        return super(AnalysisJobViewSet, self).get_serializer_class()


class PipelineReleaseViewSet(mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):

    serializer_class = emg_serializers.PipelineReleaseSerializer
    queryset = emg_models.PipelineRelease.objects.all()

    filter_class = emg_filters.PipelineReleaseFilter

    filter_backends = (
        DjangoFilterBackend,
        # filters.SearchFilter,
        # filters.OrderingFilter,
    )

    # search_fields = ()

    lookup_field = 'pipeline_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.PipelineReleaseSerializer
        return super(PipelineReleaseViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='jobs-list',
        url_path='jobs(?:/(?P<job_id>[a-zA-Z0-9]+))?',
        serializer_class=emg_serializers.AnalysisJobSerializer
    )
    def jobs(self, request, pipeline_id=None, job_id=None):
        if job_id is not None:
            queryset = self.get_object().analysis_jobs.filter(
                accession=job_id)
        else:
            queryset = self.get_object().analysis_jobs.all()
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
    queryset = emg_models.Publication.objects.all()

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    filter_fields = (
        'pub_type',
        'published_year',
    )

    search_fields = (
        '@pub_title',
        'authors',
        'doi',
        'isbn',
    )

    lookup_field = 'pub_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.PublicationSerializer
        return super(PublicationViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='studies-list',
        url_path='studies(?:/(?P<study_accession>[a-zA-Z0-9]+))?',
        serializer_class=emg_serializers.SimpleStudySerializer
    )
    def studies(self, request, pub_id=None, study_accession=None):
        if study_accession is not None:
            queryset = self.get_object().studies.filter(
                accession=study_accession)
        else:
            queryset = self.get_object().studies.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# -*- coding: utf-8 -*-

import logging

from rest_framework import viewsets, mixins
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import detail_route
# from rest_framework.decorators import list_route

from emg_api import models as emg_models
from emg_api import serializers as emg_serializers

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
        url_name='projects-list',
        serializer_class=emg_serializers.SimpleProjectSerializer
    )
    def projects(self, request, biome_id=None):
        queryset = self.get_object().projects.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProjectViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):

    serializer_class = emg_serializers.SimpleProjectSerializer
    queryset = emg_models.Project.objects.all()

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'ext_study_id',
        'last_update',
    )

    filter_fields = (
        'biome_id',
    )

    search_fields = (
        # 'study_id',
        'ext_study_id',
        '@study_name',
        '@study_abstract',
        'centre_name',
        'author_name',
        'author_email',
        'biome__biome_name',
        'biome__lineage',
    )

    lookup_field = 'ext_study_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.SimpleProjectSerializer
        return super(ProjectViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='publications-list',
        serializer_class=emg_serializers.SimplePublicationSerializer
    )
    def publications(self, request, ext_study_id=None):
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
        serializer_class=emg_serializers.SimpleSampleSerializer
    )
    def samples(self, request, ext_study_id=None):
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

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    filter_fields = (
        'biome_id',
        'analysis_jobs__analysis_status_id',
        'analysis_jobs__experiment_type_id',
        'geo_loc_name',
    )

    search_fields = (
        'sample_id',
        '@sample_name',
        'biome__biome_name',
    )

    lookup_field = 'sample_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.SampleSerializer
        return super(SampleViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='jobs-list',
        serializer_class=emg_serializers.AnalysisJobSerializer
    )
    def jobs(self, request, sample_id=None):
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

    filter_backends = (
        DjangoFilterBackend,
        # filters.SearchFilter,
        # filters.OrderingFilter,
    )

    # filter_fields = ()

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
        serializer_class=emg_serializers.AnalysisJobSerializer
    )
    def jobs(self, request, pipeline_id=None):
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

    # filter_fields = ()

    search_fields = (
        '@pub_title',
        'authors',
    )

    lookup_field = 'pub_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.PublicationSerializer
        return super(PublicationViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='projects-list',
        serializer_class=emg_serializers.SimpleProjectSerializer
    )
    def projects(self, request, pub_id=None):
        queryset = self.get_object().projects.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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


class BiomeHierarchyTreeViewSet(mixins.RetrieveModelMixin,
                                mixins.ListModelMixin,
                                viewsets.GenericViewSet):

    serializer_class = emg_serializers.BiomeHierarchyTreeSerializer
    queryset = emg_models.BiomeHierarchyTree.objects.all()

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
            return emg_serializers.BiomeHierarchyTreeSerializer
        return super(BiomeHierarchyTreeViewSet, self).get_serializer_class()

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

    filter_fields = (
        'biome_id',
        'centre_name',
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
    )

    lookup_field = 'ext_study_id'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return emg_serializers.StudySerializer
        return super(StudyViewSet, self).get_serializer_class()

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
        url_name='studies-list',
        serializer_class=emg_serializers.SimpleStudySerializer
    )
    def studies(self, request, pub_id=None):
        queryset = self.get_object().studies.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# class StudyPublicationViewSet(mixins.RetrieveModelMixin,
#                               mixins.ListModelMixin,
#                               viewsets.GenericViewSet):
#     serializer_class = emg_serializers.PublicationSerializer
#     queryset = emg_models.Publication.objects.all()
#
#     filter_backends = (
#         DjangoFilterBackend,
#         filters.SearchFilter,
#         filters.OrderingFilter,
#     )
#
#     # filter_fields = ()
#
#     search_fields = (
#         '@pub_title',
#         'authors',
#     )
#
#     lookup_field = 'pub_id'
#     lookup_value_regex = '[a-zA-Z0-9]+'
#
#     def get_study(self, request, studies_study_id=None):
#         study = get_object_or_404(
#              emg_models.Study.objects.all(), study_id=studies_study_id)
#         self.check_object_permissions(self.request, study)
#         return study
#
#     def get_queryset(self):
#         study_id = self.kwargs['studies_study_id']
#         return emg_models.Publication.objects.filter(studies=study_id)
#
#     def list(self, request, *args, **kwargs):
#         self.get_study(request, studies_study_id=kwargs['studies_study_id'])
#         return super().list(request, *args, **kwargs)
#
#     def retrieve(self, request, studies_study_id=None, pub_id=None,
#                  *args, **kwargs):
#         queryset = emg_models.Publication.objects.filter(
#             studies=studies_study_id,
#             pub_id=pub_id)
#         serializer = self.get_serializer(queryset)
#         return Response(data=serializer.data)
#
#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['studies_study_id'] = self.kwargs.get('studies_study_id')
#         return context
#
#
# class StudySampleViewSet(mixins.ListModelMixin,
#                          viewsets.GenericViewSet):
#     queryset = emg_models.Sample.objects.all()
#     serializer_class = emg_serializers.SampleSerializer
#
#     filter_backends = (
#         DjangoFilterBackend,
#         filters.SearchFilter,
#         filters.OrderingFilter,
#     )
#
#     # filter_fields = ()
#
#     search_fields = (
#         'sample_id',
#         '@sample_name',
#         'biome__biome_name',
#     )
#
#     lookup_field = 'sample_id'
#     lookup_value_regex = '[a-zA-Z0-9]+'
#
#     def get_study(self, request, studies_study_id=None):
#         study = get_object_or_404(
#             emg_models.Study.objects.all(), study_id=studies_study_id)
#         self.check_object_permissions(self.request, study)
#         return study
#
#     def get_queryset(self):
#         return emg_models.Sample.objects.filter(
#             study=self.kwargs['studies_study_id'])
#
#     def list(self, request, *args, **kwargs):
#         self.get_study(request, studies_study_id=kwargs['studies_study_id'])
#         return super().list(request, *args, **kwargs)

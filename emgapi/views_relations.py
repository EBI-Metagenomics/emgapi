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

from django.db.models import Sum
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, mixins
from rest_framework import filters
from rest_framework.response import Response

from . import models as emg_models
from . import serializers as emg_serializers
from . import filters as emg_filters
from . import mixins as emg_mixins
from . import pagination as emg_page


class BaseStudyRelationshipViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudySerializer
    pagination_class = emg_page.LargeSetPagination

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
    )


class BiomeStudyRelationshipViewSet(mixins.ListModelMixin,
                                    BaseStudyRelationshipViewSet):

    lookup_field = 'lineage'

    def get_queryset(self):
        lineage = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Biome, lineage=lineage)
        studies = emg_models.Sample.objects \
            .available(self.request) \
            .filter(
                biome__lft__gte=obj.lft, biome__rgt__lte=obj.rgt,
                biome__depth__gte=obj.depth) \
            .values('studies')
        queryset = emg_models.Study.objects \
            .available(self.request) \
            .filter(study_id__in=studies)
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('samples', queryset=_qs))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of studies for the given biome
        Example:
        ---
        `/biomes/root:Environmental:Aquatic/studies` retrieve linked
        studies

        `/biomes/root:Environmental:Aquatic/studies?include=samples` with
        studies
        """
        return super(BiomeStudyRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class PublicationStudyRelationshipViewSet(mixins.ListModelMixin,
                                          BaseStudyRelationshipViewSet):

    lookup_field = 'pubmed_id'
    lookup_value_regex = '[0-9\.]+'

    def get_queryset(self):
        pubmed_id = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Publication, pubmed_id=pubmed_id)
        queryset = emg_models.Study.objects \
            .available(self.request) \
            .filter(publications=obj)
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('samples', queryset=_qs))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of studies for the given Pubmed ID
        Example:
        ---
        `/publications/{pubmed}/studies` retrieve linked studies

        `/publications/{pubmed}/studies?include=samples` with samples
        """
        return super(PublicationStudyRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class BaseSampleRelationshipViewSet(viewsets.GenericViewSet):

    serializer_class = emg_serializers.SampleSerializer
    pagination_class = emg_page.LargeSetPagination

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


class StudySampleRelationshipViewSet(mixins.ListModelMixin,
                                     BaseSampleRelationshipViewSet):

    lookup_field = 'accession'

    def get_queryset(self):
        study = get_object_or_404(
            emg_models.Study, accession=self.kwargs[self.lookup_field])
        queryset = emg_models.Sample.objects \
            .available(self.request) \
            .filter(studies__in=[study])
        _qs = emg_models.Study.objects.available(self.request)
        # queryset = queryset.prefetch_related(
        #     Prefetch('studies', queryset=_qs))
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects \
                .available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples for the given study accession
        Example:
        ---
        `/studies/SRP001634/samples` retrieve linked samples

        `/studies/SRP001634/samples?include=runs` with runs

        Filter by:
        ---
        `/studies/ERP009004/samples?biome=root%3AEnvironmental%3AAquatic`
        filtered by biome

        `/studies/ERP009004/samples?geo_loc_name=Alberta` filtered by
        localtion
        """
        return super(StudySampleRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class PipelineSampleRelationshipViewSet(mixins.ListModelMixin,
                                        BaseSampleRelationshipViewSet):

    lookup_field = 'release_version'

    def get_queryset(self):
        pipeline = get_object_or_404(
            emg_models.Pipeline,
            release_version=self.kwargs[self.lookup_field])
        queryset = emg_models.Sample.objects \
            .available(self.request) \
            .filter(analysis__pipeline=pipeline)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples for the given pipeline version
        Example:
        ---
        `/pipeline/3.0/samples` retrieve linked samples

        `/pipeline/3.0/samples?include=runs` with runs

        Filter by:
        ---
        `/pipeline/3.0/samples?biome=root%3AEnvironmental%3AAquatic`
        filtered by biome

        `/pipeline/3.0/samples?geo_loc_name=Alberta` filtered by
        localtion
        """
        return super(PipelineSampleRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class PipelineAnalysisRelationshipViewSet(mixins.ListModelMixin,
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
    ordering = ('accession',)

    lookup_field = 'release_version'

    def get_queryset(self):
        pipeline = get_object_or_404(
            emg_models.Pipeline,
            release_version=self.kwargs[self.lookup_field])
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(pipeline=pipeline)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of analysis results for the given pipeline version
        Example:
        ---
        `/pipeline/4.0/analysis` retrieve linked analysis

        """
        return super(PipelineAnalysisRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class PipelineStudyRelationshipViewSet(mixins.ListModelMixin,
                                       BaseStudyRelationshipViewSet):

    lookup_field = 'release_version'

    def get_queryset(self):
        pipeline = get_object_or_404(
            emg_models.Pipeline,
            release_version=self.kwargs[self.lookup_field])
        queryset = emg_models.Study.objects \
            .available(self.request) \
            .filter(samples__analysis__pipeline=pipeline)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples for the given pipeline version
        Example:
        ---
        `/pipeline/3.0/studies` retrieve linked studies

        `/pipeline/3.0/studies?include=samples` with samples
        """
        return super(PipelineStudyRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class ExperimentSampleRelationshipViewSet(mixins.ListModelMixin,
                                          BaseSampleRelationshipViewSet):

    lookup_field = 'experiment_type'

    def get_queryset(self):
        experiment_type = get_object_or_404(
            emg_models.ExperimentType,
            experiment_type=self.kwargs[self.lookup_field])
        queryset = emg_models.Sample.objects \
            .available(self.request) \
            .filter(runs__experiment_type=experiment_type)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        # if 'studies' in self.request.GET.get('include', '').split(','):
        #     queryset = queryset.select_related('studies')
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples for the given experiment type
        Example:
        ---
        `/experiments/metagenomic/samples` retrieve linked samples

        `/experiments/metagenomic/samples?include=runs` with runs

        Filter by:
        ---
        `/experiments/metagenomic/samples?biome=root%3AEnvironmental
        %3AAquatic` filtered by biome

        `/experiments/metagenomic/samples?geo_loc_name=Alberta`
        filtered by localtion
        """
        return super(ExperimentSampleRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class BiomeSampleRelationshipViewSet(mixins.ListModelMixin,
                                     BaseSampleRelationshipViewSet):

    lookup_field = 'lineage'

    def get_queryset(self):
        lineage = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Biome, lineage=lineage)
        queryset = emg_models.Sample.objects \
            .available(self.request) \
            .filter(
                biome__lft__gte=obj.lft, biome__rgt__lte=obj.rgt,
                biome__depth__gte=obj.depth)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        # if 'studies' in self.request.GET.get('include', '').split(','):
        #     queryset = queryset.select_related('studies')
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples for the given biome
        Example:
        ---
        `/biomes/root:Environmental:Aquatic/samples` retrieve linked
        samples

        `/biomes/root:Environmental:Aquatic/samples?include=runs` with
        runs

        Filter by:
        ---
        `/biomes/root:Environmental:Aquatic/samples?geo_loc_name=Alberta`
        filtered by localtion

        """
        return super(BiomeSampleRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class PublicationSampleRelationshipViewSet(mixins.ListModelMixin,
                                           BaseSampleRelationshipViewSet):

    lookup_field = 'pubmed_id'
    lookup_value_regex = '[0-9\.]+'

    def get_queryset(self):
        pubmed_id = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Publication, pubmed_id=pubmed_id)
        queryset = emg_models.Sample.objects \
            .available(self.request) \
            .filter(studies__publications=obj)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        # if 'studies' in self.request.GET.get('include', '').split(','):
        #     queryset = queryset.select_related('studies')
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of studies for the given Pubmed ID
        Example:
        ---
        `/publications/{pubmed}/samples` retrieve linked samples

        `/publications/{pubmed}/samples?include=runs` with runs
        """
        return super(PublicationSampleRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class BaseRunRelationshipViewSet(mixins.ListModelMixin,
                                 viewsets.GenericViewSet):

    serializer_class = emg_serializers.RunSerializer
    pagination_class = emg_page.LargeSetPagination

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


class ExperimentRunRelationshipViewSet(BaseRunRelationshipViewSet):

    lookup_field = 'experiment_type'

    def get_queryset(self):
        experiment_type = get_object_or_404(
            emg_models.ExperimentType,
            experiment_type=self.kwargs[self.lookup_field])
        queryset = emg_models.Run.objects \
            .available(self.request) \
            .filter(experiment_type=experiment_type).distinct()
        return queryset

    def get_serializer_class(self):
        return super(ExperimentRunRelationshipViewSet,
                     self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs for the given sample accession
        Example:
        ---
        `/experiment-type/ERS1015417/runs`
        """
        return super(ExperimentRunRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class SampleRunRelationshipViewSet(BaseRunRelationshipViewSet):

    lookup_field = 'accession'

    def get_queryset(self):
        sample = get_object_or_404(
            emg_models.Sample, accession=self.kwargs[self.lookup_field])
        queryset = emg_models.Run.objects.available(self.request) \
            .filter(sample_id=sample) \
            .distinct()
        return queryset

    def get_serializer_class(self):
        return super(SampleRunRelationshipViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs for the given sample accession
        Example:
        ---
        `/samples/ERS1015417/runs`

        Filter by:
        ---
        `/samples/ERS1015417/runs?experiment_type=metagenomics`
        """
        return super(SampleRunRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class SampleStudiesRelationshipViewSet(mixins.ListModelMixin,
                                       BaseStudyRelationshipViewSet):

    lookup_field = 'accession'

    def get_queryset(self):
        sample = get_object_or_404(
            emg_models.Sample,
            accession=self.kwargs[self.lookup_field])
        queryset = emg_models.Study.objects \
            .available(self.request) \
            .filter(samples=sample)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs for the given sample accession
        Example:
        ---
        `/samples/ERS1015417/studies`

        Filter by:
        ---
        `/sample/ERS1015417/studies`
        """
        return super(SampleStudiesRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class BiomeTreeViewSet(mixins.ListModelMixin,
                       viewsets.GenericViewSet):

    serializer_class = emg_serializers.BiomeSerializer
    queryset = emg_models.Biome.objects.filter(depth=1)

    filter_class = emg_filters.BiomeFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'lineage',
    )
    ordering = ('biome_id',)

    lookup_field = 'lineage'
    lookup_value_regex = '[a-zA-Z0-9\:\-\s\(\)\<\>]+'

    def get_queryset(self):
        lineage = self.kwargs.get('lineage', None).strip()
        if lineage:
            _lineage = get_object_or_404(emg_models.Biome, lineage=lineage)
            queryset = emg_models.Biome.objects \
                .filter(lft__gt=_lineage.lft, rgt__lt=_lineage.rgt,
                        depth__gt=_lineage.depth)
        else:
            queryset = super(BiomeTreeViewSet, self).get_queryset()
        return queryset

    def get_serializer_class(self):
        return super(BiomeTreeViewSet, self).get_serializer_class()

    def get_serializer_context(self):
        context = super(BiomeTreeViewSet, self).get_serializer_context()
        context['lineage'] = self.kwargs.get('lineage')
        return context

    def list(self, request, *args, **kwargs):
        """
        Retrieves children for the given Biome node
        Example:
        ---
        `/biomes/root:Environmental:Aquatic/children`
        list all children
        """

        return super(BiomeTreeViewSet, self).list(request, *args, **kwargs)


class PipelinePipelineToolRelationshipViewSet(mixins.ListModelMixin,
                                              viewsets.GenericViewSet):

    serializer_class = emg_serializers.PipelineToolSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'tool_name',
    )
    ordering = ('tool_name',)

    lookup_field = 'release_version'
    lookup_value_regex = '[a-zA-Z0-9.]+'

    def get_queryset(self):
        release_version = self.kwargs[self.lookup_field]
        obj = get_object_or_404(
            emg_models.Pipeline, release_version=release_version)
        queryset = emg_models.PipelineTool.objects.filter(pipelines=obj)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of pipeline tools for the given pipeline version
        Example:
        ---
        `/pipeline/{release_version}/tools`
        """
        return super(PipelinePipelineToolRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class StudySummaryViewSet(emg_mixins.MultipleFieldLookupMixin,
                          viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudyAnnSerializer

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        accession = self.kwargs['accession']
        release_version = self.kwargs['release_version']
        queryset = emg_models.AnalysisJobAnn.objects.filter(
            job__study__accession=accession,
            job__pipeline__release_version=release_version) \
            .select_related('job', 'var') \
            .values('var__var_name') \
            .annotate(total_value=Sum('var_val_ucv'))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves summary for the study and pipeline version
        Example:
        ---
        `/studies/ERP001736/pipelines/2.0/summary` retrieve summary
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

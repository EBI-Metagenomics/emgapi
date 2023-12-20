# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

from django.http import HttpResponse
from django.db.models import Prefetch, Count, Q
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, mixins
from rest_framework import filters

from . import models as emg_models
from . import serializers as emg_serializers
from . import filters as emg_filters
from . import viewsets as emg_viewsets
from . import mixins as emg_mixins
from . import utils as emg_utils

logger = logging.getLogger(__name__)


class BiomeStudyRelationshipViewSet(emg_mixins.ListModelMixin,
                                    emg_viewsets.BaseStudyGenericViewSet):
    lookup_field = 'lineage'

    def get_queryset(self):
        lineage = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Biome, lineage=lineage)
        queryset = emg_models.Study.objects.available(
            self.request
        ).filter(
            biome__lft__gte=obj.lft,
            biome__rgt__lte=obj.rgt,
            biome__depth__gte=obj.depth,
        )
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request, prefetch=True)
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


class PublicationStudyRelationshipViewSet(emg_mixins.ListModelMixin,
                                          emg_viewsets.BaseStudyGenericViewSet):  # noqa

    lookup_field = 'pubmed_id'

    def get_queryset(self):
        pubmed_id = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Publication, pubmed_id=pubmed_id)
        queryset = emg_models.Study.objects \
            .available(self.request) \
            .filter(publications=obj)
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request, prefetch=True)
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


class StudyGeoCoordinateRelationshipViewSet(mixins.ListModelMixin,
                                            viewsets.GenericViewSet):
    serializer_class = emg_serializers.SampleGeoCoordinateSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'longitude',
        'latitude',
    )

    ordering = ('longitude',)

    lookup_field = 'accession'

    def get_queryset(self):
        study = get_object_or_404(
            emg_models.Study,
            *emg_utils.study_accession_query(self.kwargs['accession'])
        )
        queryset = emg_models.SampleGeoCoordinate.objects \
            .available(self.request) \
            .filter(studies=study.study_id) \
            .values('lon_lat_pk', 'longitude', 'latitude') \
            .annotate(samples_count=Count('lon_lat_pk'))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of geo coordinates for the given study accession
        Example:
        ---
        `/studies/ERP001736/geocoordinates` retrieve geo coordinates
        """

        return super(StudyGeoCoordinateRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class StudyStudyRelationshipViewSet(emg_mixins.ListModelMixin,
                                    emg_viewsets.BaseStudyGenericViewSet):
    lookup_field = 'accession'

    def get_queryset(self):
        study = get_object_or_404(
            emg_models.Study,
            *emg_utils.study_accession_query(
                self.kwargs['accession'])
        )
        samples = emg_models.StudySample.objects \
            .filter(study_id=study.study_id) \
            .values("sample_id")
        studies = emg_models.StudySample.objects \
            .filter(Q(sample_id__in=samples),
                    ~Q(study_id=study.study_id)) \
            .values("study_id")
        queryset = emg_models.Study.objects.filter(study_id__in=studies) \
            .available(self.request).distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of studies for the given study accession
        sharing the same set of samples
        Example:
        ---
        `/studies/SRP001634/studies` retrieve linked studies

        """
        return super(StudyStudyRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class StudySampleRelationshipViewSet(emg_mixins.ListModelMixin,
                                     emg_viewsets.BaseSampleGenericViewSet):
    lookup_field = 'accession'

    def get_queryset(self):
        study = get_object_or_404(
            emg_models.Study,
            *emg_utils.study_accession_query(self.kwargs['accession'])
        )
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True) \
            .filter(studies__in=[study])
        _qs = emg_models.Study.objects.available(self.request)
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
        `/studies/ERP009004/samples?lineage=root%3AEnvironmental%3AAquatic`
        filtered by biome

        `/studies/ERP009004/samples?geo_loc_name=Alberta` filtered by
        localtion
        """
        return super(StudySampleRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class StudyPublicationRelationshipViewSet(emg_mixins.ListModelMixin,
                                          emg_viewsets.BasePublicationGenericViewSet):  # noqa

    lookup_field = 'accession'

    def get_queryset(self):
        study = get_object_or_404(
            emg_models.Study,
            *emg_utils.study_accession_query(self.kwargs['accession'])
        )
        queryset = emg_models.Publication.objects \
            .filter(studies__in=[study])
        if 'studies' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Study.objects \
                .available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('studies', queryset=_qs))
        return queryset

    def get_serializer_class(self):
        return super(StudyPublicationRelationshipViewSet, self) \
            .get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of publications for the given study accession
        Example:
        ---
        `/studies/SRP000183/publications` retrieve linked publications

        `/studies/SRP000183/publications?ordering=published_year`
        ordered by year

        Search for:
        ---
        title, abstract, authors, etc.

        `/studies/SRP000183/publications?search=text`
        """
        return super(StudyPublicationRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class StudiesDownloadViewSet(emg_mixins.MultipleFieldLookupMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'
    lookup_fields = ('accession', 'release_version', 'alias')

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
            Q(pipeline__release_version=self.kwargs['release_version'])
        )

    def get_serializer_class(self):
        return super(StudiesDownloadViewSet, self).get_serializer_class()

    def retrieve(self, request, accession, release_version, alias,
                 *args, **kwargs):
        """
        Retrieves static summary file
        Example:
        ---
        `
        /studies/MGYS00000410/pipelines/2.0/file/
        ERP001736_taxonomy_abundances_v2.0.tsv`
        """
        obj = self.get_object()
        response = HttpResponse()
        response['Content-Type'] = 'application/octet-stream'
        response["Content-Disposition"] = \
            "attachment; filename={0}".format(alias)
        if obj.subdir is not None:
            response['X-Accel-Redirect'] = \
                "/results{0}/{1}/{2}".format(
                    obj.study.result_directory, obj.subdir, obj.realname
                )
        else:
            response['X-Accel-Redirect'] = \
                "/results{0}/{1}".format(
                    obj.study.result_directory, obj.realname
                )
        return response


class StudyAnalysisResultViewSet(emg_mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    serializer_class = emg_serializers.AnalysisSerializer

    filterset_class = emg_filters.AnalysisJobFilter

    filter_backends = (
        DjangoFilterBackend,
        emg_filters.getUnambiguousOrderingFilterByField('job_id'),
    )

    ordering_fields = (
        'pipeline',
        # 'accession',
    )

    ordering = ('-pipeline',)

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(StudyAnalysisResultViewSet, self).get_serializer_class()

    def get_queryset(self):
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(*emg_utils.related_study_accession_query(
            self.kwargs['accession']))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession
        Example:
        ---
        `/studies/MGYS00000410/analyses`
        """
        return super(StudyAnalysisResultViewSet, self) \
            .list(request, *args, **kwargs)


class SuperStudyFlagshipStudiesViewSet(
    emg_mixins.ListModelMixin,
    emg_viewsets.BaseStudyGenericViewSet
):
    lookup_field = 'super_study_id'

    def get_queryset(self):
        super_study = emg_models.SuperStudy.objects.get_by_id_or_slug_or_404(
            id_or_slug=self.kwargs['super_study_id']
        )
        return super_study.studies.filter(superstudystudy__is_flagship=True).available(self.request)

    def list(self, request, *args, **kwargs):
        """
        Retrieves flagship studies for the given super_study_id
        Example:
        ---
        `/super-studies/1/flagship-studies`
        """
        return super(SuperStudyFlagshipStudiesViewSet, self) \
            .list(request, *args, **kwargs)


class SuperStudyRelatedStudiesViewSet(
    emg_mixins.ListModelMixin,
    emg_viewsets.BaseStudyGenericViewSet
):
    lookup_field = 'super_study_id'

    def get_queryset(self):
        super_study = emg_models.SuperStudy.objects.get_by_id_or_slug_or_404(
            id_or_slug=self.kwargs['super_study_id']
        )
        return super_study.studies.filter(superstudystudy__is_flagship=False).available(self.request)

    def list(self, request, *args, **kwargs):
        """
        Retrieves related studies for the given super_study_id
        Example:
        ---
        `/super-studies/1/related-studies`
        """
        return super(SuperStudyRelatedStudiesViewSet, self) \
            .list(request, *args, **kwargs)


class SuperStudyGenomeCataloguesViewSet(
    emg_mixins.ListModelMixin,
    emg_viewsets.BaseGenomeCatalogueGenericViewSet
):
    lookup_field = 'super_study_id'

    def get_queryset(self):
        super_study = emg_models.SuperStudy.objects.get_by_id_or_slug_or_404(
            id_or_slug=self.kwargs['super_study_id']
        )
        return super_study.genome_catalogues

    def list(self, request, *args, **kwargs):
        """
        Retrieves genome catalogues related to the given super_study_id
        Example:
        ---
        `/super-studies/1/genome-catalogues`
        """
        return super(SuperStudyGenomeCataloguesViewSet, self) \
            .list(request, *args, **kwargs)


class RunAnalysisViewSet(emg_mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = emg_serializers.AnalysisSerializer

    filterset_class = emg_filters.AnalysisJobFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'pipeline',
    )

    ordering = ('-pipeline',)

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(RunAnalysisViewSet, self).get_serializer_class()

    def get_queryset(self):
        run = get_object_or_404(
            emg_models.Run,
            accession=self.kwargs['accession'])
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(run=run)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession
        Example:
        ---
        `/runs/ERR1385375/analyses`
        """
        return super(RunAnalysisViewSet, self) \
            .list(request, *args, **kwargs)


class PipelineSampleRelationshipViewSet(emg_mixins.ListModelMixin,
                                        emg_viewsets.BaseSampleGenericViewSet):  # noqa

    lookup_field = 'release_version'

    def get_queryset(self):
        pipeline = get_object_or_404(
            emg_models.Pipeline,
            release_version=self.kwargs[self.lookup_field])
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True) \
            .filter(analyses__pipeline=pipeline)
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


class PipelineAnalysisRelationshipViewSet(emg_mixins.ListModelMixin,
                                          emg_viewsets.BaseAnalysisGenericViewSet):  # noqa

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
        `/pipeline/4.0/analyses` retrieve linked analysis

        """
        return super(PipelineAnalysisRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class ExperimentTypeAnalysisRelationshipViewSet(  # noqa
    emg_mixins.ListModelMixin,
    emg_viewsets.BaseAnalysisGenericViewSet):
    lookup_field = 'experiment_type'

    def get_queryset(self):
        experiment_type = get_object_or_404(
            emg_models.ExperimentType,
            experiment_type=self.kwargs[self.lookup_field])
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(experiment_type=experiment_type)
        if 'sample' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects.available(
                self.request, prefetch=True)
            queryset = queryset.prefetch_related(
                Prefetch('sample', queryset=_qs))
        if 'study' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Study.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('study', queryset=_qs))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of samples for the given experiment type
        Example:
        ---
        `/experiments/metagenomic/analyses` retrieve linked analysis

        """
        return super(ExperimentTypeAnalysisRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class ExperimentTypeSampleRelationshipViewSet(emg_mixins.ListModelMixin,
                                              emg_viewsets.BaseSampleGenericViewSet):  # noqa

    lookup_field = 'experiment_type'

    def get_queryset(self):
        experiment_type = get_object_or_404(
            emg_models.ExperimentType,
            experiment_type=self.kwargs[self.lookup_field])
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True) \
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
        return super(ExperimentTypeSampleRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class BiomeSampleRelationshipViewSet(emg_mixins.ListModelMixin,
                                     emg_viewsets.BaseSampleGenericViewSet):
    lookup_field = 'lineage'
    relationship_lookup_field = 'accession'

    def get_queryset(self):
        lineage = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Biome, lineage=lineage)
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True) \
            .filter(biome__lft__gte=obj.lft, biome__rgt__lte=obj.rgt,
                    biome__depth__gte=obj.depth)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
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


class BiomeGenomeRelationshipViewSet(emg_mixins.ListModelMixin,
                                     emg_viewsets.BaseGenomeGenericViewSet):
    lookup_field = 'lineage'

    def get_queryset(self):
        lineage = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Biome, lineage=lineage)
        queryset = emg_models.Genome.objects.filter(biome=obj)
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
        return super(BiomeGenomeRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class BiomeGenomeCatalogueRelationshipViewSet(emg_mixins.ListModelMixin,
                                              emg_viewsets.BaseGenomeCatalogueGenericViewSet):
    lookup_field = 'lineage'

    def get_queryset(self):
        lineage = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Biome, lineage=lineage)
        queryset = emg_models.GenomeCatalogue.objects.filter(biome=obj)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of genome catalogues for the given biome
        Example:
        ---
        `/biomes/root:Environmental:Aquatic/genome-catalogues` retrieve genome
        catalogues for the aquatic biome

        Filter by:
        ---
        `/biomes/root:Environmental:Aquatic/genome-catalogues?name=fishes`
        filtered by catalogue name

        """
        return super(BiomeGenomeCatalogueRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class GenomeCatalogueGenomeRelationshipViewSet(emg_mixins.ListModelMixin,
                                               emg_viewsets.BaseGenomeGenericViewSet):  # noqa
    lookup_field = 'catalogue_id'

    search_fields = (
        'accession',
        'taxon_lineage',
        'type',
        'genome_set__name',
        'catalogue__name'
    )

    def get_queryset(self):
        catalogue_id = self.kwargs[self.lookup_field]
        if catalogue_id == 'all':
            genomes = emg_models.Genome.objects.all()
        else:

            catalogue = get_object_or_404(
                emg_models.GenomeCatalogue,
                catalogue_id=catalogue_id)
            genomes = catalogue.genomes.all()
        return genomes

    def list(self, request, *args, **kwargs):
        return super(GenomeCatalogueGenomeRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class PublicationSampleRelationshipViewSet(emg_mixins.ListModelMixin,
                                           emg_viewsets.BaseSampleGenericViewSet):  # noqa

    lookup_field = 'pubmed_id'

    def get_queryset(self):
        pubmed_id = self.kwargs[self.lookup_field]
        obj = get_object_or_404(emg_models.Publication, pubmed_id=pubmed_id)
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True) \
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


class ExperimentTypeRunRelationshipViewSet(emg_mixins.ListModelMixin,
                                           emg_viewsets.BaseRunGenericViewSet):  # noqa

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
        return super(ExperimentTypeRunRelationshipViewSet,
                     self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of runs for the given sample accession
        Example:
        ---
        `/experiment-type/ERS1015417/runs`
        """
        return super(ExperimentTypeRunRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class SampleRunRelationshipViewSet(emg_mixins.ListModelMixin,
                                   emg_viewsets.BaseRunGenericViewSet):
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


class SampleStudiesRelationshipViewSet(emg_mixins.ListModelMixin,
                                       emg_viewsets.BaseStudyGenericViewSet):
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

    filterset_class = emg_filters.BiomeFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    search_fields = (
        '@biome_name',
        'lineage',
    )

    ordering_fields = (
        'biome_name',
        'lineage',
        'samples_count',
        'studies_count',
    )
    ordering = ('biome_id',)

    lookup_field = 'lineage'

    lookup_value_regex = '[a-zA-Z0-9\:\-\s\(\)\<\>]+'  # noqa: W605

    def get_queryset(self):
        lineage = self.kwargs.get('lineage', None).strip()
        if lineage:
            _lineage = get_object_or_404(emg_models.Biome, lineage=lineage)
            queryset = emg_models.Biome.objects \
                .filter(lft__gte=_lineage.lft, rgt__lte=_lineage.rgt,
                        depth__gte=_lineage.depth)
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
                                              viewsets.GenericViewSet):  # noqa

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


class SampleMetadataRelationshipViewSet(mixins.ListModelMixin,
                                        viewsets.GenericViewSet):
    serializer_class = emg_serializers.SampleAnnSerializer

    lookup_field = 'accession'

    lookup_value_regex = '[a-zA-Z0-9\-\_]+'  # noqa: W605

    def get_queryset(self):
        accession = self.kwargs[self.lookup_field]
        return emg_models.SampleAnn.objects \
            .filter(sample__accession=accession) \
            .prefetch_related(
            Prefetch('sample', queryset=emg_models.Sample.objects.available(self.request))) \
            .order_by('var')

    def list(self, request, *args, **kwargs):
        """
        Retrieves metadatafor the given analysis job
        Example:
        ---
        `/samples/ERS1015417/metadata` retrieve metadata
        """
        return super(SampleMetadataRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class RunAssemblyViewSet(emg_mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = emg_serializers.AssemblySerializer

    filterset_class = emg_filters.AssemblyFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
    )

    ordering = ('-accession',)

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(RunAssemblyViewSet, self).get_serializer_class()

    def get_queryset(self):
        run = get_object_or_404(
            emg_models.Run,
            accession=self.kwargs['accession'])
        queryset = emg_models.Assembly.objects \
            .available(self.request) \
            .filter(runs__in=[run])
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession
        Example:
        ---
        `/runs/ERR1385375/assemblies`
        """
        return super(RunAssemblyViewSet, self) \
            .list(request, *args, **kwargs)


class AssemblyAnalysisViewSet(emg_mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    serializer_class = emg_serializers.AnalysisSerializer

    filterset_class = emg_filters.AnalysisJobFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'pipeline',
    )

    ordering = ('-pipeline',)

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(AssemblyAnalysisViewSet, self).get_serializer_class()

    def get_queryset(self):
        assembly = get_object_or_404(
            emg_models.Assembly,
            Q(accession=self.kwargs['accession']) |
            Q(wgs_accession=self.kwargs['accession']) |
            Q(legacy_accession=self.kwargs['accession'])
        )
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request) \
            .filter(assembly=assembly)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession
        Example:
        ---
        `/assemblies/ERZ1385375/analyses`
        """
        return super(AssemblyAnalysisViewSet, self) \
            .list(request, *args, **kwargs)


class AssemblyRunsViewSet(emg_mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    serializer_class = emg_serializers.RunSerializer

    filterset_class = emg_filters.RunFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'accession',
    )

    ordering = ('-accession',)

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(AssemblyRunsViewSet, self).get_serializer_class()

    def get_queryset(self):
        assembly = get_object_or_404(
            emg_models.Assembly,
            Q(accession=self.kwargs['accession']) |
            Q(wgs_accession=self.kwargs['accession']) |
            Q(legacy_accession=self.kwargs['accession'])
        )
        queryset = emg_models.Run.objects \
            .available(self.request) \
            .filter(assemblies__in=[assembly])
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves the runs for the given accession
        Example:
        ---
        `/assemblies/ERZ1385375/runs`
        """
        return super(AssemblyRunsViewSet, self) \
            .list(request, *args, **kwargs)


class GenomeCogsRelationshipsViewSet(emg_mixins.ListModelMixin,
                                     viewsets.GenericViewSet):
    serializer_class = emg_serializers.CogCountSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'genome_count',
        'description'
    )

    ordering = ['-genome_count']

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        genome = get_object_or_404(
            emg_models.Genome,
            Q(accession=self.kwargs['accession'])
        )
        queryset = emg_models.GenomeCogCounts.objects \
            .select_related('cog', 'genome') \
            .filter(genome=genome)
        return queryset


class GenomeKeggClassRelationshipsViewSet(emg_mixins.ListModelMixin,
                                          viewsets.GenericViewSet):
    serializer_class = emg_serializers.KeggClassMatchSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'class_id',
        'name',
        'genome_count',
    )

    ordering = ['-genome_count']

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        genome = get_object_or_404(
            emg_models.Genome,
            Q(accession=self.kwargs['accession'])
        )
        queryset = emg_models.GenomeKeggClassCounts.objects \
            .select_related('kegg_class') \
            .filter(genome=genome)
        return queryset


class GenomeKeggModuleRelationshipsViewSet(emg_mixins.ListModelMixin,
                                           viewsets.GenericViewSet):
    serializer_class = emg_serializers.KeggModuleMatchSerializer

    # filter_backends = (
    #     filters.OrderingFilter,
    # )

    ordering_fields = (
        'class_id',
        'name',
        'genome_count',
    )

    ordering = ['-genome_count']

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        genome = get_object_or_404(
            emg_models.Genome,
            Q(accession=self.kwargs['accession'])
        )
        queryset = emg_models.GenomeKeggModuleCounts.objects \
            .select_related('kegg_module') \
            .filter(genome=genome)
        return queryset


class GenomeAntiSmashGeneClustersRelationshipsViewSet(emg_mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = emg_serializers.AntiSmashCountSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'genome_count'
    )

    ordering = ['-genome_count']

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        genome = get_object_or_404(
            emg_models.Genome,
            Q(accession=self.kwargs['accession'])
        )
        queryset = emg_models.GenomeAntiSmashGCCounts.objects \
            .selected_related('') \
            .filter(genome=genome)
        return queryset


class GenomeSetGenomes(emg_mixins.ListModelMixin,
                       emg_viewsets.BaseGenomeGenericViewSet):  # noqa
    lookup_field = 'name'

    def get_queryset(self):
        set_name = self.kwargs[self.lookup_field]
        if set_name == 'all':
            genomes = emg_models.Genome.objects.all()
        else:
            genome_set = get_object_or_404(
                emg_models.GenomeSet,
                name=set_name)
            genomes = emg_models.Genome.objects.filter(genome_set=genome_set)
        return genomes

    def list(self, request, *args, **kwargs):
        return super(GenomeSetGenomes, self) \
            .list(request, *args, **kwargs)

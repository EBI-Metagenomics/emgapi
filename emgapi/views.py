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

import os
import logging
import inflection

from django.conf import settings
from django.db.models import Q
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.middleware import csrf
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.response import Response

from rest_framework import filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import status

from . import models as emg_models
from . import serializers as emg_serializers
from . import mixins as emg_mixins
from . import permissions as emg_perms
from . import viewsets as emg_viewsets
from . import utils as emg_utils
from . import renderers as emg_renderers


from emgena import models as ena_models
from emgena import serializers as ena_serializers

logger = logging.getLogger(__name__)


class UtilsViewSet(viewsets.GenericViewSet):

    schema = None

    def get_queryset(self):
        return ()

    @list_route(
        methods=['get', ],
        serializer_class=emg_serializers.TokenSerializer
    )
    def csrf_token(self, request):
        """
        Retrieves csrf token
        """
        token = csrf.get_token(request)
        csrf_token = emg_models.Token(id=token, token=token)
        serializer = self.get_serializer(csrf_token)
        return Response(serializer.data)

    @list_route(
        methods=['get', ],
        serializer_class=emg_serializers.ResourceSerializer
    )
    def resources(self, request):
        """
        Retrieves list of resources
        """
        stats = list()
        for m in [
            emg_models.Study, emg_models.Sample, emg_models.Run,
            emg_models.AnalysisJob
        ]:
            c = m.objects.available(self.request).count()
            r = emg_models.Resource(
                id=inflection.pluralize(m._meta.model_name),
                count=c
            )
            stats.append(r)
        serializer = self.get_serializer(stats, many=True)
        return Response(serializer.data)

    @list_route(
        methods=['get', ],
        serializer_class=ena_serializers.SubmitterSerializer,
        permission_classes=[permissions.IsAuthenticated, emg_perms.IsSelf]
    )
    def myaccounts(self, request, pk=None):
        submitter = ena_models.Submitter.objects.using('ena') \
            .filter(
                submission_account__submission_account__iexact=self
                .request.user.username
            ) \
            .select_related('submission_account')

        serializer = self.get_serializer(submitter, many=True)
        return Response(serializer.data)

    @list_route(
        methods=['get', 'post', ],
        serializer_class=ena_serializers.NotifySerializer,
        permission_classes=[permissions.IsAuthenticated, emg_perms.IsSelf]
    )
    def notify(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                status_code = serializer.save()
                if status_code == 200:
                    return Response("Created", status=status.HTTP_201_CREATED)
            except Exception as e:
                logging.error(e, exc_info=True)
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                "Request cannot be processed.",
                status=status.HTTP_409_CONFLICT
            )
        return Response(serializer.errors)

    @list_route(
        methods=['get', 'post', ],
        serializer_class=ena_serializers.EmailSerializer,
        permission_classes=[permissions.IsAuthenticated, emg_perms.IsSelf]
    )
    def sendemail(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logging.error(e, exc_info=True)
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors)


class MyDataViewSet(emg_mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudySerializer
    permission_classes = (
        permissions.IsAuthenticated,
        emg_perms.IsSelf,
    )

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
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
        'centre_name',
        'project_id',
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
        '@biome_name',
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
            AND parent.BIOME_ID in %s
        GROUP BY parent.BIOME_ID
        ORDER BY samples_count DESC
        LIMIT 10;
        """

        queryset = list(
            emg_models.Biome.objects.raw(
                sql, [tuple(settings.TOP10BIOMES), ]))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudyViewSet(mixins.RetrieveModelMixin,
                   emg_mixins.ListModelMixin,
                   emg_viewsets.BaseStudyGenericViewSet):

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        queryset = emg_models.Study.objects.available(self.request)
        if 'samples' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Sample.objects \
                .available(self.request, prefetch=True)
            queryset = queryset.prefetch_related(
                Prefetch('samples', queryset=_qs)
            )
        if 'analysis' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.AnalysisJob.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('analysis', queryset=_qs)
            )
        if 'downloads' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.StudyDownload.objects.all()
            queryset = queryset.prefetch_related(
                Prefetch('study_download', queryset=_qs)
            )
        return queryset

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            *emg_utils.study_accession_query(self.kwargs['accession'])
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


class StudiesDownloadsViewSet(emg_mixins.ListModelMixin,
                              viewsets.GenericViewSet):

    serializer_class = emg_serializers.StudyDownloadSerializer

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

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
            Q(pipeline__release_version=self.kwargs['release_version']),
        )

    def get_serializer_class(self):
        return super(StudiesDownloadsViewSet, self).get_serializer_class()

    def list(self, request, accession, *args, **kwargs):
        """
        Retrieves list of static summary files
        Example:
        ---
        `/studies/ERP009004/downloads`
        """
        return super(StudiesDownloadsViewSet, self) \
            .list(request, *args, **kwargs)


class SampleViewSet(mixins.RetrieveModelMixin,
                    emg_mixins.ListModelMixin,
                    emg_viewsets.BaseSampleGenericViewSet):

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        queryset = emg_models.Sample.objects \
            .available(self.request, prefetch=True)
        if 'runs' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.Run.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('runs', queryset=_qs))
        if 'analysis' in self.request.GET.get('include', '').split(','):
            _qs = emg_models.AnalysisJob.objects.available(self.request)
            queryset = queryset.prefetch_related(
                Prefetch('analysis', queryset=_qs))
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

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        return emg_models.Run.objects.available(self.request)

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            Q(accession=self.kwargs['accession']) |
            Q(secondary_accession=self.kwargs['accession'])
        )

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


class AnalysisJobViewSet(mixins.RetrieveModelMixin,
                         emg_mixins.ListModelMixin,
                         emg_viewsets.BaseAnalysisGenericViewSet):

    lookup_field = 'accession'
    lookup_value_regex = '[^/]+'

    def get_serializer_class(self):
        return super(AnalysisJobViewSet, self).get_serializer_class()

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(self.get_queryset(), Q(pk=pk))

    def get_queryset(self):
        queryset = emg_models.AnalysisJob.objects \
            .available(self.request)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Retrieves analysis results for the given accession
        Example:
        ---
        `/analyses`
        """
        return super(AnalysisJobViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves analysis result for the given accession
        Example:
        ---
        `/analyses/MGYA00135572`
        """
        return super(AnalysisJobViewSet, self) \
            .retrieve(request, *args, **kwargs)


class AnalysisQCChartViewSet(emg_mixins.ListModelMixin,
                             viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    schema = None

    renderer_classes = (emg_renderers.TSVRenderer,)

    lookup_field = 'chart'
    lookup_value_regex = (
        'gc-distribution|'
        'nucleotide-distribution|'
        'seq-length|'
        'summary'
    )

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(self.get_queryset(), Q(pk=pk))

    def _build_path(self, name):
        return os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            self.get_object().result_directory,
            'qc-statistics', name))

    def retrieve(self, request, chart=None, **kwargs):
        """
        Retrieves krona chart for the given accession and pipeline version
        Example:
        ---
        `/analyses/MGYA00102827/gc-distribution`
        """
        mapping = {
            "gc-distribution": "GC-distribution",
            "nucleotide-distribution": "nucleotide-distribution",
            "seq-length": "seq-length",
            "summary": "summary",
        }
        filepath = self._build_path(
            "{name}.out".format(name=mapping[chart]))
        if not os.path.isfile(filepath):
            filepath = self._build_path(
                "{name}.out.full".format(name=mapping[chart]))
            if not os.path.isfile(filepath):
                filepath = self._build_path(
                    "{name}.out.sub-set".format(name=mapping[chart]))
        if os.path.isfile(filepath):
            logger.info("Path %r" % filepath)
            with open(filepath, "r") as f:
                return Response(f.read())
        raise Http404()


class KronaViewSet(emg_mixins.ListModelMixin,
                   viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    schema = None

    renderer_classes = (renderers.StaticHTMLRenderer,)

    lookup_field = 'subdir'
    lookup_value_regex = 'lsu|ssu'

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(self.get_queryset(), Q(pk=pk))

    def get_serializer_class(self):
        return super(KronaViewSet, self).get_serializer_class()

    @xframe_options_exempt
    def list(self, request, **kwargs):
        """
        Retrieves krona chart for the given accession and pipeline version
        Example:
        ---
        `/analyses/MGYA00102827/krona`
        """
        obj = self.get_object()
        krona = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            'taxonomy-summary',
            'krona.html')
        )
        logger.info(krona)
        if os.path.isfile(krona):
            with open(krona, "r") as k:
                return Response(k.read())
        raise Http404('No chrona chart.')

    @xframe_options_exempt
    def retrieve(self, request, subdir=None, **kwargs):
        """
        Retrieves krona chart for the given accession and pipeline version
        Example:
        ---
        `/runs/GCA_900216095/pipelines/4.0/krona/lsu`
        """
        obj = self.get_object()
        krona = os.path.abspath(os.path.join(
            settings.RESULTS_DIR,
            obj.result_directory,
            'taxonomy-summary',
            subdir.upper(),
            'krona.html')
        )
        logger.info(krona)
        if os.path.isfile(krona):
            with open(krona, "r") as k:
                return Response(k.read())
        raise Http404('No chrona chart.')


class AnalysisResultDownloadsViewSet(emg_mixins.ListModelMixin,
                                     viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisJobDownloadSerializer

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return emg_models.AnalysisJobDownload.objects.available(self.request) \
            .filter(job__pk=pk)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias']), Q(job__pk=pk)
        )

    def get_serializer_class(self):
        return super(AnalysisResultDownloadsViewSet, self) \
            .get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of static summary files
        Example:
        ---
        `/analyses/MGYA00102827/downloads`
        """
        return super(AnalysisResultDownloadsViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisResultDownloadViewSet(emg_mixins.MultipleFieldLookupMixin,
                                    mixins.RetrieveModelMixin,
                                    viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisJobDownloadSerializer

    lookup_field = 'alias'
    lookup_value_regex = '[^/]+'
    lookup_fields = ('accession', 'alias')

    def get_queryset(self):
        return emg_models.AnalysisJobDownload.objects.available(self.request)

    def get_object(self):
        try:
            pk = int(self.kwargs['accession'].lstrip('MGYA'))
        except ValueError:
            raise Http404()
        return get_object_or_404(
            self.get_queryset(), Q(alias=self.kwargs['alias']), Q(job__pk=pk)
        )

    def get_serializer_class(self):
        return super(AnalysisResultDownloadViewSet, self) \
            .get_serializer_class()

    def retrieve(self, request, accession, alias, *args, **kwargs):
        """
        Retrieves static summary file
        Example:
        ---
        `/analyses/MGYA00102827/file/
        ERR1701760_MERGED_FASTQ_otu_table_hdf5.biom`
        """
        obj = self.get_object()
        response = HttpResponse()
        response['Content-Type'] = 'application/octet-stream'
        response["Content-Disposition"] = \
            "attachment; filename={0}".format(alias)
        if obj.subdir is not None:
            response['X-Accel-Redirect'] = \
                "/results{0}/{1}/{2}".format(
                    obj.job.result_directory, obj.subdir, obj.realname
                )
        else:
            response['X-Accel-Redirect'] = \
                "/results{0}/{1}".format(
                    obj.job.result_directory, obj.realname
                )
        return response


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
    lookup_value_regex = '[^/]+'

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
    lookup_value_regex = '[^/]+'

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
                         emg_viewsets.BasePublicationGenericViewSet):

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

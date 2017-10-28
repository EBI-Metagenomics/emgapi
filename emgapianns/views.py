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

from mongoengine.queryset.visitor import Q

from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route

from rest_framework_mongoengine import viewsets as m_viewset

from emgapi import serializers as emg_serializers
from emgapi import models as emg_models
from emgapi import filters as emg_filters
from emgapi import mixins as emg_mixins
from emgapi import pagination as emg_page

from . import serializers as m_serializers
from . import models as m_models

logger = logging.getLogger(__name__)


class GoTermViewSet(m_viewset.ReadOnlyModelViewSet):

    """
    Provides list of GO terms.
    """

    serializer_class = m_serializers.GoTermSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'GO:[0-9]+'

    def get_queryset(self):
        return m_models.GoTerm.objects.all()

    def get_object(self):
        try:
            accession = self.kwargs[self.lookup_field]
            return m_models.GoTerm.objects.get(accession=accession)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except m_models.GoTerm.DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           m_models.GoTerm.__class__.__name__))

    def get_serializer_class(self):
        return super(GoTermViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of GO terms
        Example:
        ---
        `/annotations/go-terms`
        """
        return super(GoTermViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves GO term
        Example:
        ---
        `/annotations/go-terms/GO:009579`
        """
        return super(GoTermViewSet, self) \
            .retrieve(request, *args, **kwargs)


class InterproIdentifierViewSet(m_viewset.ReadOnlyModelViewSet):

    """
    Provides list of InterPro identifiers.
    """

    serializer_class = m_serializers.InterproIdentifierSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'IPR[0-9]+'

    def get_queryset(self):
        return m_models.InterproIdentifier.objects.all()

    def get_object(self):
        try:
            accession = self.kwargs[self.lookup_field]
            return m_models.InterproIdentifier.objects.get(accession=accession)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except m_models.InterproIdentifier.DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           m_models.GoTerm.__class__.__name__))

    def get_serializer_class(self):
        return super(InterproIdentifierViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier`
        """
        return super(InterproIdentifierViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier/IPR020405`
        """
        return super(InterproIdentifierViewSet, self) \
            .retrieve(request, *args, **kwargs)


class GoTermAnalysisRelationshipViewSet(mixins.ListModelMixin,
                                        viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    filter_class = emg_filters.AnalysisJobFilter

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
        '@sample__metadata__var_val_ucv',
    )

    lookup_field = 'accession'

    def get_queryset(self):
        return emg_models.AnalysisJob.objects.available(self.request)

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of analysis results for the given GO term
        Example:
        ---
        `/annotations/go-terms/GO:009579/analysis`
        """
        accession = self.kwargs[self.lookup_field]
        try:
            annotation = m_models.GoTerm.objects.get(accession=accession)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except m_models.GoTerm.DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           m_models.GoTerm.__class__.__name__))
        logger.info("get accession %s" % annotation.accession)
        job_ids = m_models.AnalysisJobGoTerm.objects \
            .filter(
                Q(go_slim__go_term=annotation) |
                Q(go_terms__go_term=annotation)
            ) \
            .only('job_id')
        logger.info("Found %d analysis" % len(job_ids))
        job_ids = [str(j.job_id) for j in job_ids]
        queryset = emg_models.AnalysisJob.objects \
            .filter(job_id__in=job_ids) \
            .available(self.request) \
            .prefetch_related(
                'sample',
                'analysis_status',
                'experiment_type',
                'pipeline'
            )
        page = self.paginate_queryset(self.filter_queryset(queryset))
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InterproIdentifierAnalysisRelationshipViewSet(mixins.ListModelMixin,
                                                    viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    filter_class = emg_filters.AnalysisJobFilter

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
        '@sample__metadata__var_val_ucv',
    )

    lookup_field = 'accession'

    def get_queryset(self):
        return emg_models.AnalysisJob.objects.available(self.request)

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of analysis results for the given InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier/IPR020405/analysis`
        """
        accession = self.kwargs[self.lookup_field]
        try:
            annotation = m_models.InterproIdentifier.objects \
                .get(accession=accession)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except m_models.InterproIdentifier.DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           m_models.InterproIdentifier.__class__.__name__))
        logger.info("get identifier %s" % annotation.accession)
        job_ids = m_models.AnalysisJobInterproIdentifier.objects \
            .filter(interpro_identifiers__interpro_identifier=annotation) \
            .only('job_id')
        logger.info("Found %d analysis" % len(job_ids))
        job_ids = [str(j.job_id) for j in job_ids]
        queryset = emg_models.AnalysisJob.objects \
            .filter(job_id__in=job_ids) \
            .available(self.request) \
            .prefetch_related(
                'sample',
                'analysis_status',
                'experiment_type',
                'pipeline'
            )
        page = self.paginate_queryset(self.filter_queryset(queryset))
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AnalysisGoTermRelationshipViewSet(emg_mixins.MultipleFieldLookupMixin,
                                        mixins.ListModelMixin,
                                        m_viewset.GenericViewSet):

    serializer_class = m_serializers.GoTermRetriveSerializer

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.AnalysisJob.objects.available(self.request)

    def list(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves GO terms for the given run and pipeline version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/go-terms`
        """

        job = get_object_or_404(
            emg_models.AnalysisJob, accession=accession,
            pipeline__release_version=release_version
        )

        analysis = None
        try:
            analysis = m_models.AnalysisJobGoTerm.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobGoTerm.DoesNotExist:
            pass

        ann_ids = list()
        ann_counts = dict()
        if analysis is not None:
            for a in analysis.go_terms:
                ann_ids.append(a.go_term.pk)
                ann_counts[a.go_term.pk] = a.count

        queryset = m_models.GoTerm.objects.filter(pk__in=ann_ids)

        page = self.paginate_queryset(queryset)
        for p in page:
            p.count = ann_counts[p.pk]
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class AnalysisGoSlimRelationshipViewSet(emg_mixins.MultipleFieldLookupMixin,
                                        mixins.ListModelMixin,
                                        m_viewset.GenericViewSet):

    serializer_class = m_serializers.GoTermRetriveSerializer

    pagination_class = emg_page.MaxSetPagination

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.AnalysisJob.objects.available(self.request)

    def list(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves GO slim for the given run and pipeline version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/go-slim`
        """

        job = get_object_or_404(
            emg_models.AnalysisJob, accession=accession,
            pipeline__release_version=release_version
        )

        analysis = None
        try:
            analysis = m_models.AnalysisJobGoTerm.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobGoTerm.DoesNotExist:
            pass

        ann_ids = list()
        ann_counts = dict()
        if analysis is not None:
            for a in analysis.go_slim:
                ann_ids.append(a.go_term.pk)
                ann_counts[a.go_term.pk] = a.count

        queryset = m_models.GoTerm.objects.filter(pk__in=ann_ids)

        page = self.paginate_queryset(queryset)
        for p in page:
            p.count = ann_counts[p.pk]
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class AnalysisInterproIdentifierRelationshipViewSet(  # NOQA
    emg_mixins.MultipleFieldLookupMixin,
    mixins.ListModelMixin, m_viewset.GenericViewSet):

    serializer_class = m_serializers.InterproIdentifierRetriveSerializer

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.AnalysisJob.objects.available(self.request)

    def list(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves InterPro identifiers for the given run and pipeline version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/interpro-identifiers`
        """

        job = get_object_or_404(
            emg_models.AnalysisJob, accession=accession,
            pipeline__release_version=release_version
        )

        analysis = None
        try:
            analysis = m_models.AnalysisJobInterproIdentifier.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobInterproIdentifier.DoesNotExist:
            pass

        ann_ids = []
        ann_counts = dict()
        if analysis is not None:
            for a in analysis.interpro_identifiers:
                ann_ids.append(a.interpro_identifier.pk)
                ann_counts[a.interpro_identifier.pk] = a.count

        queryset = m_models.InterproIdentifier.objects.filter(pk__in=ann_ids)

        page = self.paginate_queryset(queryset)
        for p in page:
            p.count = ann_counts[p.pk]
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class OrganismViewSet(m_viewset.ReadOnlyModelViewSet):

    """
    Provides list of Organisms.
    """

    serializer_class = m_serializers.OrganismSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'lineage'
    lookup_value_regex = '[a-zA-Z0-9\_\-\.\:\s]+'

    def get_queryset(self):
        return m_models.Organism.objects.all()

    def get_object(self):
        try:
            lineage = self.kwargs[self.lookup_field]
            return m_models.Organism.objects.get(lineage=lineage)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except m_models.Organism.DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           m_models.Organism.__class__.__name__))

    def get_serializer_class(self):
        return super(OrganismViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Organisms
        Example:
        ---
        `/annotations/organisms`
        """
        return super(OrganismViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves Organism
        Example:
        ---
        `/annotations/organisms/Bacteria:Chlorobi:OPB56`
        """
        return super(OrganismViewSet, self) \
            .retrieve(request, *args, **kwargs)


class OrganismTreeViewSet(mixins.ListModelMixin,
                          m_viewset.GenericViewSet):

    """
    Provides list of Organisms.
    """

    serializer_class = m_serializers.OrganismSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'domain',
        'prefix',
        'lineage',
    )

    lookup_field = 'lineage'
    lookup_value_regex = '[a-zA-Z0-9\_\-\:\s]+'

    def get_queryset(self):
        lineage = self.kwargs.get('lineage', None).strip()
        if lineage:
            try:
                organism = m_models.Organism.objects.get(lineage=lineage)
            except KeyError:
                raise Http404(("Attribute error '%s'." % self.lookup_field))
            except m_models.Organism.DoesNotExist:
                raise Http404(('No %s matches the given query.' %
                               m_models.Organism.__class__.__name__))
            queryset = m_models.Organism.objects \
                .filter(ancestors=organism.name)
        else:
            queryset = super(OrganismTreeViewSet, self).get_queryset()
        return queryset

    def get_serializer_class(self):
        return super(OrganismTreeViewSet, self).get_serializer_class()

    def get_serializer_context(self):
        context = super(OrganismTreeViewSet, self).get_serializer_context()
        context['lineage'] = self.kwargs.get('lineage')
        return context

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Organisms
        Example:
        ---
        `/annotations/organisms/Bacteria:Chlorobi/children`
        """
        return super(OrganismTreeViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisOrganismRelationshipViewSet(emg_mixins.MultipleFieldLookupMixin,
                                          mixins.ListModelMixin,
                                          m_viewset.GenericViewSet):

    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = emg_page.MaxSetPagination

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.AnalysisJob.objects.available(self.request)

    def list(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves 16SrRNA Taxonomic analysis for the given run and pipeline
        version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/taxonomy`
        """

        job = get_object_or_404(
            emg_models.AnalysisJob, accession=accession,
            pipeline__release_version=release_version
        )

        analysis = None
        try:
            analysis = m_models.AnalysisJobTaxonomy.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            pass

        ann_ids = list()
        ann_counts = dict()
        if analysis is not None:
            for a in getattr(analysis, 'taxonomy', []):
                ann_ids.append(a.organism.pk)
                ann_counts[a.organism.pk] = a.count

        queryset = m_models.Organism.objects.filter(pk__in=ann_ids)

        page = self.paginate_queryset(queryset)
        for p in page:
            p.count = ann_counts[p.pk]
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @list_route(
        methods=['get', ],
        serializer_class=m_serializers.OrganismRetriveSerializer
    )
    def ssu(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves SSU Taxonomic analysis for the given run and pipeline
        version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/taxonomy/ssu`
        """

        job = get_object_or_404(
            emg_models.AnalysisJob, accession=accession,
            pipeline__release_version=release_version
        )

        analysis = None
        try:
            analysis = m_models.AnalysisJobTaxonomy.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            pass

        ann_ids = list()
        ann_counts = dict()
        if analysis is not None:
            for a in getattr(analysis, 'taxonomy_ssu', []):
                ann_ids.append(a.organism.pk)
                ann_counts[a.organism.pk] = a.count

        queryset = m_models.Organism.objects.filter(pk__in=ann_ids)

        page = self.paginate_queryset(queryset)
        for p in page:
            p.count = ann_counts[p.pk]
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @list_route(
        methods=['get', ],
        serializer_class=m_serializers.OrganismRetriveSerializer
    )
    def lsu(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves LSU Taxonomic analysis for the given run and pipeline
        version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/taxonomy/lsu`
        """

        job = get_object_or_404(
            emg_models.AnalysisJob, accession=accession,
            pipeline__release_version=release_version
        )

        analysis = None
        try:
            analysis = m_models.AnalysisJobTaxonomy.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            pass

        ann_ids = list()
        ann_counts = dict()
        if analysis is not None:
            for a in getattr(analysis, 'taxonomy_lsu', []):
                ann_ids.append(a.organism.pk)
                ann_counts[a.organism.pk] = a.count

        queryset = m_models.Organism.objects.filter(pk__in=ann_ids)

        page = self.paginate_queryset(queryset)
        for p in page:
            p.count = ann_counts[p.pk]
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class OrganismAnalysisRelationshipViewSet(mixins.ListModelMixin,
                                          viewsets.GenericViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    filter_class = emg_filters.AnalysisJobFilter

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
        '@sample__metadata__var_val_ucv',
    )

    lookup_field = 'lineage'

    def get_queryset(self):
        return emg_models.AnalysisJob.objects.available(self.request)

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of analysis results for the given Organism
        Example:
        ---
        `/annotations/organisms/Bacteria:Chlorobi:OPB56/analysis`
        """
        lineage = self.kwargs[self.lookup_field]
        try:
            organism = m_models.Organism.objects \
                .get(lineage=lineage)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except m_models.Organism.DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           m_models.Organism.__class__.__name__))
        logger.info("get identifier %s" % organism.lineage)
        job_ids = m_models.AnalysisJobTaxonomy.objects \
            .filter(taxonomy__organism=organism) \
            .only('analysis_id')
        logger.info("Found %d analysis" % len(job_ids))
        job_ids = [str(j.analysis_id) for j in job_ids]
        queryset = emg_models.AnalysisJob.objects \
            .filter(job_id__in=job_ids) \
            .available(self.request) \
            .prefetch_related(
                'sample',
                'analysis_status',
                'experiment_type',
                'pipeline'
            )
        page = self.paginate_queryset(self.filter_queryset(queryset))
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

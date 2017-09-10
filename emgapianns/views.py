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

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, mixins, viewsets
from rest_framework.response import Response

from rest_framework_mongoengine import viewsets as m_viewset

from emgapi import serializers as emg_serializers
from emgapi import models as emg_models
from emgapi import filters as emg_filters
from emgapi import mixins as emg_mixins

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
        accession = self.kwargs[self.lookup_field]
        return get_object_or_404(
            m_models.GoTerm.objects, accession=accession)

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
        accession = self.kwargs[self.lookup_field]
        return get_object_or_404(
            m_models.InterproIdentifier.objects, accession=accession)

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
        accession = self.kwargs[self.lookup_field]
        annotation = get_object_or_404(
            m_models.GoTerm.objects, accession=accession)
        logger.info("get accession %s" % annotation.accession)
        job_ids = m_models.AnalysisJobGoTerm.objects \
            .filter(
                Q(go_slim__go_term=annotation) |
                Q(go_terms__go_term=annotation)
            ) \
            .only('job_id')
        logger.info("Found %d analysis" % len(job_ids))
        job_ids = [str(j.accession) for j in job_ids]
        queryset = emg_models.AnalysisJob.objects \
            .filter(accession__in=job_ids) \
            .available(self.request) \
            .select_related(
                'sample',
                'analysis_status',
                'experiment_type'
            )
        return queryset

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

    def list(self, request, accession, *args, **kwargs):
        """
        Retrieves list of analysis results for the given GO term
        Example:
        ---
        `/annotations/go-terms/GO:009579/analysis`
        """
        return super(GoTermAnalysisRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


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
        accession = self.kwargs[self.lookup_field]
        annotation = get_object_or_404(
            m_models.InterproIdentifier.objects, accession=accession)
        logger.info("get identifier %s" % annotation.accession)
        job_ids = m_models.AnalysisJobInterproIdentifier.objects \
            .filter(interpro_identifiers__interpro_identifier=annotation) \
            .only('job_id')
        logger.info("Found %d analysis" % len(job_ids))
        job_ids = [str(j.accession) for j in job_ids]
        queryset = emg_models.AnalysisJob.objects \
            .filter(accession__in=job_ids) \
            .available(self.request) \
            .select_related(
                'sample',
                'analysis_status',
                'experiment_type'
            )
        return queryset

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

    def list(self, request, accession, *args, **kwargs):
        """
        Retrieves list of analysis results for the given InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier/IPR020405/analysis`
        """
        return super(InterproIdentifierAnalysisRelationshipViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisGoTermRelationshipViewSet(emg_mixins.MultipleFieldLookupMixin,
                                        mixins.ListModelMixin,
                                        m_viewset.GenericViewSet):

    serializer_class = m_serializers.GoTermRetriveSerializer

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request) \
            .select_related(
                'sample',
                'pipeline',
                'analysis_status',
            )

    def list(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves GO terms for the given run and pipeline version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/go-terms`
        """

        analysis = m_models.AnalysisJobGoTerm.objects.filter(
            accession=accession, pipeline_version=release_version).first()

        ann_ids = []
        if analysis is not None:
            ann_ids = [a.go_term.pk for a in analysis.go_terms]
            ann_counts = {
                a.go_term.pk: a.count for a in analysis.go_terms
            }

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

    lookup_fields = ('accession', 'release_version')

    def get_queryset(self):
        return emg_models.AnalysisJob.objects \
            .available(self.request) \
            .select_related(
                'sample',
                'pipeline',
                'analysis_status',
            )

    def list(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves GO slim for the given run and pipeline version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/go-slim`
        """

        analysis = m_models.AnalysisJobGoTerm.objects.filter(
            accession=accession, pipeline_version=release_version).first()

        ann_ids = []
        if analysis is not None:
            ann_ids = [a.go_term.pk for a in analysis.go_slim]
            ann_counts = {
                a.go_term.pk: a.count for a in analysis.go_slim
            }

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
        return emg_models.AnalysisJob.objects \
            .available(self.request) \
            .select_related(
                'sample',
                'pipeline',
                'analysis_status',
            )

    def list(self, request, accession, release_version, *args, **kwargs):
        """
        Retrieves InterPro identifiers for the given run and pipeline version
        Example:
        ---
        `/runs/ERR1385375/pipelines/3.0/interpro-identifiers`
        """

        analysis = m_models.AnalysisJobInterproIdentifier.objects.filter(
            accession=accession, pipeline_version=release_version).first()

        ann_ids = []
        if analysis is not None:
            ann_ids = [a.interpro_identifier.pk for a in analysis.interpro_identifiers]  # NOQA
            ann_counts = {
                a.interpro_identifier.pk: a.count for a in analysis.interpro_identifiers  # NOQA
            }

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

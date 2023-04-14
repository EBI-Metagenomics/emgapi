#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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

from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import mixins
from rest_framework import filters

from rest_framework_mongoengine.viewsets import GenericViewSet

from emgapi import mixins as emg_mixins
from emgapi import serializers as emg_serializers
from emgapi import models as emg_models
from emgapi import filters as emg_filters

from mongoengine import DoesNotExist


class ReadOnlyModelViewSet(mixins.RetrieveModelMixin,
                           emg_mixins.ListModelMixin,
                           GenericViewSet):
    """ Adaptation of DRF ReadOnlyModelViewSet """
    pass


class MultipleFieldLookupModelViewSet(emg_mixins.MultipleFieldLookupMixin,
                                      emg_mixins.ListModelMixin,
                                      GenericViewSet):
    """ Adaptation of DRF ReadOnlyModelViewSet """
    pass


class ListReadOnlyModelViewSet(emg_mixins.ListModelMixin,
                               GenericViewSet):
    """ Adaptation of DRF ReadOnlyModelViewSet """
    pass


class AnalysisRelationshipViewSet(ListReadOnlyModelViewSet):
    """Get the the Analysis that have a particular Model

    This mixin provides abstracts the common code to get the Analysis that have a
    particular annotation.

    For example: get all the analysis that have the Pfam entry X.

    Usage:
        `annotation_model`: annotation mongo model
        `get_job_ids`: method to get all the jobs that have a particular annotation
    """
    serializer_class = emg_serializers.AnalysisSerializer

    filterset_class = emg_filters.AnalysisJobFilter

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
        'sample__metadata__var_val_ucv',
    )

    lookup_field = 'accession'

    annotation_model = None

    def get_job_ids(self):
        pass

    def get_queryset(self):
        accession = self.kwargs[self.lookup_field]
        try:
            annotation = self.annotation_model.objects.get(accession=accession)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           self.annotation_model.__class__.__name__))

        job_ids = self.get_job_ids(annotation)

        return emg_models.AnalysisJob.objects \
            .filter(job_id__in=job_ids) \
            .available(self.request)

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

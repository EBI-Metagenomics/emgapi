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

from rest_framework.response import Response
from rest_framework.decorators import detail_route

from rest_framework_mongoengine import viewsets

from emgapi import serializers as emg_serializers
from emgapi import models as emg_models

from . import serializers as m_serializers
from . import models as m_models


class AnnotationViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = m_serializers.AnnotationSerializer

    lookup_field = 'accession'
    lookup_value_regex = '[a-zA-Z0-9]+'

    def get_queryset(self):
        return m_models.Annotation.objects.all()

    def get_serializer_class(self):
        return super(AnnotationViewSet, self).get_serializer_class()

    @detail_route(
        methods=['get', ],
        url_name='runs-list',
        serializer_class=emg_serializers.RunSerializer
    )
    def runs(self, request, accession=None):
        """
        Retrieves list of runs for the given sample accession
        Example:
        ---
        `/api/annotations/GO0001/runs`
        """
        run_ids = m_models.Annotation.objects \
            .filter(accession=accession).values_list('run_accession')
        queryset = emg_models.Run.objects.filter(accession__in=run_ids) \
            .available(self.request) \
            .select_related(
                'sample',
                'analysis_status',
                'experiment_type'
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)

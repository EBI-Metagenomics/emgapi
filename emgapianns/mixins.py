#!/usr/bin/env python
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

from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import filters

from emgapi import models as emg_models

from . import serializers as m_serializers
from . import models as m_models
from . import pagination as m_page


class AnalysisJobTaxonomyViewSetMixin():
    """Get the taxonomy information for an analysis from Mongo.
    There are 4 possible set of results: SSU, LSU, ITSOneDB and UNITE(ITS).
    
    The field property is required, possible values:
    - taxonomy
    - taxonomy_ssu
    - taxonomu_lsu
    - taxonomy_itsonedb
    - taxonomy_itsunite

    This corresponds to the model fields (AnalysisJobTaxonomy)
    """
    taxonomy_field = None

    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'accession'

    def get_queryset(self):
        """Get the AnalysisJob and then the AnalysisJobTaxonomy
        """
        job = get_object_or_404(
            emg_models.AnalysisJob,
            Q(pk=int(self.kwargs['accession'].lstrip('MGYA')))
        )
        analysis = None
        try:
            analysis = m_models.AnalysisJobTaxonomy.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            pass

        return getattr(analysis, self.taxonomy_field, [])
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
import collections

from django.http import Http404

from rest_framework.response import Response
from rest_framework import generics

from emgapi import models as emg_models

from . import models as m_models

logger = logging.getLogger(__name__)


class AnnotationMetadataAPIView(generics.ListAPIView,
                                generics.GenericAPIView):

    lookup_field = ('accession')

    def get_queryset(self):
        pass

    def get_serializer_class(self):
        pass

    def list(self, request, *args, **kwargs):
        """
        Example:
        ---
        `/annotations/metadata?accession=ERP001736&metadata=temperature`
        """

        # query string parameters
        accession = self.request.query_params.get('accession', None)
        key = self.request.query_params.get('key', None)

        try:
            study = emg_models.Study.objects.get(accession=accession)
        except emg_models.Study.DoesNotExist:
            raise Http404("Object does not exist")

        _run_meta_mapping = {}
        _run_metadata_list = emg_models.Run.objects.filter(
            sample__study=study, sample__metadata__var__var_name=key) \
            .values(
                'accession',
                'sample__metadata__var__var_name',
                'sample__metadata__var_val_ucv'
            )

        for r in _run_metadata_list:
            _run_meta_mapping[r['accession']] = \
                r['sample__metadata__var_val_ucv']
        result = {}

        annalysis_ids = list(_run_meta_mapping)
        m_analysis = m_models.AnalysisJob.objects.filter(
            pk__in=annalysis_ids)
        logger.debug("%d = %d" % (len(annalysis_ids), len(m_analysis)))

        result = {}
        for analysis in m_analysis:
            _accession = analysis.accession
            _key = _run_meta_mapping[_accession]

            try:
                result[_key]
            except KeyError:
                result[_key] = {}

            for ann in analysis.annotations:
                a = ann.annotation
                count = ann.count

                try:
                    result[_key][a.accession]
                except KeyError:
                    result[_key][a.accession] = list()
                result[_key][a.accession] \
                    .append({_accession: count})

        result = collections.OrderedDict(sorted(result.items()))

        return Response(result)

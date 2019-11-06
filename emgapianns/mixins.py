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

from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404

from emgapi import models as emg_models


class AnalysisJobAnnotationMixin:
    """Analysis Job Annotation Mixin.
    This mixin povides a basic get_queryset that will get an AnalysisJobAnnotation
    and will return the defined property from the Mongo model (annotation_model)

    Usage:
        `annotation_model`: class to be used (the mongo model)
        `annotation_model_property`: field within the class to get the data
        `analysis_job_filters`: an Q object to use to filter the AnalysisJob query
    """
    annotation_model = None
    annotation_model_property = None
    analysis_job_filters = None

    def get_queryset(self):
        """Get the AnalysisJob Annotation corresponding property from Mongo.
        """
        acc = self.kwargs['accession'].lstrip('MGYA')
        job_query = Q(pk=acc)

        if self.analysis_job_filters:
            job_query &= self.analysis_job_filters

        job = get_object_or_404(emg_models.AnalysisJob, job_query)

        analysis = None
        try:
            analysis = self.annotation_model.objects \
                    .get(analysis_id=str(job.job_id))
        except self.annotation_model.DoesNotExist:
            # Return an empty list, the entity exists
            # but it doesn't have annotations
            return []

        return getattr(analysis, self.annotation_model_property, [])


class AnnotationRetrivalMixin:
    """Basic annotation retrival mixin
    """

    annotation_model = None

    def get_queryset(self):
        return self.annotation_model.objects.all()

    def get_object(self):
        try:
            accession = self.kwargs[self.lookup_field]
            return self.annotation_model.objects.get(accession=accession)
        except KeyError:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        except self.annotation_model.DoesNotExist:
            raise Http404(('No %s matches the given query.' %
                           self.annotation_model.__class__.__name__))

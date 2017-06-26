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


import django_filters

from emg_api import models as emg_models


class SampleFilter(django_filters.FilterSet):

    analysis_status_id = django_filters.CharFilter(
        name='runs__analysis_status_id',
        distinct=True)

    experiment_type_id = django_filters.CharFilter(
        name='runs__experiment_type_id',
        distinct=True)

    analysis_status = django_filters.CharFilter(
        name='runs__analysis_status__analysis_status',
        distinct=True)

    experiment_type = django_filters.CharFilter(
        name='runs__experiment_type__experiment_type',
        distinct=True)

    class Meta:
        model = emg_models.Sample
        fields = (
            'analysis_status',
            'experiment_type',
            'analysis_status_id',
            'experiment_type_id',
            'biome_id',
            'geo_loc_name',
        )


class PipelineReleaseFilter(SampleFilter):

    class Meta:
        model = emg_models.PipelineRelease
        fields = (
            'analysis_status',
            'experiment_type',
            'analysis_status_id',
            'experiment_type_id',
        )


class RunFilter(django_filters.FilterSet):

    analysis_status_id = django_filters.CharFilter(
        name='analysis_status_id',
        distinct=True)

    experiment_type_id = django_filters.CharFilter(
        name='experiment_type_id',
        distinct=True)

    analysis_status = django_filters.CharFilter(
        name='analysis_status__analysis_status',
        distinct=True)

    experiment_type = django_filters.CharFilter(
        name='experiment_type__experiment_type',
        distinct=True)

    pipeline_version = django_filters.CharFilter(
        name='pipeline__release_version',
        distinct=True)

    class Meta:
        model = emg_models.Run
        fields = (
            'analysis_status',
            'experiment_type',
            'analysis_status_id',
            'experiment_type_id',
            'pipeline_version',
        )

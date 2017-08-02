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

from django.shortcuts import get_object_or_404

from . import models as emg_models


class PublicationFilter(django_filters.FilterSet):

    data_origination = django_filters.CharFilter(
        name='studies__data_origination',
        distinct=True)

    class Meta:
        model = emg_models.Publication
        fields = (
            'data_origination',
        )


class StudyFilter(django_filters.FilterSet):

    biome = django_filters.CharFilter(method='filter_biome', distinct=True)

    def filter_biome(self, qs, name, value):
        b = get_object_or_404(emg_models.Biome, lineage=value)
        return qs.filter(biome__lft__gte=b.lft-1, biome__rgt__lte=b.rgt+1)

    biome_name = django_filters.CharFilter(
        name='biome__biome_name',
        distinct=True)

    # species = django_filters.CharFilter(
    #     name='samples__species',
    #     distinct=True)

    class Meta:
        model = emg_models.Study
        fields = (
            'biome',
            'biome_name',
            'project_id',
            # 'species',
            'centre_name',
        )


class SampleFilter(django_filters.FilterSet):

    experiment_type = django_filters.CharFilter(
        name='runs__experiment_type__experiment_type',
        distinct=True)

    pipeline_version = django_filters.CharFilter(
        name='runs__pipeline__release_version',
        distinct=True)

    biome = django_filters.CharFilter(method='filter_biome', distinct=True)

    def filter_biome(self, qs, name, value):
        b = get_object_or_404(emg_models.Biome, lineage=value)
        return qs.filter(biome__lft__gte=b.lft-1, biome__rgt__lte=b.rgt+1)

    biome_name = django_filters.CharFilter(
        name='biome__biome_name',
        distinct=True)

    instrument_model = django_filters.CharFilter(
        name='runs__instrument_platform',
        distinct=True)

    instrument_platform = django_filters.CharFilter(
        name='runs__instrument_model',
        distinct=True)

    metadata_key = django_filters.CharFilter(
        name='metadata__var__var_name',
        distinct=True)

    metadata_value = django_filters.CharFilter(
        name='metadata__var_val_ucv',
        distinct=True)

    class Meta:
        model = emg_models.Sample
        fields = (
            'experiment_type',
            'biome',
            'biome_name',
            # 'pipeline_version',
            'geo_loc_name',
            'species',
            'instrument_model',
            'instrument_platform',
            'metadata_key',
            'metadata_value',
        )


class PipelineFilter(django_filters.FilterSet):

    experiment_type = django_filters.CharFilter(
        name='runs__experiment_type__experiment_type',
        distinct=True)

    class Meta:
        model = emg_models.Pipeline
        fields = (
            'experiment_type',
        )


class RunFilter(django_filters.FilterSet):

    analysis_status = django_filters.CharFilter(
        name='analysis_status__analysis_status',
        distinct=True)

    experiment_type = django_filters.CharFilter(
        name='experiment_type__experiment_type',
        distinct=True)

    pipeline_version = django_filters.CharFilter(
        name='pipeline__release_version',
        distinct=True)

    biome = django_filters.CharFilter(method='filter_biome', distinct=True)

    def filter_biome(self, qs, name, value):
        b = get_object_or_404(emg_models.Biome, lineage=value)
        return qs.filter(
            sample__biome__lft__gte=b.lft-1,
            sample__biome__rgt__lte=b.rgt+1)

    biome_name = django_filters.CharFilter(
        name='sample__biome__biome_name',
        distinct=True)

    class Meta:
        model = emg_models.Run
        fields = (
            'biome',
            'biome_name',
            'analysis_status',
            'experiment_type',
            # 'pipeline_version',
            'instrument_platform',
            'instrument_model',
        )

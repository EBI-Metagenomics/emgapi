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

from . import models as emg_models

WORD_MATCH_REGEX = r"{0}"


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
        try:
            b = emg_models.Biome.objects.get(lineage=value)
            qs = qs.filter(
                samples__biome__lft__gte=b.lft-1,
                samples__biome__rgt__lte=b.rgt+1)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    other_accession = django_filters.CharFilter(
        name='project_id',
        distinct=True)

    centre_name = django_filters.CharFilter(
        method='filter_centre_name', distinct=True)

    def filter_centre_name(self, qs, name, value):
        return qs.filter(
            centre_name__iregex=WORD_MATCH_REGEX.format(value))

    class Meta:
        model = emg_models.Study
        fields = (
            'biome',
            'project_id',
            'centre_name',
            'other_accession',
        )


class SampleFilter(django_filters.FilterSet):

    experiment_type = django_filters.CharFilter(
        name='runs__experiment_type__experiment_type',
        distinct=True)

    # pipeline_version = django_filters.CharFilter(
    #     name='runs__pipeline__release_version',
    #     distinct=True)

    biome = django_filters.CharFilter(method='filter_biome', distinct=True)

    def filter_biome(self, qs, name, value):
        try:
            b = emg_models.Biome.objects.get(lineage=value)
            qs = qs.filter(biome__lft__gte=b.lft-1, biome__rgt__lte=b.rgt+1)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    instrument_platform = django_filters.CharFilter(
        method='filter_instrument_platform', distinct=True)

    def filter_instrument_platform(self, qs, name, value):
        samples = emg_models.Run.objects.values('sample_id') \
            .available(self.request) \
            .filter(instrument_platform__iregex=WORD_MATCH_REGEX.format(value))
        return qs.filter(pk__in=samples).select_related('study', 'biome')

    instrument_model = django_filters.CharFilter(
        method='filter_instrument_model', distinct=True)

    def filter_instrument_model(self, qs, name, value):
        samples = emg_models.Run.objects.values('sample_id') \
            .available(self.request) \
            .filter(instrument_model__iregex=WORD_MATCH_REGEX.format(value))
        return qs.filter(pk__in=samples).select_related('study', 'biome')

    metadata_key = django_filters.CharFilter(
        method='filter_metadata_key', distinct=True)

    def filter_metadata_key(self, qs, name, value):
        return qs.filter(
            metadata__var__var_name__iregex=WORD_MATCH_REGEX.format(value))

    metadata_value = django_filters.CharFilter(
        method='filter_metadata_value', distinct=True)

    def filter_metadata_value(self, qs, name, value):
        return qs.filter(
            metadata__var_val_ucv__iregex=WORD_MATCH_REGEX.format(value))

    other_accession = django_filters.CharFilter(
        name='study__project_id',
        distinct=True)

    species = django_filters.CharFilter(method='filter_species', distinct=True)

    def filter_species(self, qs, name, value):
        return qs.filter(species__iregex=WORD_MATCH_REGEX.format(value))

    geo_loc_name = django_filters.CharFilter(
        method='filter_geo_loc_name', distinct=True)

    def filter_geo_loc_name(self, qs, name, value):
        return qs.filter(geo_loc_name__iregex=WORD_MATCH_REGEX.format(value))

    study_accession = django_filters.CharFilter(
        method='filter_study_accession', distinct=True)

    def filter_study_accession(self, qs, name, value):
        return qs.filter(
            study__accession__iregex=WORD_MATCH_REGEX.format(value))

    class Meta:
        model = emg_models.Sample
        fields = (
            'experiment_type',
            'biome',
            # 'pipeline_version',
            'geo_loc_name',
            'species',
            'instrument_model',
            'instrument_platform',
            'metadata_key',
            'metadata_value',
            'other_accession',
            'study_accession'
        )


class RunFilter(django_filters.FilterSet):

    analysis_status = django_filters.CharFilter(
        name='analysis_status__analysis_status',
        distinct=True)

    experiment_type = django_filters.CharFilter(
        name='experiment_type__experiment_type',
        distinct=True)

    # pipeline_version = django_filters.CharFilter(
    #     name='pipeline__release_version',
    #     distinct=True)

    biome = django_filters.CharFilter(method='filter_biome', distinct=True)

    def filter_biome(self, qs, name, value):
        try:
            b = emg_models.Biome.objects.get(lineage=value)
            qs = qs.filter(
                sample__biome__lft__gte=b.lft-1,
                sample__biome__rgt__lte=b.rgt+1)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    biome_name = django_filters.CharFilter(
        name='sample__biome__biome_name',
        distinct=True)

    species = django_filters.CharFilter(method='filter_species', distinct=True)

    def filter_species(self, qs, name, value):
        return qs.filter(
            sample__species__iregex=WORD_MATCH_REGEX.format(value))

    instrument_platform = django_filters.CharFilter(
        method='filter_instrument_platform', distinct=True)

    def filter_instrument_platform(self, qs, name, value):
        return qs.filter(
            instrument_platform__iregex=WORD_MATCH_REGEX.format(value))

    instrument_model = django_filters.CharFilter(
        method='filter_instrument_model', distinct=True)

    def filter_instrument_model(self, qs, name, value):
        return qs.filter(
            instrument_model__iregex=WORD_MATCH_REGEX.format(value))

    sample_accession = django_filters.CharFilter(
        method='filter_sample_accession', distinct=True)

    def filter_sample_accession(self, qs, name, value):
        return qs.filter(
            sample__accession__iregex=WORD_MATCH_REGEX.format(value))

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
            'species',
            'sample_accession',
        )

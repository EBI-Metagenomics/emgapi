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
from django_filters import filters

from . import models as emg_models

WORD_MATCH_REGEX = r"{0}"


def published_year():
    years = emg_models.Publication.objects \
        .filter(published_year__isnull=False, published_year__gt=0) \
        .order_by('published_year') \
        .values('published_year').distinct()
    return [(y['published_year'], y['published_year']) for y in years]


def metadata_keywords():
    keywords = emg_models.VariableNames.objects.all() \
        .order_by('var_name') \
        .values('var_name').distinct()
    return [(k['var_name'], k['var_name']) for k in keywords]


class PublicationFilter(django_filters.FilterSet):

    doi = django_filters.CharFilter(
        name='doi', distinct=True,
        label='DOI', help_text='DOI')

    isbn = django_filters.CharFilter(
        name='isbn', distinct=True,
        label='ISBN', help_text='ISBN')

    published_year = filters.ChoiceFilter(
        choices=published_year(),
        name='published_year', distinct=True,
        label='Published year', help_text='Published year')

    class Meta:
        model = emg_models.Publication
        fields = (
            'doi',
            'isbn',
            'published_year',
        )


class BiomeFilter(django_filters.FilterSet):

    depth_gte = filters.NumberFilter(
        name='depth', lookup_expr='gte',
        label='Depth, greater/equal then',
        help_text='Biome depth, greater/equal then')
    depth_lte = filters.NumberFilter(
        name='depth', lookup_expr='lte',
        label='Depth, less/equal then',
        help_text='Biome depth, less/equal then')

    class Meta:
        model = emg_models.Biome
        fields = (
            'depth_gte',
            'depth_lte',
        )


class StudyFilter(django_filters.FilterSet):

    lineage = filters.ModelChoiceFilter(
        queryset=emg_models.Biome.objects.all(),
        method='filter_lineage', distinct=True,
        to_field_name='lineage',
        label='Biome lineage',
        help_text='Biome lineage')

    def filter_lineage(self, qs, name, value):
        try:
            b = emg_models.Biome.objects.get(lineage=value)
            studies = emg_models.Sample.objects.values('study') \
                .available(self.request) \
                .filter(
                    biome__lft__gte=b.lft,
                    biome__rgt__lte=b.rgt)
            qs = qs.filter(pk__in=studies)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    biome_name = django_filters.CharFilter(
        method='filter_biome_name', distinct=True,
        label='Biome name',
        help_text='Biome name')

    def filter_biome_name(self, qs, name, value):
        try:
            biome_ids = emg_models.Biome.objects.filter(
                lineage__iregex=WORD_MATCH_REGEX.format(value)) \
                .values('biome_id')
            studies = emg_models.Sample.objects.values('study') \
                .available(self.request) \
                .filter(biome__biome_id__in=biome_ids)
            qs = qs.filter(pk__in=studies)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    other_accession = django_filters.CharFilter(
        name='project_id', distinct=True,
        label='ENA accession',
        help_text='ENA accession')

    centre_name = django_filters.CharFilter(
        method='filter_centre_name', distinct=True,
        label='Centre name',
        help_text='Centre name')

    def filter_centre_name(self, qs, name, value):
        return qs.filter(
            centre_name__iregex=WORD_MATCH_REGEX.format(value))

    class Meta:
        model = emg_models.Study
        fields = (
            'biome_name',
            'lineage',
            'centre_name',
            'other_accession',
        )


class SampleFilter(django_filters.FilterSet):

    experiment_type = filters.ModelChoiceFilter(
        queryset=emg_models.ExperimentType.objects.all(),
        to_field_name='experiment_type',
        method='filter_experiment_type', distinct=True,
        label='Experiment type',
        help_text='Experiment type')

    def filter_experiment_type(self, qs, name, value):
        try:
            analysis = emg_models.AnalysisJob.objects \
                .filter(experiment_type__experiment_type=value) \
                .values('sample')
            qs = qs.filter(pk__in=analysis)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    biome_name = django_filters.CharFilter(
        method='filter_biome_name', distinct=True,
        label='Biome name',
        help_text='Biome name')

    def filter_biome_name(self, qs, name, value):
        return qs.filter(
            biome__lineage__iregex=WORD_MATCH_REGEX.format(value))

    lineage = filters.ModelChoiceFilter(
        queryset=emg_models.Biome.objects.all(),
        method='filter_lineage', distinct=True,
        to_field_name='lineage',
        label='Biome lineage',
        help_text='Biome lineage')

    def filter_lineage(self, qs, name, value):
        try:
            b = emg_models.Biome.objects.get(lineage=value)
            qs = qs.filter(biome__lft__gte=b.lft, biome__rgt__lte=b.rgt)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    instrument_platform = django_filters.CharFilter(
        method='filter_instrument_platform', distinct=True,
        label='Instrument platform',
        help_text='Instrument platform')

    def filter_instrument_platform(self, qs, name, value):
        samples = emg_models.Run.objects.values('sample_id') \
            .available(self.request) \
            .filter(instrument_platform__iregex=WORD_MATCH_REGEX.format(value))
        return qs.filter(pk__in=samples).select_related('study', 'biome')

    instrument_model = django_filters.CharFilter(
        method='filter_instrument_model', distinct=True,
        label='Instrument model',
        help_text='Instrument model')

    def filter_instrument_model(self, qs, name, value):
        samples = emg_models.Run.objects.values('sample_id') \
            .available(self.request) \
            .filter(instrument_model__iregex=WORD_MATCH_REGEX.format(value))
        return qs.filter(pk__in=samples).select_related('study', 'biome')

    metadata_key = filters.ChoiceFilter(
            choices=metadata_keywords(),
            method='filter_metadata_key',
            name='metadata_key', distinct=True,
            label='Metadata keyword', help_text='Metadata keyword')

    def filter_metadata_key(self, qs, name, value):
        m = emg_models.VariableNames.objects.filter(
            var_name__iregex=WORD_MATCH_REGEX.format(value))
        return qs.filter(metadata__var__in=m)

    metadata_value_gte = django_filters.CharFilter(
        method='filter_metadata_value_gte', distinct=True,
        label='Metadata value',
        help_text='Metadata greater/equal then value')

    def filter_metadata_value_gte(self, qs, name, value):
        return qs.filter(
            metadata__var_val_ucv__gte=value)

    metadata_value_lte = django_filters.CharFilter(
        method='filter_metadata_value_lte', distinct=True,
        label='Metadata value',
        help_text='Metadata less/equal then value')

    def filter_metadata_value_lte(self, qs, name, value):
        return qs.filter(
            metadata__var_val_ucv__lte=value)

    metadata_value = django_filters.CharFilter(
        method='filter_metadata_value', distinct=True,
        label='Metadata value',
        help_text='Metadata exact value')

    def filter_metadata_value(self, qs, name, value):
        return qs.filter(
            metadata__var_val_ucv=value)

    other_accession = django_filters.CharFilter(
        name='study__project_id', distinct=True,
        label='ENA accession',
        help_text='ENA accession')

    species = django_filters.CharFilter(
        method='filter_species', distinct=True,
        label='Species',
        help_text='Species')

    def filter_species(self, qs, name, value):
        return qs.filter(species__iregex=WORD_MATCH_REGEX.format(value))

    geo_loc_name = django_filters.CharFilter(
        method='filter_geo_loc_name', distinct=True,
        label='Geological location name',
        help_text='Geological location name')

    def filter_geo_loc_name(self, qs, name, value):
        return qs.filter(geo_loc_name__iregex=WORD_MATCH_REGEX.format(value))

    study_accession = django_filters.CharFilter(
        method='filter_study_accession', distinct=True,
        label='Study accession',
        help_text='Study accession')

    def filter_study_accession(self, qs, name, value):
        return qs.filter(study__accession=value)

    class Meta:
        model = emg_models.Sample
        fields = (
            'experiment_type',
            'biome_name',
            'lineage',
            'geo_loc_name',
            'species',
            'instrument_model',
            'instrument_platform',
            'metadata_key',
            'metadata_value_gte',
            'metadata_value_lte',
            'metadata_value',
            'other_accession',
            'environment_material',
            'environment_feature',
            'study_accession',
        )


class RunFilter(django_filters.FilterSet):

    experiment_type = filters.ModelChoiceFilter(
        queryset=emg_models.ExperimentType.objects.all(),
        to_field_name='experiment_type',
        method='filter_experiment_type', distinct=True,
        label='Experiment type',
        help_text='Experiment type')

    def filter_experiment_type(self, qs, name, value):
        return qs.filter(
            experiment_type__experiment_type__iregex=WORD_MATCH_REGEX.format(value)  # NOQA
            )

    biome_name = django_filters.CharFilter(
        method='filter_biome_name', distinct=True,
        label='Biome name',
        help_text='Biome name')

    def filter_biome_name(self, qs, name, value):
        return qs.filter(
            sample__lineage__iregex=WORD_MATCH_REGEX.format(value))

    lineage = filters.ModelChoiceFilter(
        queryset=emg_models.Biome.objects.all(),
        method='filter_lineage', distinct=True,
        to_field_name='lineage',
        label='Biome lineage',
        help_text='Biome lineage')

    def filter_lineage(self, qs, name, value):
        try:
            b = emg_models.Biome.objects.get(lineage=value)
            qs = qs.filter(
                sample__biome__lft__gte=b.lft,
                sample__biome__rgt__lte=b.rgt)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    species = django_filters.CharFilter(
        method='filter_species', distinct=True,
        label='Species',
        help_text='Species')

    def filter_species(self, qs, name, value):
        return qs.filter(
            sample__species__iregex=WORD_MATCH_REGEX.format(value))

    instrument_platform = django_filters.CharFilter(
        method='filter_instrument_platform', distinct=True,
        label='Instrument platform',
        help_text='Instrument platform')

    def filter_instrument_platform(self, qs, name, value):
        return qs.filter(
            instrument_platform__iregex=WORD_MATCH_REGEX.format(value))

    instrument_model = django_filters.CharFilter(
        method='filter_instrument_model', distinct=True,
        label='Instrument model',
        help_text='Instrument model')

    def filter_instrument_model(self, qs, name, value):
        return qs.filter(
            instrument_model__iregex=WORD_MATCH_REGEX.format(value))

    sample_accession = django_filters.CharFilter(
        method='filter_sample_accession', distinct=True,
        label='Sample accession',
        help_text='Sample accession')

    def filter_sample_accession(self, qs, name, value):
        return qs.filter(sample__accession=value)

    study_accession = django_filters.CharFilter(
        method='filter_study_accession', distinct=True,
        label='Study accession',
        help_text='Study accession')

    def filter_study_accession(self, qs, name, value):
        return qs.filter(sample__study__accession=value)

    class Meta:
        model = emg_models.Run
        fields = (
            'biome_name',
            'lineage',
            'experiment_type',
            'instrument_platform',
            'instrument_model',
            'species',
            'sample_accession',
        )

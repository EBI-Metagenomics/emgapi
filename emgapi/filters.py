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
import re
from decimal import Decimal

from django import forms
from django.db.models import Q
from django.db.models import FloatField
from django.db.models.functions import Cast
from django.utils.datastructures import MultiValueDict
# from django.utils.six import string_types

import django_filters
from django_filters import filters
from django_filters import widgets

from . import models as emg_models
from . import utils as emg_utils

from rest_framework import filters as drf_filters

from rest_framework_json_api import filters as drfja_filters

WORD_MATCH_REGEX = r"{0}"
FLOAT_MATCH_REGEX = r"^[0-9 \.\,]+$"


def published_year():
    try:
        years = emg_models.Publication.objects \
            .filter(published_year__isnull=False, published_year__gt=0) \
            .order_by('published_year') \
            .values('published_year').distinct()
        return [(y['published_year'], y['published_year']) for y in years]
    except:  # noqa: E722
        return []


def metadata_keywords():
    try:
        keywords = emg_models.VariableNames.objects.all() \
            .order_by('var_name') \
            .values('var_name').distinct()
        return [(k['var_name'], k['var_name']) for k in keywords]
    except:  # noqa: E722
        return []


def pipeline_version():
    try:
        pipelines = emg_models.Pipeline.objects.all() \
            .order_by('release_version').distinct()
        return [(p.release_version, p.release_version) for p in pipelines]
    except:  # noqa: E722
        return []


class PublicationFilter(django_filters.FilterSet):

    doi = django_filters.CharFilter(
        field_name='doi', distinct=True,
        label='DOI', help_text='DOI')

    isbn = django_filters.CharFilter(
        field_name='isbn', distinct=True,
        label='ISBN', help_text='ISBN')

    published_year = filters.ChoiceFilter(
        choices=published_year,
        field_name='published_year', distinct=True,
        label='Published year', help_text='Published year')

    # include
    include = django_filters.CharFilter(
        method='filter_include', distinct=True,
        label='Include',
        help_text='Include related studies in the same response')

    def filter_include(self, qs, name, value):
        return qs

    class Meta:
        model = emg_models.Publication
        fields = (
            'doi',
            'isbn',
            'published_year',
            'include',
        )


class JsonApiPlusSearchQueryParameterValidationFilter(drfja_filters.QueryParameterValidationFilter):
    """
    Validate query parameters align to JSON:API standard, but also allow the non-standard ?search= param.
    """
    query_regex = re.compile(
        r"^(format|sort|include|search|ordering)$|^(?P<type>filter|fields|page|page_size)(\[[\w\.\-]+\])?$"
    )


class BiomeFilter(django_filters.FilterSet):

    depth_gte = filters.NumberFilter(
        field_name='depth', lookup_expr='gte',
        label='Depth, greater/equal then',
        help_text='Biome depth, greater/equal then')

    depth_lte = filters.NumberFilter(
        field_name='depth', lookup_expr='lte',
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
            studies = emg_models.Sample.objects.values('studies') \
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
            studies = emg_models.Sample.objects.values('studies') \
                .available(self.request) \
                .filter(biome__biome_id__in=biome_ids)
            qs = qs.filter(pk__in=studies)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    accession = django_filters.CharFilter(
        method='filter_study_accession', distinct=True,
        label='Study, ENA or BioProject accession',
        help_text='Study, ENA or BioProject accession')

    def filter_study_accession(self, qs, name, value):
        return qs.filter(*emg_utils.study_accession_query(value))

    centre_name = django_filters.CharFilter(
        method='filter_centre_name', distinct=True,
        label='Centre name',
        help_text='Centre name')

    def filter_centre_name(self, qs, name, value):
        return qs.filter(
            centre_name__iregex=WORD_MATCH_REGEX.format(value))

    # include
    include = django_filters.CharFilter(
        method='filter_include', distinct=True,
        label='Include',
        help_text=('Include related samples and/or biomes in the same '
                   'response.'))

    def filter_include(self, qs, name, value):
        return qs

    class Meta:
        model = emg_models.Study
        fields = (
            'accession',
            'biome_name',
            'lineage',
            'centre_name',
            'include',
        )


class QueryArrayWidget(widgets.BaseCSVWidget, forms.TextInput):
    """
    Fix django_filter.widgets to allow csv values on ModelMultipleChoiceFilter

    Enables request query array notation that might be consumed by
    MultipleChoiceFilter
    1. Values can be provided as csv string:  ?foo=bar,baz
    2. Values can be provided as query array: ?foo[]=bar&foo[]=baz
    3. Values can be provided as query array: ?foo=bar&foo=baz
    Note: Duplicate and empty values are skipped from results
    """
    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            data = data.copy()
        for key, value in data.items():
            # treat value as csv string: ?foo=1,2
            # if isinstance(value, string_types):
            data[key] = [
                x.strip() for x in value.rstrip(',').split(',') if x]
        data = MultiValueDict(data)

        if not isinstance(data, MultiValueDict):
            values_list = data.getlist(name, data.getlist('%s[]' % name)) or []
        else:
            values_list = data.get(name, [])
        # apparently its an array, so no need to process it's values as csv
        # ?foo=1&foo=2 -> data.getlist(foo) -> foo = [1, 2]
        # ?foo[]=1&foo[]=2 -> data.getlist(foo[]) -> foo = [1, 2]
        if len(values_list) > 0:
            ret = [x for x in values_list if x]
        else:
            ret = []

        return list(set(ret))


class SuperStudyFilter(django_filters.FilterSet):

    biome_name = django_filters.CharFilter(
        method='filter_biome_lineage', distinct=True,
        label='Biome name',
        help_text='Biome name')

    def filter_biome_lineage(self, qs, name, value):
        return qs.filter(
            biomes__lineage__iregex=WORD_MATCH_REGEX.format(value))

    class Meta:
        model = emg_models.SuperStudy
        fields = (
            'super_study_id',
            'title',
            'url_slug',
            'description',
            'biome_name',
        )


class SampleFilter(django_filters.FilterSet):

    accession = filters.ModelMultipleChoiceFilter(
        queryset=emg_models.Sample.objects,
        to_field_name='accession',
        method='filter_accession',
        distinct=True,
        label='Sample accession',
        help_text='Sample accession',
        widget=QueryArrayWidget
    )

    def filter_accession(self, qs, name, values):
        if values:
            qs = qs.available(self.request).filter(accession__in=values)
        return qs

    experiment_type = filters.ModelMultipleChoiceFilter(
        queryset=emg_models.ExperimentType.objects,
        to_field_name='experiment_type',
        method='filter_experiment_type',
        distinct=True,
        label='Experiment type',
        help_text='Experiment type',
        widget=QueryArrayWidget
    )

    def filter_experiment_type(self, qs, name, values):
        analyses = emg_models.AnalysisJob.objects \
            .filter(experiment_type__in=values) \
            .values('sample')
        if len(analyses) > 0:
            qs = qs.filter(pk__in=analyses)
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
        return qs.filter(pk__in=samples)

    instrument_model = django_filters.CharFilter(
        method='filter_instrument_model', distinct=True,
        label='Instrument model',
        help_text='Instrument model')

    def filter_instrument_model(self, qs, name, value):
        samples = emg_models.Run.objects.values('sample_id') \
            .available(self.request) \
            .filter(instrument_model__iregex=WORD_MATCH_REGEX.format(value))
        return qs.filter(pk__in=samples)

    metadata_key = filters.ChoiceFilter(
            choices=metadata_keywords,
            method='filter_metadata_key',
            field_name='metadata_key', distinct=True,
            label='Metadata keyword', help_text='Metadata keyword')

    def filter_metadata_key(self, qs, name, value):
        m = emg_models.VariableNames.objects.filter(var_name=value)
        return qs.filter(metadata__var__in=m)

    metadata_value_gte = django_filters.NumberFilter(
        method='filter_metadata_value_gte', distinct=True,
        label='Metadata greater/equal then value',
        help_text='Metadata greater/equal then value')

    def filter_metadata_value_gte(self, qs, name, value):
        return qs.filter(metadata__var_val_ucv__iregex=FLOAT_MATCH_REGEX) \
            .annotate(float_value=Cast(
                'metadata__var_val_ucv', FloatField())) \
            .filter(float_value__gte=float(value))

    metadata_value_lte = django_filters.NumberFilter(
        method='filter_metadata_value_lte', distinct=True,
        label='Metadata less/equal then value',
        help_text='Metadata less/equal then value')

    def filter_metadata_value_lte(self, qs, name, value):
        return qs.filter(metadata__var_val_ucv__iregex=FLOAT_MATCH_REGEX) \
            .annotate(float_value=Cast(
                'metadata__var_val_ucv', FloatField())) \
            .filter(float_value__lte=float(value))

    metadata_value = django_filters.CharFilter(
        method='filter_metadata_value', distinct=True,
        label='Metadata value',
        help_text='Metadata exact value')

    def filter_metadata_value(self, qs, name, value):
        return qs.filter(metadata__var_val_ucv__iregex=FLOAT_MATCH_REGEX) \
            .filter(metadata__var_val_ucv=value)

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

    latitude_gte = django_filters.NumberFilter(
        method='filter_latitude_gte', distinct=True,
        label='Latitude greater/equal then value',
        help_text='Latitude greater/equal then value')

    def filter_latitude_gte(self, qs, name, value):
        return qs.filter(latitude__gte=Decimal(str(value)))

    latitude_lte = django_filters.NumberFilter(
        method='filter_latitude_lte', distinct=True,
        label='Latitude less/equal then value',
        help_text='Latitude less/equal then value')

    def filter_latitude_lte(self, qs, name, value):
        return qs.filter(latitude__lte=Decimal(str(value)))

    longitude_gte = django_filters.NumberFilter(
        method='filter_longitude_gte', distinct=True,
        label='Longitude greater/equal then value',
        help_text='Longitude greater/equal then value')

    def filter_longitude_gte(self, qs, name, value):
        return qs.filter(longitude__gte=Decimal(str(value)))

    longitude_lte = django_filters.NumberFilter(
        method='filter_longitude_lte', distinct=True,
        label='Longitude less/equal then value',
        help_text='Longitude less/equal then value')

    def filter_longitude_lte(self, qs, name, value):
        return qs.filter(longitude__lte=Decimal(str(value)))

    study_accession = django_filters.CharFilter(
        method='filter_study_accession', distinct=True,
        label='Study, ENA or BioProject accession',
        help_text='Study, ENA or BioProject accession')

    def filter_study_accession(self, qs, name, value):
        return qs.filter(*emg_utils.sample_study_accession_query(value))

    # include
    include = django_filters.CharFilter(
        method='filter_include', distinct=True,
        label='Include',
        help_text=(
            'Include related run, metadata and/or biome in the same '
            'response.')
        )

    def filter_include(self, qs, name, value):
        return qs

    class Meta:
        model = emg_models.Sample
        fields = (
            'accession',
            'experiment_type',
            'biome_name',
            'lineage',
            'geo_loc_name',
            'latitude_gte',
            'latitude_lte',
            'longitude_gte',
            'longitude_lte',
            'species',
            'instrument_model',
            'instrument_platform',
            'metadata_key',
            'metadata_value_gte',
            'metadata_value_lte',
            'metadata_value',
            'environment_material',
            'environment_feature',
            'study_accession',
            'include',
        )


class RunFilter(django_filters.FilterSet):

    accession = filters.ModelMultipleChoiceFilter(
        queryset=emg_models.Run.objects,
        to_field_name='accession',
        method='filter_accession',
        distinct=True,
        label='Run accession',
        help_text='Run accession',
        widget=QueryArrayWidget
    )

    def filter_accession(self, qs, name, values):
        if values:
            qs = qs.available(self.request).filter(accession__in=values)
        return qs

    experiment_type = filters.ModelMultipleChoiceFilter(
        queryset=emg_models.ExperimentType.objects,
        to_field_name='experiment_type',
        field_name='experiment_type__experiment_type',
        distinct=True,
        label='Experiment type',
        help_text='Experiment type',
        widget=QueryArrayWidget
    )

    biome_name = django_filters.CharFilter(
        method='filter_biome_name', distinct=True,
        label='Biome name',
        help_text='Biome name')

    def filter_biome_name(self, qs, name, value):
        return qs.filter(
            sample__biome__lineage__iregex=WORD_MATCH_REGEX.format(value))

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

    metadata_key = filters.ChoiceFilter(
            choices=metadata_keywords,
            method='filter_metadata_key',
            field_name='metadata_key', distinct=True,
            label='Metadata keyword', help_text='Metadata keyword')

    def filter_metadata_key(self, qs, name, value):
        m = emg_models.VariableNames.objects.filter(var_name=value)
        return qs.filter(sample__metadata__var__in=m)

    metadata_value_gte = django_filters.NumberFilter(
        method='filter_metadata_value_gte', distinct=True,
        label='Metadata greater/equal then value',
        help_text='Metadata greater/equal then value')

    def filter_metadata_value_gte(self, qs, name, value):
        return qs.annotate(
            float_value=Cast('sample__metadata__var_val_ucv', FloatField())) \
            .filter(float_value__gte=float(value))

    metadata_value_lte = django_filters.NumberFilter(
        method='filter_metadata_value_lte', distinct=True,
        label='Metadata less/equal then value',
        help_text='Metadata less/equal then value')

    def filter_metadata_value_lte(self, qs, name, value):
        return qs.annotate(
            float_value=Cast('sample__metadata__var_val_ucv', FloatField())) \
            .filter(float_value__lte=float(value))

    metadata_value = django_filters.CharFilter(
        method='filter_metadata_value', distinct=True,
        label='Metadata value',
        help_text='Metadata exact value')

    def filter_metadata_value(self, qs, name, value):
        return qs.filter(
            sample__metadata__var_val_ucv=value)

    sample_accession = django_filters.CharFilter(
        method='filter_sample_accession', distinct=True,
        label='Sample accession',
        help_text='Sample accession')

    def filter_sample_accession(self, qs, name, value):
        return qs.filter(sample__accession=value)

    study_accession = django_filters.CharFilter(
        method='filter_study_accession', distinct=True,
        label='Study, ENA or BioProject accession',
        help_text='Study, ENA or BioProject accession')

    def filter_study_accession(self, qs, name, value):
        return qs.filter(*emg_utils.related_study_accession_query(value))

    # include
    include = django_filters.CharFilter(
        method='filter_include', distinct=True,
        label='Include',
        help_text=(
            'Include related sample in the same response.')
        )

    def filter_include(self, qs, name, value):
        return qs

    class Meta:
        model = emg_models.Run
        fields = (
            'accession',
            'experiment_type',
            'biome_name',
            'lineage',
            'species',
            'instrument_platform',
            'instrument_model',
            'metadata_key',
            'metadata_value_gte',
            'metadata_value_lte',
            'metadata_value',
            'sample_accession',
            'study_accession',
            'include',
        )


class AnalysisJobFilter(RunFilter):

    accession = django_filters.CharFilter(
        method='filter_analysisjob_accession', distinct=True,
        label='Analyses job accession',
        help_text='Analyses job accession')

    def filter_analysisjob_accession(self, qs, name, value):
        return qs.filter(*emg_utils.analysisjob_accession_query(value))

    pipeline_version = filters.ChoiceFilter(
        choices=pipeline_version,
        field_name='pipeline__release_version', distinct=True,
        label='Pipeline version', help_text='Pipeline version')

    sample_accession = django_filters.CharFilter(
        method='filter_sample_accession', distinct=True,
        label='Sample accession',
        help_text='Sample accession')

    def filter_sample_accession(self, qs, name, value):
        return qs.filter(Q(sample__accession=value) | Q(sample__primary_accession=value))

    class Meta:
        model = emg_models.AnalysisJob
        fields = (
            'biome_name',
            'lineage',
            'experiment_type',
            'species',
            'sample_accession',
            'pipeline_version'
        )


class AssemblyFilter(django_filters.FilterSet):

    accession = filters.ModelMultipleChoiceFilter(
        queryset=emg_models.Assembly.objects,
        to_field_name='accession',
        method='filter_accession',
        distinct=True,
        label='Assembly accession',
        help_text='Assembly accession',
        widget=QueryArrayWidget
    )

    def filter_accession(self, qs, name, values):
        if values:
            qs = qs.available(self.request).filter(
                Q(accession__in=values) |
                Q(wgs_accession__in=values) |
                Q(legacy_accession__in=values)
            )
        return qs

    biome_name = django_filters.CharFilter(
        method='filter_biome_name', distinct=True,
        label='Biome name',
        help_text='Biome name')

    def filter_biome_name(self, qs, name, value):
        return qs.filter(
            samples__lineage__iregex=WORD_MATCH_REGEX.format(value))

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
                samples__biome__lft__gte=b.lft,
                samples__biome__rgt__lte=b.rgt)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    species = django_filters.CharFilter(
        method='filter_species', distinct=True,
        label='Species',
        help_text='Species')

    def filter_species(self, qs, name, value):
        return qs.filter(
            samples__species__iregex=WORD_MATCH_REGEX.format(value))

    metadata_key = filters.ChoiceFilter(
            choices=metadata_keywords,
            method='filter_metadata_key',
            field_name='metadata_key', distinct=True,
            label='Metadata keyword', help_text='Metadata keyword')

    def filter_metadata_key(self, qs, name, value):
        m = emg_models.VariableNames.objects.filter(var_name=value)
        return qs.filter(samples__metadata__var__in=m)

    metadata_value_gte = django_filters.NumberFilter(
        method='filter_metadata_value_gte', distinct=True,
        label='Metadata greater/equal then value',
        help_text='Metadata greater/equal then value')

    def filter_metadata_value_gte(self, qs, name, value):
        return qs.annotate(
            float_value=Cast('samples__metadata__var_val_ucv', FloatField())) \
            .filter(float_value__gte=float(value))

    metadata_value_lte = django_filters.NumberFilter(
        method='filter_metadata_value_lte', distinct=True,
        label='Metadata less/equal then value',
        help_text='Metadata less/equal then value')

    def filter_metadata_value_lte(self, qs, name, value):
        return qs.annotate(
            float_value=Cast('samples__metadata__var_val_ucv', FloatField())) \
            .filter(float_value__lte=float(value))

    metadata_value = django_filters.CharFilter(
        method='filter_metadata_value', distinct=True,
        label='Metadata value',
        help_text='Metadata exact value')

    def filter_metadata_value(self, qs, name, value):
        return qs.filter(
            samples__metadata__var_val_ucv=value)

    sample_accession = django_filters.CharFilter(
        method='filter_sample_accession', distinct=True,
        label='Sample accession',
        help_text='Sample accession')

    def filter_sample_accession(self, qs, name, value):
        return qs.filter(Q(samples__accession=value) | Q(samples__primary_accession=value))

    run_accession = django_filters.CharFilter(
        method='filter_runs_accession', distinct=True,
        label='Run accession',
        help_text='Run accession')

    def filter_runs_accession(self, qs, name, value):
        return qs.filter(runs__accession=value)

    # include
    include = django_filters.CharFilter(
        method='filter_include', distinct=True,
        label='Include',
        help_text=(
            'Include related sample in the same response.')
        )

    def filter_include(self, qs, name, value):
        return qs

    class Meta:
        model = emg_models.Assembly
        fields = (
            'accession',
            'biome_name',
            'lineage',
            'species',
            'metadata_key',
            'metadata_value_gte',
            'metadata_value_lte',
            'metadata_value',
            'sample_accession',
            'include',
        )


class GenomeFilter(django_filters.FilterSet):

    length__gte = django_filters.NumberFilter(
        field_name="length",
        lookup_expr="gte",
        help_text="Length (bp) greater/equal value",
    )
    length__lte = django_filters.NumberFilter(
        field_name="length", lookup_expr="lte", help_text="Length (bp) less/equal value"
    )

    num_contigs__gte = django_filters.NumberFilter(
        field_name="num_contigs",
        label="Number of contigs",
        lookup_expr="gte",
        help_text="Number of contigs greater/equal value",
    )
    num_contigs__lte = django_filters.NumberFilter(
        field_name="num_contigs",
        label="Number of contigs",
        lookup_expr="lte",
        help_text="Number of contigs greater/equal value",
    )

    n_50__gte = django_filters.NumberFilter(
        field_name="n_50",
        label="N50",
        lookup_expr="gte",
        help_text="N50 greater/equal value",
    )
    n_50__lte = django_filters.NumberFilter(
        field_name="n_50",
        label="N50",
        lookup_expr="lte",
        help_text="N50 less/equal value",
    )

    gc_content__gte = django_filters.NumberFilter(
        field_name="gc_content",
        label="GC%",
        lookup_expr="gte",
        help_text="GC% greater/equal value",
    )
    gc_content__lte = django_filters.NumberFilter(
        field_name="gc_content",
        label="GC%",
        lookup_expr="lte",
        help_text="GC% less/equal value",
    )

    completeness__gte = django_filters.NumberFilter(
        field_name="completeness",
        label="Completeness",
        lookup_expr="gte",
        help_text="Completeness greater/equal value",
    )
    completeness__lte = django_filters.NumberFilter(
        field_name="completeness",
        label="Completeness",
        lookup_expr="lte",
        help_text="Completeness less/equal value",
    )

    # TODO: use Range instead
    contamination__gte = django_filters.NumberFilter(
        field_name="contamination",
        label="Contamination",
        lookup_expr="gte",
        help_text="Contamination greater/equal value",
    )
    contamination__lte = django_filters.NumberFilter(
        field_name="contamination",
        label="Contamination",
        lookup_expr="lte",
        help_text="Contamination less/equal value",
    )

    num_proteins__gte = django_filters.NumberFilter(
        field_name="num_proteins",
        label="Number of proteins",
        lookup_expr="gte",
        help_text="Number of proteins greater/equal value",
    )
    num_proteins__lte = django_filters.NumberFilter(
        field_name="num_proteins",
        label="Number of proteins",
        lookup_expr="lte",
        help_text="Number of proteins less/equal value",
    )

    num_genomes_total__gte = django_filters.NumberFilter(
        field_name="num_genomes_total",
        label="Total number of genomes in species",
        lookup_expr="gte",
        help_text="Total number of genomes in species greater/equal value",
    )
    num_genomes_total__lte = django_filters.NumberFilter(
        field_name="num_genomes_total",
        label="Total number of genomes in species",
        lookup_expr="lte",
        help_text="Total number of genomes in species less/equal value",
    )

    pangenome_size__gte = django_filters.NumberFilter(
        field_name="pangenome_size",
        label="Pan-genome size",
        lookup_expr="gte",
        help_text="Pan-genome size greater/equal value",
    )
    pangenome_size__lte = django_filters.NumberFilter(
        field_name="pangenome_size",
        label="Pan-genome size",
        lookup_expr="lte",
        help_text="Pan-genome size less/equal value",
    )

    pangenome_core_size__gte = django_filters.NumberFilter(
        field_name="pangenome_core_size",
        label="Pan-genome core size",
        lookup_expr="gte",
        help_text="Pan-genome core size greater/equal value",
    )
    pangenome_core___lte = django_filters.NumberFilter(
        field_name="pangenome_core_size",
        label="Pan-genome core size",
        lookup_expr="lte",
        help_text="Pan-genome core size less/equal value",
    )

    pangenome_accessory_size__gte = django_filters.NumberFilter(
        field_name="pangenome_accessory_size",
        label="Pan-genome core size",
        lookup_expr="gte",
        help_text="Pan-genome accessory size greater/equal value",
    )

    pangenome_accessory_size__lte = django_filters.NumberFilter(
        field_name="pangenome_accessory_size",
        label="Pan-genome core size",
        lookup_expr="lte",
        help_text="Pan-genome accessory size less/equal value",
    )

    accession = filters.ModelMultipleChoiceFilter(
        queryset=emg_models.Genome.objects,
        to_field_name="accession",
        method="filter_accession",
        distinct=True,
        label="Accession",
        help_text="Select by MGnify, NCBI, IMG or Patric accession",
        widget=QueryArrayWidget,
    )

    def filter_accession(self, qs, name, values):
        """Filter by any accession:
        - MGnify accession
        - ENA genome, sample or study accession
        - NCBI genome, sample or study accession
        - IMG genome accession
        - PATRIC genome accesssion
        """
        if values:
            qs = qs.filter(
                Q(accession__in=values)
                | Q(ena_genome_accession__in=values)
                | Q(ena_sample_accession__in=values)
                | Q(ena_study_accession__in=values)
                | Q(ncbi_genome_accession__in=values)
                | Q(ncbi_sample_accession__in=values)
                | Q(ncbi_study_accession__in=values)
                | Q(img_genome_accession__in=values)
                | Q(patric_genome_accession__in=values)
            )
        return qs

    taxon_lineage = django_filters.CharFilter(
        field_name="taxon_lineage",
        lookup_expr="contains",
        help_text="Taxon lineage",
        label="Taxon lineage",
    )

    mag_type = django_filters.ChoiceFilter(
        field_name="type",
        help_text="MAG or isolate",
        label="Type",
        choices=emg_models.Genome.TYPE_CHOICES
    )

    geo_origin = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="geo_origin__name",
        to_field_name="name",
        queryset=emg_models.GeographicLocation.objects.all(),
    )

    pangenome_geographic_range = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="pangenome_geographic_range__name",
        to_field_name="name",
        queryset=emg_models.GeographicLocation.objects.all(),
    )

    class Meta:
        model = emg_models.Genome
        fields = (
            "accession",
            "taxon_lineage",
            "mag_type",
            "geo_origin",
            "pangenome_geographic_range",
            "length__gte",
            "length__lte",
            "num_contigs__gte",
            "num_contigs__lte",
            "n_50__gte",
            "n_50__lte",
            "gc_content__gte",
            "gc_content__lte",
            "completeness__gte",
            "completeness__lte",
            "contamination__gte",
            "contamination__lte",
            "num_proteins__gte",
            "num_proteins__lte",
            "num_genomes_total__gte",
            "num_genomes_total__lte",
            "pangenome_size__gte",
            "pangenome_size__lte",
            "pangenome_accessory_size__gte",
            "pangenome_accessory_size__lte",
        )


class GenomeCatalogueFilter(django_filters.FilterSet):

    lineage = filters.ModelChoiceFilter(
        queryset=emg_models.Biome.objects.all(),
        method='filter_lineage', distinct=True,
        to_field_name='lineage',
        label='Biome lineage',
        help_text='Biome lineage')

    def filter_lineage(self, qs, name, value):
        try:
            b = emg_models.Biome.objects.get(lineage=value)
            catalogues = emg_models.GenomeCatalogue.objects\
                .filter(
                biome__lft__gte=b.lft,
                biome__rgt__lte=b.rgt)
            qs = qs.filter(pk__in=catalogues)
        except emg_models.Biome.DoesNotExist:
            pass
        return qs

    class Meta:
        model = emg_models.GenomeCatalogue
        fields = {
            'catalogue_id': ['exact'],
            'name': ['exact', 'icontains'],
            'description': ['exact', 'icontains'],
            'biome__biome_name': ['exact', 'icontains'],
            'last_update': ['exact', 'lt', 'gt'],
        }


def getUnambiguousOrderingFilterByField(field):
    class UnambiguousOrderingFilter(drf_filters.OrderingFilter):
        def filter_queryset(self, request, queryset, view):
            ordering = self.get_ordering(request, queryset, view)

            if ordering:
                if field in ordering:
                    return queryset.order_by(*ordering)
                else:
                    return queryset.order_by(*ordering, field)

            return queryset
    return UnambiguousOrderingFilter
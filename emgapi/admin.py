#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django import forms

from . import models as emg_models


class AccessionSearch:
    prefix = ''
    filter_property = None

    def get_search_results(self, request, queryset, search_term):
        """Allow users to search using Mgnify accession prefix (i.e. MGSYS)
        """
        if search_term and search_term.startswith(self.prefix):
            clean_id = int(search_term.lstrip(self.prefix) or 0)
            return self.model.objects.filter(**{self.filter_property: [clean_id]}), False
        else:
            return super().get_search_results(request, queryset, search_term)


@admin.register(emg_models.Biome)
class Biome(admin.ModelAdmin):
    search_fields = [
        'biome_id',
        'biome_name',
        'lineage'
    ]


@admin.register(emg_models.Study)
class Study(admin.ModelAdmin):
    ordering = ['-last_update']
    search_fields = [
        'study_id',
        'secondary_accession',
        'project_id',
        'centre_name',
        'study_abstract',
        'study_name',
        'author_name',
        'author_email',
        'biome__biome_name',
    ]
    list_display = (
        'study_id',
        'project_id',
        'study_name',
    )
    list_filter = ('is_public', )


class SuperStudyStudiesInline(admin.TabularInline):
    model = emg_models.SuperStudyStudy
    raw_id_fields = ('study',)


class SuperStudyBiomesInline(admin.TabularInline):
    model = emg_models.SuperStudyBiome
    raw_id_fields = ('biome',)


class SuperStudyAdminForm(forms.ModelForm):
    class Meta:
        model = emg_models.SuperStudy
        fields = '__all__'
        if os.path.isdir(settings.IMG_DIR):
            _options = [(fname, fname) for fname in os.listdir(settings.IMG_DIR)]
            _options.insert(0, ('', ''))
            widgets = {
                'image': forms.Select(choices=_options)
            }


@admin.register(emg_models.SuperStudy)
class SuperStudyAdmin(admin.ModelAdmin):

    readonly_fields = ('image_tag',)
    inlines = [SuperStudyStudiesInline, SuperStudyBiomesInline]
    form = SuperStudyAdminForm

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(
                '<img src="{}/{}" width="150" height="150" />'.format(settings.IMG_FOLDER, obj.image)
            )
        else:
            return 'No image selected'
    image_tag.short_description = 'Image'


@admin.register(emg_models.Sample)
class SampleAdmin(admin.ModelAdmin):

    readonly_fields = (
        'sample_id',
        'accession',
        'primary_accession'
    )
    ordering = ['-last_update']
    search_fields = [
        'sample_id',
        'accession',
        'primary_accession',
        'sample_name',
        'sample_alias',
        'species',
        'biome__biome_name'
    ]
    list_filter = ('is_public', )
    list_display = (
        'accession',
        'primary_accession',
        'sample_name',
        'sample_desc',
        'is_public',
    )

    def get_search_results(self, request, queryset, search_term):
        """For searches that start with MGYS will only search on samples
        """
        if search_term and search_term.startswith('MGYS'):
            study_id = int(search_term.lstrip('MGYS') or 0)
            return self.model.objects.filter(studies__in=[study_id]), False
        else:
            return super().get_search_results(request, queryset, search_term)


@admin.register(emg_models.Run)
class RunAdmin(admin.ModelAdmin, AccessionSearch):

    ordering = ['-run_id']

    readonly_fields = (
        'run_id',
        'accession',
        'secondary_accession',
        'sample',
        'study',
    )
    search_fields = [
        'run_id',
        'secondary_accession',
        'sample__accession',
        'instrument_platform',
        'instrument_model'
    ]
    list_filter = ('status', )
    list_display = (
        'run_id',
        'accession',
        'secondary_accession',
        'sample',
        'study',
        'status'
    )

    filter_property = 'study'
    prefix = 'MGYS'


@admin.register(emg_models.Publication)
class PublicationAdmin(admin.ModelAdmin):
    ordering = ['-published_year']
    search_fields = [
        'pub_title',
        'authors',
        'doi',
        'pub_url',
        'pub_type',
    ]
    list_display = [
        'pub_id',
        'pub_title',
        'pub_url',
        'pub_type',
    ]


class AssemblyRunInline(admin.TabularInline):
    model = emg_models.Assembly.runs.through


class AssemblySampleInline(admin.TabularInline):
    model = emg_models.Assembly.samples.through


@admin.register(emg_models.Assembly)
class AssemblyAdmin(admin.ModelAdmin, AccessionSearch):
    readonly_fields = [
        'assembly_id',
        'accession'
    ]
    search_fields = [
        'assembly_id',
        'accession',
        'wgs_accession',
        'legacy_accession',
        'experiment_type'
    ]
    list_filter = [
        'experiment_type',
        'status_id'
    ]
    inlines = [
        AssemblyRunInline,
        AssemblySampleInline
    ]


@admin.register(emg_models.AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    ordering = ['-submit_time']
    readonly_fields = (
        'job_id',
        'accession',
        'secondary_accession',
        'run',
        'sample',
        'study',
        'assembly'
    )
    search_fields = [
        'job_id',
        'accession',
        'secondary_accession',
        'run__accession',
        'sample__accession',
        'study__accession',
        'assembly__accession',
        'instrument_platform',
        'instrument_model'
    ]
    list_filter = ['status', 'pipeline']
    list_display = [
        'job_id',
        'accession',
        'secondary_accession',
        'run',
        'sample',
        'study',
        'assembly'
    ]


@admin.register(emg_models.StudyErrorType)
class StudyErrorTypeAdmin(admin.ModelAdmin):
    readonly_fields = [
        'error_id',
        'error_type',
        'description'
    ]


@admin.register(emg_models.BlacklistedStudy)
class BlacklistedStudyAdmin(admin.ModelAdmin):
    readonly_fields = (
        'ext_study_id',
        'error_type',
        'analyzer',
        'pipeline_id',
        'date_blacklisted',
        'comments'
    )
    list_filter = ['pipeline_id', ]
    list_display = [
        'ext_study_id',
        'error_type',
        'analyzer',
        'date_blacklisted'
    ]


@admin.register(emg_models.VariableNames)
class VariableNamesAdmin(admin.ModelAdmin):
    readonly_fields = [
        'id',
        'var_name'
    ]
    search_fields = [
        'var_name',
        'alias',
        'definition',
        'authority',
        'comments',
    ]
    list_filter = (
        'authority',
        'required_for_mimarks_complianc',
        'required_for_mims_compliance'
    )
    list_display = (
        'var_name',
        'alias',
        'authority'
    )


@admin.register(emg_models.SampleAnn)
class SampleAnnAdmin(admin.ModelAdmin):
    readonly_fields = [
        'id',
        'sample',
    ]
    search_fields = [
        'sample'
    ]
    list_display = (
        'sample',
        'units',
        'var'
    )

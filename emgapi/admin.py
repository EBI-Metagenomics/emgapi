#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django import forms

from . import models as emg_models


# utilities
class NoRemoveMixin:
    """Disable delete permissions
    """
    def has_delete_permission(self, request, obj=None):
        return False


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
class Study(admin.ModelAdmin, NoRemoveMixin):
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
class SampleAdmin(admin.ModelAdmin, NoRemoveMixin):
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
    change_list_template = "admin/change_list_filter_sidebar.html"
    list_filter = [
        'is_public',
    ]
    list_display = [
        'accession',
        'primary_accession',
        'sample_name',
        'sample_desc',
        'is_public',
    ]

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
    ordering = [
        '-run_id'
    ]
    readonly_fields = [
        'run_id',
        'accession',
        'secondary_accession',
        'sample',
        'study',
    ]
    search_fields = [
        'run_id',
        'secondary_accession',
        'sample__accession',
        'instrument_platform',
        'instrument_model'
    ]
    list_filter = [
        'status_id',
    ]
    list_display = [
        'run_id',
        'accession',
        'secondary_accession',
        'sample',
        'study',
        'status_id'
    ]

    filter_property = 'study'
    prefix = 'MGYS'


@admin.register(emg_models.Publication)
class PublicationAdmin(admin.ModelAdmin):
    ordering = [
        '-published_year'
    ]
    readonly_fields = [
        'pub_id'
    ]
    search_fields = [
        'pub_title',
        'authors',
        'doi',
        'pub_url',
        'pub_type',
    ]
    list_display = [
        'pub_title',
        'pub_url',
        'pub_type',
    ]


class AssemblyRunInline(admin.TabularInline):
    model = emg_models.Assembly.runs.through


class AssemblySampleInline(admin.TabularInline):
    model = emg_models.Assembly.samples.through


@admin.register(emg_models.Assembly)
class AssemblyAdmin(admin.ModelAdmin):
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
class AnalysisJobAdmin(admin.ModelAdmin, AccessionSearch, NoRemoveMixin):
    ordering = ['-submit_time']
    readonly_fields = [
        'job_id',
        'secondary_accession',
        'run',
        'sample',
        'study',
        'assembly',
    ]
    search_fields = [
        'job_id',
        'secondary_accession',
        'run__accession',
        'sample__accession',
        'study__accession',
        'assembly__accession',
        'instrument_platform',
        'instrument_model'
    ]
    change_list_template = 'admin/filter_listing.html'
    list_filter = [
        'analysis_status',
        'pipeline__release_version',
    ]
    list_display = [
        'job_id',
        'secondary_accession',
        'experiment_type',
        'analysis_status',
        'run',
        'sample',
        'study',
        'assembly'
    ]
    prefix = 'MGYA'
    filter_property = 'job_id'


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
    )
    change_list_template = "admin/change_list_filter_sidebar.html"
    list_filter = [
        'pipeline_id',
    ]
    list_display = [
        'ext_study_id',
        'error_type',
        'analyzer',
        'date_blacklisted'
    ]


@admin.register(emg_models.VariableNames)
class VariableNamesAdmin(admin.ModelAdmin):
    readonly_fields = [
        'var_id',
    ]
    search_fields = [
        'var_name',
        'alias',
        'definition',
        'authority',
        'comments',
    ]
    change_list_template = "admin/change_list_filter_sidebar.html"
    list_filter = [
        'authority',
        'required_for_mimarks_complianc',
        'required_for_mims_compliance'
    ]
    list_display = [
        'var_name',
        'alias',
        'authority'
    ]


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


@admin.register(emg_models.AnalysisMetadataVariableNames)
class AnalysisMetadataVariableNamesAdmin(admin.ModelAdmin):
    list_display = [
        'var_name',
        'description'
    ]
    search_fields = [
        'var_name',
        'description'
    ]


@admin.register(emg_models.AnalysisJobAnn)
class AnalysisJobAnnAdmin(admin.ModelAdmin):
    readonly_fields = [
        'job',
        'var',
    ]
    list_display = [
        'job',
        'var'
    ]
    search_fields = [
        'job__accession',
        'var'
    ]


@admin.register(emg_models.CogCat)
class CogCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'description'
    ]
    search_fields = [
        'name',
        'description'
    ]


@admin.register(emg_models.AntiSmashGC)
class AntiSmashGCAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'description'
    ]
    search_fields = [
        'name',
        'description'
    ]


@admin.register(emg_models.GeographicLocation)
class GeographicLocationAdmin(admin.ModelAdmin):
    list_display = [
        'name',
    ]
    search_fields = [
        'name'
    ]


@admin.register(emg_models.GenomeSet)
class GenomeSetAdmin(admin.ModelAdmin):
    list_display = [
        'name'
    ]
    search_fields = [
        'name',
    ]


class GenomeReleasesInline(admin.TabularInline):
    model = emg_models.Genome.releases.through


@admin.register(emg_models.Genome)
class GenomeAdmin(admin.ModelAdmin):
    readonly_fields = [
        'genome_id',
        'accession',
    ]
    list_display = [
        'accession',
        'type',
        'ena_genome_accession',
        'ncbi_genome_accession',
        'img_genome_accession',
        'patric_genome_accession',
        'genome_set'
    ]
    search_fields = [
        'accession',
        'type',
        'ena_genome_accession',
        'ena_sample_accession',
        'ena_study_accession',
        'ncbi_genome_accession',
        'ncbi_sample_accession',
        'ncbi_study_accession',
        'img_genome_accession',
        'patric_genome_accession',
        'biome'
    ]
    change_list_template = "admin/change_list_filter_sidebar.html"
    list_filter = [
        'genome_set',
        'releases',
        'completeness',
        'contamination',
        'num_contigs',
        'n_50'
    ]
    # TODO: find a pagination inline tool or write one
    exclude = [
        'cog_matches',
        'kegg_classes',
        'kegg_modules',
        'antismash_geneclusters'
    ]
    inlines = [
        GenomeReleasesInline
    ]


@admin.register(emg_models.Release)
class GenomeReleaseAdmin(admin.ModelAdmin):
    readonly_fields = [
        'id'
    ]
    list_display = [
        'version',
        'first_created',
        'last_update'
    ]
    exclude = [
        'genomes'
    ]


@admin.register(emg_models.KeggClass)
class KeggClassAdmin(admin.ModelAdmin):
    list_display = [
        'class_id',
        'name',
        'parent'
    ]
    search_fields = [
        'class_id',
        'name',
        'parent__class_id',
        'parent__name'
    ]


@admin.register(emg_models.KeggModule)
class KeggModuleAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'description'
    ]
    search_fields = [
        'name',
        'description'
    ]


class PipelineToolInlineAdmin(admin.TabularInline):
    model = emg_models.Pipeline.tools.through


@admin.register(emg_models.Pipeline)
class PipelineAdmin(admin.ModelAdmin, NoRemoveMixin):
    readonly_fields = [
        'pipeline_id'
    ]
    list_display = [
        'release_version',
        'release_date'
    ]
    search_fields = [
        'pipeline_id',
        'release_version',
        'release_date',
    ]
    inlines = [
        PipelineToolInlineAdmin
    ]


@admin.register(emg_models.PipelineTool)
class PipelineTool(admin.ModelAdmin):
    readonly_fields = [
        'tool_id'
    ]
    list_display = [
        'tool_name',
        'version'
    ]
    search_fields = [
        'tool_name',
        'description',
        'web_link',
        'version',
        'exe_command',
        'installation_dir',
        'configuration_file',
        'notes'
    ]


@admin.register(emg_models.FileFormat)
class FileFormatAdmin(admin.ModelAdmin):
    readonly_fields = [
        'format_id'
    ]
    list_filter = [
        'compression'
    ]
    search_fields = [
        'format_name',
        'format_extension',
    ]
    list_display = [
        'format_name',
        'format_extension',
        'compression'
    ]


class BaseDownloadAdmin:
    readonly_fields = [
        'id'
    ]
    list_display = [
        'realname',
        'parent_id',
        'alias',
        'group_type',
        'subdir',
        'file_format'
    ]
    list_filter = [
        'file_format__format_name',
        'file_format__compression',
        'group_type'
    ]
    search_fields = [
        'realname',
        'alias',
        'group_type',
        'subdir',
        'file_format__format_name'
    ]


@admin.register(emg_models.AnalysisJobDownload)
class AnalysisJobDownloadAdmin(admin.ModelAdmin,
                               BaseDownloadAdmin):
    list_display = BaseDownloadAdmin.list_display + [
        'job'
    ]
    search_fields = BaseDownloadAdmin.search_fields + [
        'job__accession'
    ]


@admin.register(emg_models.GenomeDownload)
class GenomeDownloadAdmin(admin.ModelAdmin, BaseDownloadAdmin):
    list_display = BaseDownloadAdmin.list_display + [
        'genome'
    ]
    search_fields = BaseDownloadAdmin.search_fields + [
        'genome__accession',
        'genome__ena_genome_accession',
        'genome__ncbi_genome_accession',
        'genome__img_genome_accession',
        'genome__patric_genome_accession',
    ]


@admin.register(emg_models.ReleaseDownload)
class ReleaseDownloadAdmin(admin.ModelAdmin, BaseDownloadAdmin):
    list_display = BaseDownloadAdmin.list_display + [
        'release'
    ]

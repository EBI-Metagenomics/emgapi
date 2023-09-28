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

from django.contrib import admin, messages
from django import forms

from .widgets import BiomePredictionWidget
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
        """Allow users to search using Mgnify accession prefix (i.e. MGYS)
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


class BiomePredictorAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['biome'].widget = BiomePredictionWidget(
            search_fields=self.search_fields,
            rel=self.model._meta.get_field('biome').remote_field,
            admin_site=admin.sites.site)


class StudyAdminForm(BiomePredictorAdminForm):
    search_fields = ['study_name', 'study_abstract']
    model = emg_models.Study


@admin.register(emg_models.Study)
class StudyAdmin(admin.ModelAdmin, NoRemoveMixin):
    form = StudyAdminForm
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
    list_filter = ('is_private',)
    raw_id_fields = ('biome',)

    def save_model(self, request, obj, form, change):
        """Save the Study and cascade the biome to the Samples
        """
        super().save_model(request, obj, form, change)
        obj.samples.update(biome=obj.biome)


class SuperStudyStudiesInline(admin.TabularInline):
    model = emg_models.SuperStudyStudy
    raw_id_fields = ('study',)


class SuperStudyBiomesInline(admin.TabularInline):
    model = emg_models.SuperStudyBiome
    raw_id_fields = ('biome',)


class SuperStudyGenomeCataloguesInline(admin.TabularInline):
    model = emg_models.SuperStudyGenomeCatalogue
    extra = 0


class Base64FileInput(forms.TextInput):
    template_name = 'admin/base64_image.html'


class SuperStudyAdminForm(forms.ModelForm):
    class Meta:
        model = emg_models.SuperStudy
        fields = '__all__'
        widgets = {
            'logo': Base64FileInput
        }


@admin.register(emg_models.SuperStudy)
class SuperStudyAdmin(admin.ModelAdmin):
    inlines = [SuperStudyStudiesInline, SuperStudyBiomesInline, SuperStudyGenomeCataloguesInline]
    form = SuperStudyAdminForm


class SampleAdminForm(BiomePredictorAdminForm):
    search_fields = [
        'sample_name',
        'environment_biome',
        'environment_feature',
        'environment_material'
    ]
    model = emg_models.Sample


@admin.register(emg_models.Sample)
class SampleAdmin(admin.ModelAdmin, NoRemoveMixin):
    form = SampleAdminForm
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
        'is_private',
    ]
    list_display = [
        'accession',
        'primary_accession',
        'sample_name',
        'sample_desc',
        'is_private',
    ]

    def get_search_results(self, request, queryset, search_term):
        """For searches that start with MGYS will only search on samples
        """
        if search_term and search_term.startswith('MGYS'):
            study_id = int(search_term.lstrip('MGYS') or 0)
            return self.model.objects.filter(studies__in=[study_id]), False
        else:
            return super().get_search_results(request, queryset, search_term)


class RunExtraAnnotationDownloads(admin.TabularInline):
    model = emg_models.RunExtraAnnotation
    raw_id_fields = [
        'run',
        'parent_id',
        'group_type',
        'subdir',
        'description',
        'file_format'
    ]
    extra = 0

@admin.register(emg_models.Run)
class RunAdmin(admin.ModelAdmin, AccessionSearch):
    change_list_template = "admin/change_list_filter_sidebar.html"
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
    list_display = [
        'run_id',
        'accession',
        'secondary_accession',
        'sample',
        'study',
    ]
    inlines = [
        RunExtraAnnotationDownloads,
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


class AssemblyExtraAnnotationDownloads(admin.TabularInline):
    model = emg_models.AssemblyExtraAnnotation
    raw_id_fields = [
        'assembly',
        'parent_id',
        'group_type',
        'subdir',
        'description',
        'file_format'
    ]
    extra = 0


@admin.register(emg_models.Assembly)
class AssemblyAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list_filter_sidebar.html"
    ordering = ['-assembly_id', ]
    readonly_fields = [
        'assembly_id',
        'accession'
    ]
    search_fields = [
        'assembly_id',
        'accession',
        'wgs_accession',
        'legacy_accession',
        'experiment_type__experiment_type'
    ]
    inlines = [
        AssemblyExtraAnnotationDownloads
    ]


@admin.register(emg_models.AssemblyRun)
class AssemblyRunAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'assembly',
        'run',
    ]
    search_fields = [
        'assembly__accession',
        'run__accession',
    ]
    raw_id_fields = [
        'assembly',
        'run',
    ]


@admin.register(emg_models.AssemblySample)
class AssemblySampleAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'assembly',
        'sample',
    ]
    search_fields = [
        'assembly__accession',
        'sample__accession',
    ]
    raw_id_fields = [
        'assembly',
        'sample',
    ]


class AnalysisJobDownloads(admin.TabularInline):
    model = emg_models.AnalysisJobDownload
    raw_id_fields = [
        'job',
        'parent_id',
        'group_type',
        'subdir',
        'description',
        'file_format',
        'pipeline'
    ]


@admin.register(emg_models.AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin, AccessionSearch, NoRemoveMixin):
    change_list_template = "admin/change_list_filter_sidebar.html"
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
        'study__study_id',
        'assembly__accession',
        'instrument_platform',
        'instrument_model'
    ]
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
    inlines = [
        AnalysisJobDownloads
    ]
    prefix = 'MGYA'
    filter_property = 'job_id'

    def get_queryset(self, request):
        return emg_models.AnalysisJob.objects_admin.all() \
            .select_related(
            'pipeline',
            'analysis_status',
            'experiment_type',
            'run',
            'study',
            'assembly',
            'sample')


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
    change_list_template = "admin/change_list_filter_sidebar.html"
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


# @admin.register(emg_models.AnalysisJobAnn)
# class AnalysisJobAnnAdmin(admin.ModelAdmin):
#     readonly_fields = [
#         'job',
#         'var',
#     ]
#     list_display = [
#         'job',
#         'var'
#     ]
#     search_fields = [
#         'job__job_id',
#         'var__var_name',
#         'var__description',
#     ]


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


class GenomeDownloads(admin.TabularInline):
    model = emg_models.GenomeDownload
    raw_id_fields = [
        'genome',
        'parent_id',
        'group_type',
        'subdir',
        'description',
        'file_format'
    ]
    extra = 0


@admin.register(emg_models.Genome)
class GenomeAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list_filter_sidebar.html"
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
        'catalogue__name',
        'type',
        'ena_genome_accession',
        'ena_sample_accession',
        'ena_study_accession',
        'ncbi_genome_accession',
        'ncbi_sample_accession',
        'ncbi_study_accession',
        'img_genome_accession',
        'patric_genome_accession',
        'biome__lineage'
    ]
    list_filter = [
        'genome_set',
        'catalogue__catalogue_id',
        'type',
    ]
    raw_id_fields = [
        'biome',
    ]
    exclude = [
        'cog_matches',
        'kegg_classes',
        'kegg_modules',
        'antismash_geneclusters'
    ]
    inlines = [
        GenomeDownloads
    ]


class GenomeCatalogueDownloads(admin.TabularInline):
    model = emg_models.GenomeCatalogueDownload
    raw_id_fields = [
        'genome_catalogue',
        'parent_id',
        'group_type',
        'subdir',
        'description',
        'file_format'
    ]
    extra = 0


def recalculate_genome_count(modeladmin, request, queryset):
    for catalogue in queryset:
        catalogue.calculate_genome_count()
        messages.add_message(request, messages.SUCCESS, f'Catalogue {catalogue.catalogue_id} saved '
                                                        f'with genome_count={catalogue.genome_count}')


recalculate_genome_count.short_description = 'Recalculate genome count'


@admin.register(emg_models.GenomeCatalogue)
class GenomeCatalogueAdmin(admin.ModelAdmin):
    list_display = [
        'catalogue_id',
        'name',
        'biome',
        'last_update',
    ]
    raw_id_fields = [
        'biome',
    ]
    inlines = [
        GenomeCatalogueDownloads
    ]
    readonly_fields = ['genome_count']
    actions = [recalculate_genome_count, ]


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


@admin.register(emg_models.DownloadGroupType)
class DownloadGroupTypeAdmin(admin.ModelAdmin):
    readonly_fields = [
        'group_id'
    ]
    search_fields = [
        'group_type'
    ]
    list_display = [
        'group_type'
    ]


@admin.register(emg_models.DownloadSubdir)
class DownloadSubdirAdmin(admin.ModelAdmin):
    readonly_fields = [
        'subdir_id'
    ]
    search_fields = [
        'subdir'
    ]
    list_display = [
        'subdir'
    ]


@admin.register(emg_models.DownloadDescriptionLabel)
class DownloadDescriptionLabelAdmin(admin.ModelAdmin):
    readonly_fields = [
        'description_id'
    ]
    search_fields = [
        'description',
        'description_label'
    ]
    list_display = [
        'description_id',
        'description',
        'description_label'
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
        'group_type__group_type',
        'subdir__subdir',
        'file_format__format_name'
    ]


@admin.register(emg_models.AnalysisJobDownload)
class AnalysisJobDownloadAdmin(admin.ModelAdmin,
                               BaseDownloadAdmin):
    list_display = BaseDownloadAdmin.list_display + [
        'job'
    ]
    search_fields = BaseDownloadAdmin.search_fields + [
        'job__job_id'
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


@admin.register(emg_models.GenomeCatalogueDownload)
class GenomeCatalogueDownloadAdmin(admin.ModelAdmin, BaseDownloadAdmin):
    list_display = BaseDownloadAdmin.list_display + [
        'genome_catalogue'
    ]

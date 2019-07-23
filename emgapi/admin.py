#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.safestring import mark_safe

from . import models as emg_models


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
    list_display = ('study_id',
                    'project_id',
                    'study_name',)
    list_filter = ('is_public', )


class SuperStudyStudiesInline(admin.TabularInline):
    model = emg_models.SuperStudyStudy
    raw_id_fields = ('study',)


class SuperStudyBiomesInline(admin.TabularInline):
    model = emg_models.SuperStudyBiome
    raw_id_fields = ('biome',)


@admin.register(emg_models.SuperStudy)
class SuperStudyAdmin(admin.ModelAdmin):
    inlines = [SuperStudyStudiesInline, SuperStudyBiomesInline]
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image and obj.image.url:
            return mark_safe(
                '<img src="{}" width="150" height="150" />'.format(obj.image.url)
            )
        else:
            return ''

    image_tag.short_description = 'Image'

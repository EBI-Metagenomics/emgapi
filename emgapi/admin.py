#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django import forms

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

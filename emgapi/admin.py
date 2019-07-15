#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models as emg_models

admin.site.register(emg_models.Study)
admin.site.register(emg_models.Biome)


class SuperStudyStudiesInline(admin.TabularInline):
    model = emg_models.SuperStudyStudy
    raw_id_fields = ('study',)


class SuperStudyBiomesInline(admin.TabularInline):
    model = emg_models.SuperStudyBiome
    raw_id_fields = ('biome',)


@admin.register(emg_models.SuperStudy)
class SuperStudyAdmin(admin.ModelAdmin):
    inlines = [SuperStudyStudiesInline, SuperStudyBiomesInline]

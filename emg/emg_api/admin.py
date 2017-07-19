#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models as emg_models

admin.site.register(emg_models.Biome)
admin.site.register(emg_models.Study)
admin.site.register(emg_models.Sample)
admin.site.register(emg_models.Run)
admin.site.register(emg_models.Publication)

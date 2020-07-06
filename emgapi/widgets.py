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

from django.contrib.admin import widgets


class BiomePredictionWidget(widgets.ForeignKeyRawIdWidget):
    template_name = 'biome_predictor_widget.html'

    def __init__(self, *args, **kwargs):
        self.search_fields = kwargs.pop('search_fields', None)
        super().__init__(*args, **kwargs)

    class Media:
        js = ('js/biome_predictor.js',)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['search_fields'] = self.search_fields
        return context

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
import csv

from rest_framework import renderers
from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer, CSVStreamingRenderer as BaseCSVStreamingRenderer


class DefaultJSONRenderer(JSONRenderer):
    media_type = 'application/json'
    format = 'json'


class JSONLDRenderer(renderers.JSONRenderer):
    media_type = 'application/ld+json'
    format = 'ldjson'


class CSVStreamingRenderer(BaseCSVStreamingRenderer):
    """
    Based on rest_framework_csv.renderers.CSVStreamingRenderer
    combined with rest_framework_csv.renderers.PaginatedCSVRenderer
    """
    results_field = 'results'
    writer_opts = {'quoting': csv.QUOTE_NONNUMERIC}

    def render(self, data, *args, **kwargs):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
        return super(CSVStreamingRenderer, self).render(data, *args, **kwargs)

    def flatten_item(self, item):
        flat_item = super(CSVStreamingRenderer, self).flatten_item(item)
        for k, v in flat_item.items():
            if type(v) is str:
                flat_item[k] = v.replace('\n', ' ').replace('\r', ' ')
        return flat_item


class TSVRenderer(CSVRenderer):
    media_type = 'text/tsv'
    format = 'tsv'
    charset = 'iso-8859-1'

    def render(self, data, media_type=None, renderer_context=None):
        if type(data) == str:
            return data.encode(self.charset)
        return ''

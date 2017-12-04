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

from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer
from rest_framework_csv.misc import Echo


class DefaultJSONRenderer(JSONRenderer):
    media_type = 'application/json'
    format = 'application/json'


class CSVStreamingRenderer(CSVRenderer):
    """
    Based on rest_framework_csv.renderers.CSVStreamingRenderer,
    tabilize() call is not iterator-friendly.
    """

    def render(self, data, media_type=None, renderer_context={}):

        try:
            queryset = data['queryset']
            serializer = data['serializer']
            context = data['context']
        except KeyError:
            return None

        csv_buffer = Echo()
        csv_writer = csv.writer(csv_buffer)

        header_fields = list()
        for item in queryset:
            if len(header_fields) < 1:
                header_fields = list(serializer(item, context=context).fields)
                yield csv_writer.writerow(header_fields)
            items = serializer(item, context=context).data
            ordered = [items[column] for column in header_fields]
            yield csv_writer.writerow([
                elem for elem in ordered
            ])

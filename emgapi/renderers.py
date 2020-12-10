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

import math
import json
import csv

from rest_framework import renderers
from rest_framework.compat import six
from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer
from rest_framework_csv.misc import Echo
from rest_framework.utils.serializer_helpers import ReturnDict

from mongoengine.base.datastructures import BaseList


class DefaultJSONRenderer(JSONRenderer):
    media_type = 'application/json'
    format = 'json'


class JSONLDRenderer(renderers.JSONRenderer):
    media_type = 'application/ld+json'
    format = 'ldjson'


class CSVStreamingRenderer(CSVRenderer):
    """
    Based on rest_framework_csv.renderers.CSVStreamingRenderer,
    tabilize() call is not iterator-friendly.
    """

    def render(self, data, media_type=None, renderer_context={}):

        csv_buffer = Echo()
        csv_writer = csv.writer(csv_buffer)

        if isinstance(data, ReturnDict):
            yield csv_writer.writerow(data.keys())
            flat_row = self.flatten([data[column] for column in data.keys()])
            yield csv_writer.writerow(flat_row)
            return

        try:
            queryset = data['queryset']
            serializer = data['serializer']
            context = data['context']
        except KeyError:
            return None

        if isinstance(queryset, BaseList):
            # Handle SortedListField in the AnnotationModels
            # TODO: pending review as this has no pagination at the moment
            if not queryset:
                return None

            header_fields = list(serializer(queryset[0], context=context).fields)
            yield csv_writer.writerow(header_fields)

            for item in queryset:
                items = serializer(item, context=context).data
                ordered = [items[column] for column in header_fields]
                yield csv_writer.writerow(self.flatten(ordered))
            return

        total = queryset.count()
        page_size = 25

        header_fields = list(serializer(queryset.first(),
                             context=context).fields)
        yield csv_writer.writerow(header_fields)

        for page in range(0, math.ceil(total / page_size)):
            for item in queryset[page * page_size:(page + 1) * page_size]:
                items = serializer(item, context=context).data
                ordered = [items[column] for column in header_fields]
                yield csv_writer.writerow(self.flatten(ordered))

    def flatten(self, rowdata):
        """
        Flatten the data.
        Used to represent nested fields as json
        """
        new_row = []
        for elem in rowdata:
            if type(elem) is list or type(elem) is tuple:
                new_row.append(json.dumps(elem))
            else:
                new_row.append(elem)
        return new_row


class TSVRenderer(CSVRenderer):
    media_type = 'text/tsv'
    format = 'tsv'
    charset = 'iso-8859-1'

    def render(self, data, media_type=None, renderer_context=None):
        if isinstance(data, six.text_type):
            return data.encode(self.charset)
        return ''

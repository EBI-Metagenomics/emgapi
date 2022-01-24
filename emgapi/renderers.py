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

from django.utils import encoding
from rest_framework import renderers
from rest_framework_csv.renderers import CSVRenderer, CSVStreamingRenderer as BaseCSVStreamingRenderer
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework_json_api import utils
from rest_framework_json_api.renderers import JSONRenderer, BrowsableAPIRenderer


class DictAsDummyInstance(dict):
    """
    Add dot-notation getter and setters to a dict, e.g. when for a fake instance of a proxy model generated with
    queryset.values(...). Additionally look for a likely fieldname to dummy as a `pk`,
    e.g. if no 'pk' is set, but `lot_lan_pk` exists, set pk=lon_lat_pk.

    E.g. my_data = {'my_fake_pk': 1, 'some_proxy_field': 'some data'}
    my_fake_instance = DictAsDummyInstance(my_data)
    assert my_fake_instance.pk == 1
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self, 'pk', None) is None:
            for field in self.keys():
                if 'pk' in field:
                    self.pk = self[field]
                    break


class DefaultJSONRenderer(JSONRenderer):
    media_type = 'application/json'
    format = 'json'

    @classmethod
    def build_json_resource_obj(
            cls,
            fields,
            resource,
            resource_instance,
            resource_name,
            serializer,
            force_type_resolution=False,
            **kwargs
    ):
        if type(resource_instance) is dict:
            resource_instance = DictAsDummyInstance(resource_instance)
        resource_data = super().build_json_resource_obj(fields, resource, resource_instance, resource_name, serializer, force_type_resolution=force_type_resolution)

        relationships = resource_data.get('relationships')
        if relationships:
            for field_name in relationships.keys():
                if isinstance(fields.fields.get(field_name), HyperlinkedRelatedField):
                    id_field = getattr(fields.fields.get(field_name), 'lookup_field')
                    related_instance =  getattr(resource_instance, field_name)
                    id_value = getattr(related_instance, id_field, None)
                    if None not in [id_value, resource_data['relationships'][field_name]['data']]:
                        resource_data['relationships'][field_name]['data']['id'] = id_value

        current_serializer = fields.serializer
        context = current_serializer.context
        view = context.get("view", None)
        if hasattr(view, "relationship_lookup_field"):
            if view.relationship_lookup_field in resource:
                resource_data['id'] = resource.get(view.relationship_lookup_field, resource_data['id'])
        elif hasattr(view, 'lookup_field'):
            if view.lookup_field in resource:
                resource_data['id'] = encoding.force_str(resource.get(view.lookup_field, resource_data['id']))
        if "url" in fields and resource_data.get('id') is not None:
            custom_id = getattr(resource_instance, fields["url"].lookup_field)
            resource_data['id'] = encoding.force_str(custom_id)

        return resource_data


class EMGBrowsableAPIRenderer(BrowsableAPIRenderer):
    @classmethod
    def _get_included_serializers(cls, serializer, prefix="", already_seen=None):
        """Prevents browsable API showing options to include deeply nested serializers
        (e.g. ?include=biome.studies.biomes)"""
        if not already_seen:
            already_seen = set()

        if serializer in already_seen:
            return []

        included_serializers = []
        already_seen.add(serializer)

        for include, included_serializer in utils.get_included_serializers(
                serializer
        ).items():
            included_serializers.append(f"{prefix}{include}")

        return included_serializers


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
            if self.results_field in data:
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

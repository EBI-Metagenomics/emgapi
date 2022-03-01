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

import collections

from rest_framework_json_api.relations import (
    SerializerMethodResourceRelatedField,
    ManySerializerMethodHyperlinkedRelatedField,
    SkipDataMixin,
)
from rest_framework_json_api.utils import get_resource_type_from_instance

from rest_framework_json_api.relations import LINKS_PARAMS
LINKS_PARAMS.append('related_link_self_view_name')
LINKS_PARAMS.append('related_link_self_lookup_field')
LINKS_PARAMS.append('related_link_self_lookup_fields')


class HyperlinkedSerializerMethodResourceRelatedField(SerializerMethodResourceRelatedField):  # noqa

    related_link_self_view_name = None
    related_link_self_lookup_field = 'pk'

    def __init__(self, *args, **kwargs):
        self.related_link_self_view_name = kwargs.pop(
            'related_link_self_view_name',
            self.related_link_self_view_name)
        self.related_link_self_lookup_field = kwargs.pop(
            'related_link_self_lookup_field',
            self.related_link_self_lookup_field)
        super(HyperlinkedSerializerMethodResourceRelatedField, self) \
            .__init__(*args, **kwargs)

    def _to_representation(self, value):
        if getattr(self, 'pk_field', None) is not None:
            pk = self.pk_field.to_representation(value.pk)
        else:
            pk = getattr(value, self.related_link_self_lookup_field)

        resource_type = self.get_resource_type_from_included_serializer()
        if resource_type is None or not self._skip_polymorphic_optimization:
            resource_type = get_resource_type_from_instance(value)

        relation_data = collections.OrderedDict()
        relation_data['type'] = resource_type
        relation_data['id'] = str(pk)

        if self.related_link_self_view_name:
            request = self.context.get('request', None)
            self_kwargs = {
                self.related_link_self_lookup_field:
                    getattr(value, self.related_link_self_lookup_field)
            }
            self_link = self.get_url(
                'self', self.related_link_self_view_name, self_kwargs, request)
            relation_data['links'] = {'self': self_link}
        return relation_data

    def to_representation(self, value):
        try:
            return [self._to_representation(x) for x in value]
        except TypeError:
            return self._to_representation(value)


class HyperlinkedSerializerMethodResourceRelatedFieldWithoutData(SkipDataMixin, HyperlinkedSerializerMethodResourceRelatedField):
    many_cls = ManySerializerMethodHyperlinkedRelatedField

# TODO: clean up below
class AnalysisJobSerializerMethodResourceRelatedField(SerializerMethodResourceRelatedField):  # NOQA

    def get_links(self, obj=None, lookup_field='pk'):

        request = self.context.get('request', None)
        view = self.context.get('view', None)
        return_data = collections.OrderedDict()

        kwargs = {
            lookup_field: getattr(
                obj, lookup_field) if obj else view.kwargs[lookup_field]
        }

        self_kwargs = kwargs.copy()
        self_kwargs.update({
            'related_field':
                self.field_name if self.field_name else self.parent.field_name
        })
        self_link = self.get_url(
            'self', self.self_link_view_name, self_kwargs, request)

        related_kwargs = {
            self.related_link_url_kwarg: kwargs[self.related_link_lookup_field]
        }
        # TODO: add related_link_lookup_fields, a list
        related_kwargs['release_version'] = obj.pipeline.release_version

        related_link = self.get_url(
            'related', self.related_link_view_name, related_kwargs, request)

        if self_link:
            return_data.update({'self': self_link})
        if related_link:
            return_data.update({'related': related_link})
        return return_data


class DownloadSerializerMethodResourceRelatedField(SerializerMethodResourceRelatedField):  # noqa

    related_link_self_view_name = None
    related_link_self_lookup_field = 'pk'
    related_link_self_lookup_fields = ()

    def __init__(self, *args, **kwargs):
        self.related_link_self_view_name = kwargs.pop(
            'related_link_self_view_name',
            self.related_link_self_view_name)
        self.related_link_self_lookup_field = kwargs.pop(
            'related_link_self_lookup_field',
            self.related_link_self_lookup_field)
        self.related_link_self_lookup_fields = kwargs.pop(
            'related_link_self_lookup_fields',
            self.related_link_self_lookup_fields)
        super(DownloadSerializerMethodResourceRelatedField, self) \
            .__init__(*args, **kwargs)

    def _to_representation(self, value):
        if getattr(self, 'pk_field', None) is not None:
            pk = self.pk_field.to_representation(value.pk)
        else:
            pk = getattr(value, self.related_link_self_lookup_field)

        resource_type = self.get_resource_type_from_included_serializer()
        if resource_type is None or not self._skip_polymorphic_optimization:
            resource_type = get_resource_type_from_instance(value)

        relation_data = collections.OrderedDict()
        relation_data['type'] = resource_type
        relation_data['id'] = str(pk)

        if self.related_link_self_view_name:
            request = self.context.get('request', None)
            self_kwargs = {
                lookup_field:
                getattr(
                    value, lookup_field
                ) for lookup_field in self.related_link_self_lookup_fields
            }

            self_link = self.get_url(
                'self', self.related_link_self_view_name, self_kwargs, request)
            relation_data['links'] = {'self': self_link}
        return relation_data

    def to_representation(self, value):
        return [self._to_representation(x) for x in value]

    def get_links(self, obj=None, lookup_field='pk'):
        request = self.context.get('request', None)
        view = self.context.get('view', None)
        return_data = collections.OrderedDict()

        kwargs = {
            lookup_field:
            getattr(obj, lookup_field) if obj else view.kwargs[lookup_field]
        }

        self_kwargs = kwargs.copy()
        self_kwargs.update({
            'related_field':
                self.field_name if self.field_name else self.parent.field_name
        })
        self_link = self.get_url(
            'self', self.self_link_view_name, self_kwargs, request)

        related_kwargs = {
            self.related_link_url_kwarg: kwargs[self.related_link_lookup_field]
        }
        try:
            # TODO: add related_link_lookup_fields, a list
            related_kwargs['release_version'] = obj.pipeline.release_version
        except:  # noqa: E722
            pass

        related_link = self.get_url(
            'related', self.related_link_view_name, related_kwargs, request)

        if self_link:
            return_data.update({'self': self_link})
        if related_link:
            return_data.update({'related': related_link})
        return return_data

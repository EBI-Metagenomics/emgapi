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

from rest_framework_json_api import serializers
from rest_framework_json_api import relations

from rest_framework_mongoengine import serializers as m_serializers

from emgapi import models as emg_models
from emgapi import serializers as emg_serializers

from . import models as m_models


class AnnotationSerializer(m_serializers.DocumentSerializer,
                           serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapimetadata:annotations-detail',
        lookup_field='accession',
    )

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapimetadata:annotations-runs-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_analysis(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = m_models.Annotation
        fields = '__all__'


class RetrieveRunSerializer(emg_serializers.RetrieveRunSerializer):

    annotations = relations.SerializerMethodResourceRelatedField(
        source='get_annotations',
        model=m_models.Annotation,
        many=True,
        read_only=True,
        related_link_view_name='emgapimetadata:runs-pipelines-annotations-list',  # noqa
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_annotations(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()


emg_serializers.RetrieveRunSerializer = RetrieveRunSerializer

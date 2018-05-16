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

from . import models as m_models


class GoTermSerializer(m_serializers.DocumentSerializer,
                       serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:goterms-detail',
        lookup_field='accession',
    )

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:goterms-analysis-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_analysis(self, obj):
        return None

    class Meta:
        model = m_models.GoTerm
        fields = '__all__'


class InterproIdentifierSerializer(m_serializers.DocumentSerializer,
                                   serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:interproidentifier-detail',
        lookup_field='accession',
    )

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:interproidentifier-analysis-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_analysis(self, obj):
        return None

    class Meta:
        model = m_models.InterproIdentifier
        fields = '__all__'


class GoTermRetriveSerializer(m_serializers.DynamicDocumentSerializer,
                              serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:goterms-detail',
        lookup_field='accession',
    )

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:goterms-analysis-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_analysis(self, obj):
        return None

    count = serializers.IntegerField(required=False)

    class Meta:
        model = m_models.GoTerm
        fields = '__all__'


class InterproIdentifierRetriveSerializer(  # NOQA
    m_serializers.DynamicDocumentSerializer,
    serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:interproidentifier-detail',
        lookup_field='accession',
    )

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:interproidentifier-analysis-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_analysis(self, obj):
        return None

    count = serializers.IntegerField(required=False)

    class Meta:
        model = m_models.InterproIdentifier
        fields = '__all__'


class OrganismSerializer(m_serializers.DynamicDocumentSerializer,
                         serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:organisms-children-list',
        lookup_field='lineage',
    )

    # attributes
    # children = relations.SerializerMethodResourceRelatedField(
    #     source='get_children',
    #     model=m_models.Organism,
    #     many=True,
    #     read_only=True,
    #     related_link_view_name='emgapi_v1:organisms-children-list',
    #     related_link_url_kwarg='lineage',
    #     related_link_lookup_field='lineage',
    # )
    #
    # def get_children(self, obj):
    #     return None

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:organisms-analysis-list',
        related_link_url_kwarg='lineage',
        related_link_lookup_field='lineage'
    )

    def get_analysis(self, obj):
        return None

    class Meta:
        model = m_models.Organism
        exclude = (
            'id',
            'ancestors',
        )


class OrganismRetriveSerializer(OrganismSerializer):

    count = serializers.IntegerField(required=False)

    class Meta:
        model = m_models.Organism
        exclude = (
            'id',
            'ancestors',
        )

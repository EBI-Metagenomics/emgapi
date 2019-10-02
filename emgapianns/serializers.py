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

from rest_framework_mongoengine import serializers as m_serializers

from emgapi import fields as emg_fields

from . import models as m_models


class GoTermSerializer(m_serializers.DocumentSerializer,
                       serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:goterms-detail',
        lookup_field='accession',
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

    def get_analysis(self, obj):
        return None

    class Meta:
        model = m_models.InterproIdentifier
        fields = '__all__'


class KeggModuleSerializer(m_serializers.DocumentSerializer,
                           serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:keggmodule-detail',
        lookup_field='accession',
    )

    class Meta:
        model = m_models.KeggModule
        fields = '__all__'


class PfamSerializer(m_serializers.DocumentSerializer,
                     serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:pfam-detail',
        lookup_field='accession',
    )

    class Meta:
        model = m_models.PfamEntry
        fields = '__all__'


class KeggOrthologSerializer(m_serializers.DocumentSerializer,
                             serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:kegg-orthologs-detail',
        lookup_field='accession',
    )

    class Meta:
        model = m_models.KeggOrtholog
        fields = '__all__'


class GenomePropertySerializer(m_serializers.DocumentSerializer,
                               serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:genome-properties-detail',
        lookup_field='accession',
    )

    class Meta:
        model = m_models.GenomeProperty
        fields = '__all__'


class AntiSmashGeneClusterSerializer(m_serializers.DocumentSerializer,
                                     serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:antismash-gene-clusters-detail',
        lookup_field='accession',
    )

    class Meta:
        model = m_models.AntiSmashGeneCluster
        fields = '__all__'


class GoTermRetriveSerializer(m_serializers.DynamicDocumentSerializer,
                              serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:goterms-detail',
        lookup_field='accession',
    )

    count = serializers.IntegerField(required=False)

    class Meta:
        model = m_models.GoTerm
        fields = '__all__'


class InterproIdentifierRetriveSerializer(m_serializers.DynamicDocumentSerializer,
                                          serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:interproidentifier-detail',
        lookup_field='accession',
    )

    count = serializers.IntegerField(required=False)

    class Meta:
        model = m_models.InterproIdentifier
        fields = '__all__'


class KeggModuleRetrieveSerializer(m_serializers.DynamicDocumentSerializer,
                                   serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:keggmodule-detail',
        lookup_field='accession',
    )

    completeness = serializers.FloatField(required=True)
    matching_kos = serializers.ListField(required=True)
    missing_kos = serializers.ListField(required=True)

    class Meta:
        model = m_models.KeggModule
        fields = '__all__'


class PfamRetrieveSerializer(m_serializers.DynamicDocumentSerializer,
                             serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:pfam-detail',
        lookup_field='accession',
    )

    count = serializers.IntegerField(required=True)

    class Meta:
        model = m_models.PfamEntry
        fields = '__all__'


class KeggOrthologRetrieveSerializer(m_serializers.DynamicDocumentSerializer,
                                     serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:kegg-orthologs-detail',
        lookup_field='accession',
    )

    count = serializers.IntegerField(required=True)

    class Meta:
        model = m_models.KeggOrtholog
        fields = '__all__'


class GenomePropertyRetrieveSerializer(m_serializers.DynamicDocumentSerializer,
                                       serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:genome-properties-detail',
        lookup_field='accession',
    )

    count = serializers.IntegerField(required=True)

    class Meta:
        model = m_models.GenomeProperty
        fields = '__all__'


class AntiSmashGeneClusterRetrieveSerializer(m_serializers.DynamicDocumentSerializer,
                                             serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:antismash-gene-clusters-detail',
        lookup_field='accession',
    )

    count = serializers.IntegerField(required=True)

    class Meta:
        model = m_models.AntiSmashGeneCluster
        fields = '__all__'


class OrganismSerializer(m_serializers.DynamicDocumentSerializer,
                         serializers.HyperlinkedModelSerializer):

    url = emg_fields.OrganismHyperlinkedIdentityField(
        view_name='emgapi_v1:organisms-children-list',
        lookup_field='lineage',
    )

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


class AnalysisJobContigSerializer(m_serializers.DocumentSerializer):

    class Meta:
        model = m_models.AnalysisJobContig
        exclude = (
            'cogs',
            'keggs',
            'pfams',
            'gos',
            'interpros'
        )

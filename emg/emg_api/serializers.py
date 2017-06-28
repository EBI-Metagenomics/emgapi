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


import logging

from django.utils.text import Truncator

# from rest_framework import serializers
from rest_framework_json_api import serializers
from rest_framework_json_api import relations
from emg_api import models as emg_models

logger = logging.getLogger(__name__)


class BiomeSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='biomes-detail',
        lookup_field='biome_id',
    )

    # studies = serializers.HyperlinkedIdentityField(
    #     view_name='biomes-studies-list',
    #     lookup_field='biome_id',
    # )
    # studies = relations.ResourceRelatedField(
    #     queryset=emg_models.Biome.objects,
    #     many=True,
    #     related_link_view_name='biomes-studies-list',
    #     related_link_url_kwarg='biome_id',
    # )
    studies = relations.SerializerMethodResourceRelatedField(
        source='get_studies',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='biomes-studies-list',
        related_link_url_kwarg='biome_id',
    )

    def get_studies(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    # samples = serializers.HyperlinkedIdentityField(
    #     view_name='biomes-samples-list',
    #     lookup_field='biome_id',
    # )
    # samples = relations.ResourceRelatedField(
    #     queryset=emg_models.Biome.objects,
    #     many=True,
    #     related_link_view_name='biomes-samples-list',
    #     related_link_url_kwarg='biome_id',
    # )
    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='biomes-samples-list',
        related_link_url_kwarg='biome_id',
    )

    def get_samples(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = emg_models.Biome
        fields = '__all__'


# Publication serializer

class PublicationSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='publications-detail',
        lookup_field='pub_id',
    )

    # studies = serializers.HyperlinkedIdentityField(
    #     view_name='publications-studies-list',
    #     lookup_field='pub_id',
    # )
    studies = relations.ResourceRelatedField(
        queryset=emg_models.Publication.objects,
        many=True,
        related_link_view_name='publications-studies-list',
        related_link_url_kwarg='pub_id',
    )

    class Meta:
        model = emg_models.Publication
        fields = '__all__'


class SimplePublicationSerializer(PublicationSerializer):

    class Meta:
        model = emg_models.Publication
        fields = '__all__'


# Pipeline serializer

class PipelineSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='pipelines-detail',
        lookup_field='release_version',
    )

    # runs = relations.ResourceRelatedField(
    #     read_only=True,
    #     many=True,
    #     related_link_view_name='pipelines-runs-list',
    #     related_link_url_kwarg='release_version',
    # )
    runs = relations.SerializerMethodResourceRelatedField(
        source='get_runs',
        model=emg_models.Run,
        many=True,
        read_only=True,
        related_link_view_name='pipelines-runs-list',
        related_link_url_kwarg='release_version',
        related_link_lookup_field='release_version',
    )

    def get_runs(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = emg_models.Pipeline
        fields = '__all__'


# ExperimentType serializer

class ExperimentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = emg_models.ExperimentType
        fields = '__all__'


# Run serializer

class RunSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='runs-detail',
        lookup_field='accession',
    )

    # attributes
    analysis_status = serializers.SerializerMethodField()

    def get_analysis_status(self, obj):
        return obj.analysis_status.analysis_status

    # relationship
    pipeline = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='pipelines-detail',
        lookup_field='release_version',
    )

    sample = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='samples-detail',
        lookup_field='accession',
    )

    class Meta:
        model = emg_models.Run
        fields = '__all__'


# Sample serializer

class SampleSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='samples-detail',
        lookup_field='accession',
    )

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='biomes-detail',
        lookup_field='biome_id',
    )

    study = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='studies-detail',
        lookup_field='accession',
    )

    # runs = serializers.HyperlinkedIdentityField(
    #     view_name='samples-runs-list',
    #     lookup_field='accession',
    # )
    runs = relations.SerializerMethodResourceRelatedField(
        source='get_runs',
        model=emg_models.Run,
        many=True,
        read_only=True,
        related_link_view_name='samples-runs-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_runs(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = emg_models.Sample
        fields = '__all__'


class SimpleSampleSerializer(SampleSerializer):

    sample_desc = serializers.SerializerMethodField(
        'get_short_sample_desc')

    def get_short_sample_desc(self, obj):
        return Truncator(obj.sample_desc).chars(75)

    class Meta:
        model = emg_models.Sample
        fields = '__all__'


# Study serializer

class StudySerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='studies-detail',
        lookup_field='accession',
    )

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='biomes-detail',
        lookup_field='biome_id',
    )

    # publications = serializers.HyperlinkedIdentityField(
    #     view_name='studies-publications-list',
    #     lookup_field='accession',
    # )
    publications = relations.SerializerMethodResourceRelatedField(
        source='get_publications',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='studies-publications-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_publications(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    # samples = serializers.HyperlinkedIdentityField(
    #     view_name='studies-samples-list',
    #     lookup_field='accession',
    # )
    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='studies-samples-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_samples(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = emg_models.Study
        fields = '__all__'


class SimpleStudySerializer(StudySerializer):

    study_abstract = serializers.SerializerMethodField(
        'get_short_study_abstract')

    def get_short_study_abstract(self, obj):
        return Truncator(obj.study_abstract).chars(75)

    class Meta:
        model = emg_models.Study
        fields = '__all__'

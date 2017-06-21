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

# from rest_framework import serializers
from rest_framework_json_api import serializers
from rest_framework_json_api import relations
from emg_api import models as emg_models

logger = logging.getLogger(__name__)


class BiomeSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='biome-detail',
        lookup_field='biome_id',
    )

    # projects = serializers.HyperlinkedIdentityField(
    #     view_name='biome-projects-list',
    #     lookup_field='biome_id',
    # )
    # projects = relations.ResourceRelatedField(
    #     queryset=emg_models.Biome.objects,
    #     many=True,
    #     related_link_view_name='biome-projects-list',
    #     related_link_url_kwarg='biome_id',
    # )
    projects = relations.SerializerMethodResourceRelatedField(
        source='get_projects',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='biome-projects-list',
        related_link_url_kwarg='biome_id',
    )

    def get_projects(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    # samples = serializers.HyperlinkedIdentityField(
    #     view_name='biome-samples-list',
    #     lookup_field='biome_id',
    # )
    # samples = relations.ResourceRelatedField(
    #     queryset=emg_models.Biome.objects,
    #     many=True,
    #     related_link_view_name='biome-samples-list',
    #     related_link_url_kwarg='biome_id',
    # )
    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='biome-samples-list',
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

class SimplePublicationSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='publications-detail',
        lookup_field='pub_id',
    )

    class Meta:
        model = emg_models.Publication
        fields = '__all__'


class PublicationSerializer(SimplePublicationSerializer):

    # projects = serializers.HyperlinkedIdentityField(
    #     view_name='publications-projects-list',
    #     lookup_field='pub_id',
    # )
    projects = relations.ResourceRelatedField(
        queryset=emg_models.Publication.objects,
        many=True,
        related_link_view_name='publications-projects-list',
        related_link_url_kwarg='pub_id',
    )

    class Meta:
        model = emg_models.Publication
        fields = '__all__'


# PipelineRelease serializer

class PipelineReleaseSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    url = serializers.HyperlinkedIdentityField(
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    # analysis_jobs = relations.ResourceRelatedField(
    #     read_only=True,
    #     many=True,
    #     related_link_view_name='pipelines-jobs-list',
    #     related_link_url_kwarg='pipeline_id',
    # )
    analysis_jobs = relations.SerializerMethodResourceRelatedField(
        source='get_analysis_jobs',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='pipelines-jobs-list',
        related_link_url_kwarg='pipeline_id',
    )

    def get_analysis_jobs(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = emg_models.PipelineRelease
        fields = '__all__'


# ExperimentType serializer

class ExperimentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = emg_models.ExperimentType
        fields = '__all__'


# AnalysisStatus serializer

class AnalysisStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = emg_models.AnalysisStatus
        fields = '__all__'


# AnalysisJob serializer

class AnalysisJobSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='jobs-detail',
        lookup_field='job_id',
    )

    pipeline = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    analysis_status = AnalysisStatusSerializer()

    experiment_type = ExperimentTypeSerializer()

    pipeline = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    sample = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='samples-detail',
        lookup_field='sample_id',
    )

    class Meta:
        model = emg_models.AnalysisJob
        fields = '__all__'


# Sample serializer

class SimpleSampleSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='samples-detail',
        lookup_field='sample_id',
    )

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='biome-detail',
        lookup_field='biome_id',
    )

    project = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='projects-detail',
        lookup_field='ext_study_id',
    )

    analysis_jobs = relations.SerializerMethodResourceRelatedField(
        source='get_analysis_jobs',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='samples-jobs-list',
        related_link_url_kwarg='sample_id',
    )

    def get_analysis_jobs(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = emg_models.Sample
        fields = '__all__'


class SampleSerializer(SimpleSampleSerializer):

    # analysis_jobs = serializers.HyperlinkedIdentityField(
    #     view_name='samples-jobs-list',
    #     lookup_field='sample_id',
    # )
    analysis_jobs = relations.ResourceRelatedField(
        read_only=True,
        many=True,
        related_link_view_name='samples-jobs-list',
        related_link_url_kwarg='sample_id',
    )

    class Meta:
        model = emg_models.Sample
        fields = '__all__'


# Project serializer

class SimpleProjectSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='projects-detail',
        lookup_field='ext_study_id',
    )

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='biome-detail',
        lookup_field='biome_id',
    )

    # publications = serializers.HyperlinkedIdentityField(
    #     view_name='projects-publications-list',
    #     lookup_field='ext_study_id',
    # )
    publications = relations.SerializerMethodResourceRelatedField(
        source='get_publications',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='projects-publications-list',
        related_link_url_kwarg='ext_study_id',
        related_link_lookup_field='ext_study_id',
    )

    def get_publications(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    # samples = serializers.HyperlinkedIdentityField(
    #     view_name='projects-samples-list',
    #     lookup_field='ext_study_id',
    # )
    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='projects-samples-list',
        related_link_url_kwarg='ext_study_id',
        related_link_lookup_field='ext_study_id',
    )

    def get_samples(self, obj):
        # TODO: provide counter instead of paginating relationship
        # workaround https://github.com/django-json-api
        # /django-rest-framework-json-api/issues/178
        return ()

    class Meta:
        model = emg_models.Project
        fields = '__all__'


class ProjectSerializer(SimpleProjectSerializer):

    class Meta:
        model = emg_models.Project
        fields = '__all__'

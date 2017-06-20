# -*- coding: utf-8 -*-

import logging

# from rest_framework import serializers
from rest_framework_json_api import serializers
from rest_framework_json_api import relations
from emg_api import models as emg_models

logger = logging.getLogger(__name__)


class SimpleBiomeHierarchyTreeSerializer(serializers.
                                         HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='biome-detail',
        lookup_field='biome_id',
    )

    class Meta:
        model = emg_models.BiomeHierarchyTree
        fields = '__all__'


class BiomeHierarchyTreeSerializer(SimpleBiomeHierarchyTreeSerializer):

    # studies = serializers.HyperlinkedIdentityField(
    #     view_name='biome-studies-list',
    #     lookup_field='biome_id',
    # )
    studies = relations.ResourceRelatedField(
        queryset=emg_models.BiomeHierarchyTree.objects,
        many=True,
        related_link_view_name='biome-studies-list',
        related_link_url_kwarg='biome_id',
    )

    # samples = serializers.HyperlinkedIdentityField(
    #     view_name='biome-samples-list',
    #     lookup_field='biome_id',
    # )
    samples = relations.ResourceRelatedField(
        queryset=emg_models.BiomeHierarchyTree.objects,
        many=True,
        related_link_view_name='biome-samples-list',
        related_link_url_kwarg='biome_id',
    )

    class Meta:
        model = emg_models.BiomeHierarchyTree
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


# PipelineRelease serializer

class SimplePipelineReleaseSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    class Meta:
        model = emg_models.PipelineRelease
        fields = '__all__'


class PipelineReleaseSerializer(SimplePipelineReleaseSerializer):

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

class SimpleAnalysisJobSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='jobs-detail',
        lookup_field='job_id',
    )

    analysis_status = AnalysisStatusSerializer()

    experiment_type = ExperimentTypeSerializer()

    pipeline = serializers.HyperlinkedRelatedField(
        read_only=True,
        many=True,
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    class Meta:
        model = emg_models.AnalysisJob
        exclude = (
            'sample',
            'pipeline',
        )


class AnalysisJobSerializer(SimpleAnalysisJobSerializer):

    pipeline = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    class Meta:
        model = emg_models.AnalysisJob
        exclude = (
            'sample',
        )


# Sample serializer

class SimpleSampleSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='samples-detail',
        lookup_field='sample_id',
    )

    class Meta:
        model = emg_models.Sample
        exclude = (
            'biome',
            'study',
        )


class SampleSerializer(SimpleSampleSerializer):

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='biome-detail',
        lookup_field='biome_id',
    )

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

    study = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='studies-detail',
        lookup_field='study_id',
    )

    class Meta:
        model = emg_models.Sample
        fields = '__all__'


# Study serializer

class SimpleStudySerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='studies-detail',
        lookup_field='study_id',
    )

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='biome-detail',
        lookup_field='biome_id',
    )

    # publications = serializers.HyperlinkedIdentityField(
    #     view_name='studies-publications-list',
    #     lookup_field='study_id',
    # )
    publications = relations.ResourceRelatedField(
        read_only=True,
        many=True,
        related_link_view_name='studies-publications-list',
        related_link_url_kwarg='study_id',
    )

    class Meta:
        model = emg_models.Study
        fields = '__all__'


class StudySerializer(SimpleStudySerializer):

    # samples = serializers.HyperlinkedIdentityField(
    #     view_name='studies-samples-list',
    #     lookup_field='study_id',
    # )
    samples = relations.ResourceRelatedField(
        read_only=True,
        many=True,
        related_link_view_name='studies-samples-list',
        related_link_url_kwarg='study_id',
    )

    class Meta:
        model = emg_models.Study
        exclude = ('publications',)

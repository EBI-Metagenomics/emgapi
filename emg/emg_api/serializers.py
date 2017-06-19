# -*- coding: utf-8 -*-

from rest_framework import serializers
# from rest_framework_json_api import serializers
from emg_api import models as emg_models


class BiomeHierarchyTreeSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='biome-detail',
        lookup_field='biome_id',
    )

    studies = serializers.HyperlinkedIdentityField(
        view_name='biome-studies-list',
        lookup_field='biome_id',
    )
    samples = serializers.HyperlinkedIdentityField(
        view_name='biome-samples-list',
        lookup_field='biome_id',
    )

    class Meta:
        model = emg_models.BiomeHierarchyTree
        fields = '__all__'


# Publication serializer

class PublicationSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='publications-detail',
        lookup_field='pub_id',
    )

    studies = serializers.HyperlinkedIdentityField(
        view_name='publications-studies-list',
        lookup_field='pub_id',
    )

    class Meta:
        model = emg_models.Publication
        fields = '__all__'


# AnalysisJob serializer

class PipelineReleaseSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='pipelines-detail',
        lookup_field='pipeline_id',
    )

    analysis_jobs = serializers.HyperlinkedIdentityField(
        view_name='pipelines-jobs-list',
        lookup_field='pipeline_id',
    )

    class Meta:
        model = emg_models.PipelineRelease
        fields = '__all__'


class ExperimentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = emg_models.ExperimentType
        fields = '__all__'


class AnalysisStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = emg_models.AnalysisStatus
        fields = '__all__'


class AnalysisJobSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='jobs-detail',
        lookup_field='job_id',
    )

    analysis_status = AnalysisStatusSerializer()
    pipeline = PipelineReleaseSerializer()
    experiment_type = ExperimentTypeSerializer()

    class Meta:
        model = emg_models.AnalysisJob
        exclude = ('sample',)


# Sample serializer

class SampleSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='samples-detail',
        lookup_field='sample_id',
    )

    analysis_jobs = serializers.HyperlinkedIdentityField(
        view_name='samples-jobs-list',
        lookup_field='sample_id',
    )

    study = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='studies-detail',
        lookup_field='study_id',
    )

    biome = BiomeHierarchyTreeSerializer()

    class Meta:
        model = emg_models.Sample
        fields = '__all__'


# Study serializer

class StudySerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='studies-detail',
        lookup_field='study_id',
    )

    biome = BiomeHierarchyTreeSerializer()

    publications = serializers.HyperlinkedIdentityField(
        view_name='studies-publications-list',
        lookup_field='study_id',
    )

    samples = serializers.HyperlinkedIdentityField(
        view_name='studies-samples-list',
        lookup_field='study_id',
    )

    class Meta:
        model = emg_models.Study
        fields = '__all__'

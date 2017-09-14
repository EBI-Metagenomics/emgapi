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

# from django.utils.text import Truncator
from rest_framework.reverse import reverse

# from rest_framework import serializers
from rest_framework_json_api import serializers
from rest_framework_json_api import relations

from . import models as emg_models
from . import relations as emg_relations

# TODO: add related_link_lookup_fields, a list
from emgapianns import models as m_models

logger = logging.getLogger(__name__)


class ExplicitFieldsModelSerializer(serializers.ModelSerializer):
    """
    Retrieve object with explicit fields. This is compatible with `include`
    although relationship has to be present in `fields`.
    """

    def __init__(self, *args, **kwargs):
        super(ExplicitFieldsModelSerializer, self).__init__(*args, **kwargs)

        fields = self.context['request'].query_params.get('fields')
        if fields:
            fields = fields.split(',')
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class BiomeSerializer(ExplicitFieldsModelSerializer,
                      serializers.HyperlinkedModelSerializer):

    included_serializers = {}

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi:biomes-detail',
        lookup_field='lineage',
    )

    # relationships
    studies = relations.SerializerMethodResourceRelatedField(
        source='get_studies',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:biomes-studies-list',
        related_link_url_kwarg='lineage',
        related_link_lookup_field='lineage',
    )

    def get_studies(self, obj):
        return None

    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:biomes-samples-list',
        related_link_url_kwarg='lineage',
        related_link_lookup_field='lineage',
    )

    def get_samples(self, obj):
        return None

    children = relations.SerializerMethodResourceRelatedField(
        source='get_children',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:biomes-children-list',
        related_link_url_kwarg='lineage',
        related_link_lookup_field='lineage',
    )

    def get_children(self, obj):
        return None

    # counters
    studies_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Biome
        exclude = (
            'lft',
            'rgt',
            'depth',
        )


class Top10BiomeSerializer(BiomeSerializer):

    study_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Biome
        exclude = (
            'lft',
            'rgt',
            'depth',
        )


# Publication serializer

class PublicationSerializer(ExplicitFieldsModelSerializer,
                            serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'studies': 'emgapi.serializers.StudySerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi:publications-detail',
        lookup_field='pubmed_id',
    )

    # relationships
    studies = relations.SerializerMethodResourceRelatedField(
        source='get_studies',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:publications-studies-list',
        related_link_url_kwarg='pubmed_id',
        related_link_lookup_field='pubmed_id',
    )

    def get_studies(self, obj):
        return None

    # counters
    studies_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Publication
        fields = (
            'url',
            'pubmed_id',
            'pubmed_central_id',
            'pub_title',
            'pub_abstract',
            'authors',
            'doi',
            'isbn',
            'published_year',
            'pub_type',
            'issue',
            'volume',
            'raw_pages',
            'iso_journal',
            'medline_journal',
            'pub_url',
            'studies_count',
            'studies',
        )


# PipelineTool serializer

class PipelineToolHyperlinkedField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        kwargs = {
            'tool_name': obj.tool_name,
            'version': obj.version
        }
        return reverse(
            view_name, kwargs=kwargs, request=request, format=format)


class PipelineToolSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    # workaround to provide multiple values in PK
    id = serializers.ReadOnlyField(source="multiple_pk")

    url = PipelineToolHyperlinkedField(
        view_name='emgapi:pipeline-tools-version-detail',
        lookup_field='tool_name',
    )

    # relationships
    pipelines = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_pipelines',
        model=emg_models.Pipeline,
        related_link_self_view_name='emgapi:pipelines-detail',
        related_link_self_lookup_field='release_version'
    )

    def get_pipelines(self, obj):
        return obj.pipelines.all()

    class Meta:
        model = emg_models.PipelineTool
        fields = (
            'id',
            'url',
            'tool_name',
            'description',
            'web_link',
            'version',
            'exe_command',
            'configuration_file',
            'notes',
            'pipelines',
        )


# Pipeline serializer

class PipelineSerializer(ExplicitFieldsModelSerializer,
                         serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'tools': 'emgapi.serializers.PipelineToolSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi:pipelines-detail',
        lookup_field='release_version',
    )

    # relationships
    studies = relations.SerializerMethodResourceRelatedField(
        source='get_studies',
        model=emg_models.Study,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:pipelines-studies-list',
        related_link_url_kwarg='release_version',
        related_link_lookup_field='release_version',
    )

    def get_studies(self, obj):
        return None

    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:pipelines-samples-list',
        related_link_url_kwarg='release_version',
        related_link_lookup_field='release_version',
    )

    def get_samples(self, obj):
        return None

    tools = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        source='get_tools',
        model=emg_models.PipelineTool,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:pipelines-pipeline-tools-list',
        related_link_url_kwarg='release_version',
        related_link_lookup_field='release_version',
        related_link_self_lookup_field='tool_name'
    )

    def get_tools(self, obj):
        return obj.tools.all().distinct()

    # counters
    samples_count = serializers.IntegerField()

    analysis_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Pipeline
        fields = '__all__'


# ExperimentType serializer

class ExperimentTypeSerializer(ExplicitFieldsModelSerializer,
                               serializers.ModelSerializer):

    included_serializers = {}

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi:experiment-types-detail',
        lookup_field='experiment_type',
    )

    # relationships
    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:experiment-types-samples-list',
        related_link_url_kwarg='experiment_type',
        related_link_lookup_field='experiment_type',
    )

    def get_samples(self, obj):
        return None

    # counters
    samples_count = serializers.IntegerField()

    runs_count = serializers.IntegerField()

    class Meta:
        model = emg_models.ExperimentType
        exclude = ('experiment_type_id',)


# Run serializer

class RunSerializer(ExplicitFieldsModelSerializer,
                    serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'sample': 'emgapi.serializers.SampleSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi:runs-detail',
        lookup_field='accession'
    )

    # attributes
    accession = serializers.SerializerMethodField()

    def get_accession(self, obj):
        return obj.accession

    sample_accession = serializers.SerializerMethodField()

    def get_sample_accession(self, obj):
        return obj.sample.accession

    study_accession = serializers.SerializerMethodField()

    def get_study_accession(self, obj):
        return obj.sample.study.accession

    # relationship
    experiment_type = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi:experiment-types-detail',
        lookup_field='experiment_type'
    )

    # relationships
    sample = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi:samples-detail',
        lookup_field='accession'
    )

    pipelines = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_pipelines',
        model=emg_models.Pipeline,
        related_link_self_view_name='emgapi:pipelines-detail',
        related_link_self_lookup_field='release_version'
    )

    def get_pipelines(self, obj):
        # TODO: push that to queryset
        return emg_models.Pipeline.objects \
            .filter(analysis__accession=obj.accession)

    analysis = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_analysis',
        model=emg_models.AnalysisJob,
        related_link_view_name='emgapi:runs-pipelines-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_analysis(self, obj):
        return None

    class Meta:
        model = emg_models.Run
        exclude = (
            'analysis_status',
            'run_status_id',
        )


class AnalysisJobHyperlinkedField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        kwargs = {
            'accession': obj.accession,
            'release_version': obj.pipeline.release_version
        }
        return reverse(
            view_name, kwargs=kwargs, request=request, format=format)


class AnalysisSerializer(RunSerializer):

    # workaround to provide multiple values in PK
    id = serializers.ReadOnlyField(source="multiple_pk")

    url = AnalysisJobHyperlinkedField(
        view_name='emgapi:runs-pipelines-detail',
        lookup_field='accession'
    )

    # attributes
    pipeline_version = serializers.SerializerMethodField()

    def get_pipeline_version(self, obj):
        return obj.pipeline.release_version

    # relationships
    go_terms = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(  # NOQA
        source='get_goterms',
        model=m_models.GoTerm,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:runs-pipelines-goterms-list',  # noqa
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_goterms(self, obj):
        return None

    go_slim = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(  # NOQA
        source='get_goslim',
        model=m_models.GoTerm,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:runs-pipelines-goslim-list',  # noqa
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_goslim(self, obj):
        return None

    interpro_identifiers = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(  # NOQA
        source='get_interproidentifier',
        model=m_models.InterproIdentifier,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:runs-pipelines-interpro-list',  # noqa
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_interproidentifier(self, obj):
        return None

    metadata = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(
        source='get_metadata',
        model=emg_models.AnalysisJobAnn,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:runs-pipelines-metadata-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_metadata(self, obj):
        return None

    class Meta:
        model = emg_models.AnalysisJob
        fields = (
            'id',
            'url',
            'accession',
            'pipeline_version',
            'sample_accession',
            'study_accession',
            'submit_time',
            'experiment_type',
            'metadata',
            'sample',
            'go_slim',
            'go_terms',
            'interpro_identifiers',
        )


# SampleAnn serializer

# class MetadataHyperlinkedField(serializers.HyperlinkedIdentityField):
#
#     def get_url(self, obj, view_name, request, format):
#         kwargs = {
#             'name': obj.var.var_name,
#             'value': obj.var_val_ucv
#         }
#         return reverse(
#             view_name, kwargs=kwargs, request=request, format=format)

class BaseMetadataSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    # workaround to provide multiple values in PK
    id = serializers.ReadOnlyField(source="multiple_pk")

    # attributes
    var_name = serializers.SerializerMethodField()

    def get_var_name(self, obj):
        return obj.var.var_name

    var_value = serializers.SerializerMethodField()

    def get_var_value(self, obj):
        return obj.var_val_ucv

    unit = serializers.SerializerMethodField()

    def get_unit(self, obj):
        return obj.units


class SampleAnnSerializer(BaseMetadataSerializer):

    # attributes
    # sample_accession = serializers.SerializerMethodField()
    #
    # def get_sample_accession(self, obj):
    #     return obj.sample.accession

    # relationships
    sample = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi:samples-detail',
        lookup_field='accession'
    )

    class Meta:
        model = emg_models.SampleAnn
        fields = (
            'id',
            'var_name',
            'var_value',
            'unit',
            # 'sample_accession',
            'sample',
        )


class AnalysisJobAnnSerializer(BaseMetadataSerializer):

    class Meta:
        model = emg_models.AnalysisJobAnn
        fields = (
            'id',
            'var_name',
            'var_value',
            'unit',
        )


# Sample serializer

class SampleSerializer(ExplicitFieldsModelSerializer,
                       serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'biome': 'emgapi.serializers.BiomeSerializer',
        'runs': 'emgapi.serializers.RunSerializer',
        'metadata': 'emgapi.serializers.SampleAnnSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi:samples-detail',
        lookup_field='accession'
    )

    # attributes
    study_accession = serializers.SerializerMethodField()

    def get_study_accession(self, obj):
        return obj.study.accession

    latitude = serializers.FloatField()

    longitude = serializers.FloatField()

    # relationships
    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi:biomes-detail',
        lookup_field='lineage',
    )

    study = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi:studies-detail',
        lookup_field='accession',
    )

    runs = relations.SerializerMethodResourceRelatedField(
        source='get_runs',
        model=emg_models.Run,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:samples-runs-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_runs(self, obj):
        return None

    metadata = relations.SerializerMethodResourceRelatedField(
        source='get_metadata',
        model=emg_models.SampleAnn,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:samples-metadata-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_metadata(self, obj):
        return None

    # counters
    runs_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Sample
        fields = (
            'url',
            'study_accession',
            'runs_count',
            'accession',
            'analysis_completed',
            'collection_date',
            'geo_loc_name',
            'longitude',
            'latitude',
            'sample_desc',
            'environment_biome',
            'environment_feature',
            'environment_material',
            'sample_name',
            'sample_alias',
            'host_tax_id',
            'species',
            'last_update',
            'biome',
            'study',
            'runs',
            'metadata',
        )


class RetrieveSampleSerializer(SampleSerializer):

    included_serializers = {
        'biome': 'emgapi.serializers.BiomeSerializer',
        'study': 'emgapi.serializers.StudySerializer',
        'runs': 'emgapi.serializers.RunSerializer',
        'metadata': 'emgapi.serializers.SampleAnnSerializer',
    }


# Study serializer

class StudySerializer(ExplicitFieldsModelSerializer,
                      serializers.HyperlinkedModelSerializer):

    included_serializers = {
        # 'publications': 'emgapi.serializers.PublicationSerializer',
        'biomes': 'emgapi.serializers.BiomeSerializer',
        'samples': 'emgapi.serializers.SampleSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi:studies-detail',
        lookup_field='accession',
    )

    # relationships
    biomes = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_biomes',
        model=emg_models.Biome,
        related_link_view_name='emgapi:studies-biomes-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi:biomes-detail',
        related_link_self_lookup_field='lineage'
    )

    def get_biomes(self, obj):
        biomes = obj.samples.values('biome_id').distinct()
        return emg_models.Biome.objects \
            .filter(pk__in=biomes)

    publications = relations.SerializerMethodResourceRelatedField(
        source='get_publications',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:studies-publications-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_publications(self, obj):
        return None

    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='emgapi:studies-samples-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_samples(self, obj):
        return None

    # counters
    samples_count = serializers.IntegerField()

    runs_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Study
        exclude = (
            # TODO: remove biome when schema updated
            'biome',
            'is_public',
            'experimental_factor',
            'submission_account_id',
            'result_directory',
            'first_created',
            'study_status',
        )


class RetrieveStudySerializer(StudySerializer):

    included_serializers = {
        'publications': 'emgapi.serializers.PublicationSerializer',
        'samples': 'emgapi.serializers.SampleSerializer',
        'biomes': 'emgapi.serializers.BiomeSerializer',
    }

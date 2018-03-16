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

from rest_framework_json_api import serializers
from rest_framework_json_api import relations

from . import models as emg_models
from . import relations as emg_relations
from . import fields as emg_fields

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


# Serializers

class ResourceSerializer(serializers.Serializer):

    id = serializers.CharField(read_only=True, max_length=20)
    count = serializers.IntegerField()

    class Meta:
        model = emg_models.Resource
        fields = '__all__'


class TokenSerializer(serializers.Serializer):

    id = serializers.CharField(read_only=True)
    token = serializers.CharField(max_length=50)

    class Meta:
        model = emg_models.Token
        fields = '__all__'


# Model Serializers


class BiomeSerializer(ExplicitFieldsModelSerializer,
                      serializers.HyperlinkedModelSerializer):

    included_serializers = {}

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:biomes-detail',
        lookup_field='lineage',
    )

    # relationships
    studies = relations.SerializerMethodResourceRelatedField(
        source='get_studies',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:biomes-studies-list',
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
        related_link_view_name='emgapi_v1:biomes-samples-list',
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
        related_link_view_name='emgapi_v1:biomes-children-list',
        related_link_url_kwarg='lineage',
        related_link_lookup_field='lineage',
    )

    def get_children(self, obj):
        return None

    # counters
    samples_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Biome
        exclude = (
            'lft',
            'rgt',
            'depth',
        )


class Top10BiomeSerializer(BiomeSerializer):

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
        view_name='emgapi_v1:publications-detail',
        lookup_field='pubmed_id',
    )

    # relationships
    studies = relations.SerializerMethodResourceRelatedField(
        source='get_studies',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:publications-studies-list',
        related_link_url_kwarg='pubmed_id',
        related_link_lookup_field='pubmed_id',
    )

    def get_studies(self, obj):
        return None

    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:publications-samples-list',
        related_link_url_kwarg='pubmed_id',
        related_link_lookup_field='pubmed_id',
    )

    def get_samples(self, obj):
        return None

    # counters
    studies_count = serializers.IntegerField()
    samples_count = serializers.IntegerField()

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
            'samples_count',
            'studies',
            'samples',
        )


# PipelineTool serializer

class PipelineToolSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    # workaround to provide multiple values in PK
    id = serializers.ReadOnlyField(source="multiple_pk")

    url = emg_fields.PipelineToolHyperlinkedField(
        view_name='emgapi_v1:pipeline-tools-version-detail',
        lookup_field='tool_name',
    )

    # relationships
    pipelines = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_pipelines',
        model=emg_models.Pipeline,
        related_link_self_view_name='emgapi_v1:pipelines-detail',
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
        view_name='emgapi_v1:pipelines-detail',
        lookup_field='release_version',
    )

    # relationships
    # studies = relations.SerializerMethodResourceRelatedField(
    #     source='get_studies',
    #     model=emg_models.Study,
    #     many=True,
    #     read_only=True,
    #     related_link_view_name='emgapi_v1:pipelines-studies-list',
    #     related_link_url_kwarg='release_version',
    #     related_link_lookup_field='release_version',
    # )
    #
    # def get_studies(self, obj):
    #     return None

    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:pipelines-samples-list',
        related_link_url_kwarg='release_version',
        related_link_lookup_field='release_version',
    )

    def get_samples(self, obj):
        return None

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:pipelines-analysis-list',
        related_link_url_kwarg='release_version',
        related_link_lookup_field='release_version',
    )

    def get_analysis(self, obj):
        return None

    tools = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        source='get_tools',
        model=emg_models.PipelineTool,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:pipelines-pipeline-tools-list',
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
        view_name='emgapi_v1:experiment-types-detail',
        lookup_field='experiment_type',
    )

    # relationships
    samples = relations.SerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:experiment-types-samples-list',
        related_link_url_kwarg='experiment_type',
        related_link_lookup_field='experiment_type',
    )

    def get_samples(self, obj):
        return None

    runs = relations.SerializerMethodResourceRelatedField(
        source='get_runs',
        model=emg_models.Run,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:experiment-types-runs-list',
        related_link_url_kwarg='experiment_type',
        related_link_lookup_field='experiment_type',
    )

    def get_runs(self, obj):
        return None

    analysis = relations.SerializerMethodResourceRelatedField(
        source='get_analysis',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:experiment-types-analysis-list',
        related_link_url_kwarg='experiment_type',
        related_link_lookup_field='experiment_type',
    )

    def get_analysis(self, obj):
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
        'study': 'emgapi.serializers.StudySerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:runs-detail',
        lookup_field='accession'
    )

    # attributes
    accession = serializers.SerializerMethodField()

    def get_accession(self, obj):
        return obj.accession

    experiment_type = serializers.SerializerMethodField()

    def get_experiment_type(self, obj):
        return obj.experiment_type.experiment_type

    # relationships
    sample = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:samples-detail',
        lookup_field='accession'
    )

    study = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:studies-detail',
        lookup_field='accession'
    )

    pipelines = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_pipelines',
        model=emg_models.Pipeline,
        related_link_self_view_name='emgapi_v1:pipelines-detail',
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
        related_link_view_name='emgapi_v1:runs-pipelines-list',
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


# Download serializer
class BaseDownloadSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    id = serializers.ReadOnlyField(source="alias")

    url = emg_fields.DownloadHyperlinkedIdentityField(
        view_name='emgapi_v1:studydownload-detail',
        lookup_field='alias',
    )

    description = serializers.SerializerMethodField()

    def get_description(self, obj):
        return {
            'label': obj.description.description_label,
            'description': obj.description.description
        }

    group_type = serializers.SerializerMethodField()

    def get_group_type(self, obj):
        return obj.group_type.group_type

    file_format = serializers.SerializerMethodField()

    def get_file_format(self, obj):
        return {
            'name': obj.file_format.format_name,
            'extension': obj.file_format.format_extension,
            'compression': obj.file_format.compression,
        }

    pipeline = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:pipelines-detail',
        lookup_field='release_version'
    )

    class Meta:
        model = emg_models.StudyDownload
        fields = (
            'id',
            'url',
            'alias',
            'file_format',
            'description',
            'group_type',
            'pipeline',
        )


class StudyDownloadSerializer(BaseDownloadSerializer):

    study = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:studies-detail',
        lookup_field='accession'
    )

    class Meta:
        model = emg_models.StudyDownload
        fields = (
            'id',
            'url',
            'alias',
            'file_format',
            'description',
            'group_type',
            'pipeline',
            'study',
        )


class AnalysisJobDownloadSerializer(BaseDownloadSerializer):

    analysis = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:runs-pipelines-detail',
        lookup_field='accession'
    )

    class Meta:
        model = emg_models.AnalysisJobDownload
        fields = (
            'id',
            'url',
            'alias',
            'file_format',
            'description',
            'group_type',
            'pipeline',
            'analysis',
        )


class BaseAnalysisSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'sample': 'emgapi.serializers.SampleSerializer',
        'study': 'emgapi.serializers.StudySerializer',
    }

    # workaround to provide multiple values in PK
    id = serializers.ReadOnlyField(source="multiple_pk")

    url = emg_fields.AnalysisJobHyperlinkedField(
        view_name='emgapi_v1:runs-pipelines-detail',
        lookup_field='accession'
    )

    # attributes
    accession = serializers.SerializerMethodField()

    def get_accession(self, obj):
        return obj.accession

    experiment_type = serializers.SerializerMethodField()

    def get_experiment_type(self, obj):
        return obj.experiment_type.experiment_type

    pipeline_version = serializers.SerializerMethodField()

    def get_pipeline_version(self, obj):
        return obj.pipeline.release_version

    analysis_summary = serializers.ListField()

    # relationships
    sample = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:samples-detail',
        lookup_field='accession'
    )

    study = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:studies-detail',
        lookup_field='accession'
    )

    downloads = emg_relations.DownloadSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_downloads',
        model=emg_models.AnalysisJobDownload,
        related_link_view_name='emgapi_v1:analysisdownload-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi_v1:analysisdownload-detail',
        related_link_self_lookup_field='alias',
        related_link_self_lookup_fields=(
            'accession', 'release_version', 'alias'
        )
    )

    def get_downloads(self, obj):
        return obj.downloads

    taxonomy = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(
        source='get_taxonomy',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:runs-pipelines-taxonomy-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy(self, obj):
        return None

    taxonomy_lsu = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(  # NOQA
        source='get_taxonomy_lsu',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:runs-pipelines-taxonomy-lsu-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy_lsu(self, obj):
        return None

    taxonomy_ssu = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(  # NOQA
        source='get_taxonomy_ssu',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:runs-pipelines-taxonomy-ssu-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy_ssu(self, obj):
        return None

    class Meta:
        model = emg_models.AnalysisJob
        exclude = (
            're_run_count',
            'input_file_name',
            'result_directory',
            'is_production_run',
            'run_status_id',
            'job_operator',
            'submit_time',
            'analysis_status',
        )


class AnalysisSerializer(BaseAnalysisSerializer):

    go_terms = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(
        source='get_goterms',
        model=m_models.GoTerm,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:runs-pipelines-goterms-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_goterms(self, obj):
        return None

    go_slim = emg_relations.AnalysisJobSerializerMethodResourceRelatedField(
        source='get_goslim',
        model=m_models.GoTerm,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:runs-pipelines-goslim-list',
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
        related_link_view_name='emgapi_v1:runs-pipelines-interpro-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_interproidentifier(self, obj):
        return None


# Sample serializer

class BaseMetadataSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    # workaround to provide multiple values in PK
    id = serializers.ReadOnlyField(source="multiple_pk")

    # attributes
    key = serializers.SerializerMethodField()

    def get_key(self, obj):
        return obj.var.var_name

    value = serializers.SerializerMethodField()

    def get_value(self, obj):
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
        view_name='emgapi_v1:samples-detail',
        lookup_field='accession'
    )

    class Meta:
        model = emg_models.SampleAnn
        fields = (
            'id',
            'key',
            'value',
            'unit',
            # 'sample_accession',
            'sample',
        )


class SampleSerializer(ExplicitFieldsModelSerializer,
                       serializers.HyperlinkedModelSerializer):

    included_serializers = {
        # 'studies': 'emgapi.serializers.StudySerializer',
        'biome': 'emgapi.serializers.BiomeSerializer',
        'runs': 'emgapi.serializers.RunSerializer',
        # 'metadata': 'emgapi.serializers.SampleAnnSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:samples-detail',
        lookup_field='accession'
    )

    # attributes
    biosample = serializers.SerializerMethodField()

    def get_biosample(self, obj):
        return obj.primary_accession

    latitude = serializers.FloatField()

    longitude = serializers.FloatField()

    sample_metadata = serializers.ListField()

    # relationships
    # metadata = relations.SerializerMethodResourceRelatedField(
    #     source='get_metadata',
    #     model=emg_models.SampleAnn,
    #     many=True,
    #     read_only=True,
    #     related_link_view_name='emgapi_v1:samples-metadata-list',
    #     related_link_url_kwarg='accession',
    #     related_link_lookup_field='accession'
    # )
    #
    # def get_metadata(self, obj):
    #     return None

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:biomes-detail',
        lookup_field='lineage',
    )

    studies = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        source='get_studies',
        model=emg_models.Study,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:samples-studies-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi_v1:studies-detail',
        related_link_self_lookup_field='accession'
    )

    def get_studies(self, obj):
        return obj.studies.available(self.context['request'])

    runs = relations.SerializerMethodResourceRelatedField(
        source='get_runs',
        model=emg_models.Run,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:samples-runs-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_runs(self, obj):
        return None

    # counters
    # runs_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Sample
        exclude = (
            'primary_accession',
            'is_public',
            'metadata_received',
            'sequencedata_received',
            'sequencedata_archived',
            'submission_account_id',
        )


class RetrieveSampleSerializer(SampleSerializer):

    included_serializers = {
        'biome': 'emgapi.serializers.BiomeSerializer',
        # 'studies': 'emgapi.serializers.StudySerializer',
        'runs': 'emgapi.serializers.RunSerializer',
        # 'metadata': 'emgapi.serializers.SampleAnnSerializer',
    }


# Study serializer
class StudySerializer(ExplicitFieldsModelSerializer,
                      serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'biomes': 'emgapi.serializers.BiomeSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:studies-detail',
        lookup_field='accession',
    )

    bioproject = serializers.SerializerMethodField()

    def get_bioproject(self, obj):
        return obj.project_id

    # relationships
    biomes = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_biomes',
        model=emg_models.Biome,
        related_link_view_name='emgapi_v1:studies-biomes-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi_v1:biomes-detail',
        related_link_self_lookup_field='lineage'
    )

    def get_biomes(self, obj):
        biomes = obj.samples \
            .available(self.context['request']) \
            .values('biome_id').distinct()
        return emg_models.Biome.objects \
            .filter(pk__in=biomes)

    publications = relations.SerializerMethodResourceRelatedField(
        source='get_publications',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:studies-publications-list',
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
        related_link_view_name='emgapi_v1:studies-samples-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_samples(self, obj):
        return None

    # counters
    samples_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Study
        exclude = (
            # TODO: remove biome when schema updated
            'biome',
            'project_id',
            'is_public',
            'experimental_factor',
            'submission_account_id',
            'result_directory',
            'first_created',
            'study_status',
            'author_email',
            'author_name',
        )


class RetrieveStudySerializer(StudySerializer):

    included_serializers = {
        'publications': 'emgapi.serializers.PublicationSerializer',
        'samples': 'emgapi.serializers.SampleSerializer',
        'biomes': 'emgapi.serializers.BiomeSerializer',
    }

    downloads = emg_relations.DownloadSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_downloads',
        model=emg_models.StudyDownload,
        related_link_view_name='emgapi_v1:studydownload-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi_v1:studydownload-detail',
        related_link_self_lookup_field='alias',
        related_link_self_lookup_fields=(
            'accession', 'release_version', 'alias'
        )
    )

    def get_downloads(self, obj):
        return obj.downloads

    # studies = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
    #     many=True,
    #     read_only=True,
    #     source='get_studies',
    #     model=emg_models.Study,
    #     related_link_view_name='emgapi_v1:studies-studies-list',
    #     related_link_url_kwarg='accession',
    #     related_link_lookup_field='accession',
    #     related_link_self_view_name='emgapi_v1:studies-detail',
    #     related_link_self_lookup_field='accession'
    # )
    #
    # def get_studies(self, obj):
    #     return emg_models.Study.objects \
    #         .filter(
    #             samples__in=obj.samples.available(
    #                 self.context['request'])
    #         ).available(self.context['request'])

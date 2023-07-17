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

from collections import OrderedDict

from django.db.models import Q

from rest_framework import serializers as drf_serializers
from rest_framework.serializers import FileField, ChoiceField

from rest_framework_json_api import serializers, relations, utils

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
class BiomeSkinnySerializer(ExplicitFieldsModelSerializer,
                            serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:biomes-detail',
        lookup_field='lineage',
    )

    children = relations.SerializerMethodHyperlinkedRelatedField(
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

    class Meta:
        model = emg_models.Biome
        exclude = (
            'lft',
            'rgt',
            'depth',
        )


class BiomeSerializer(ExplicitFieldsModelSerializer,
                      serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:biomes-detail',
        lookup_field='lineage',
    )

    # relationships
    studies = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_studies',
        model=emg_models.Biome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:biomes-studies-list',
        related_link_url_kwarg='lineage',
        related_link_lookup_field='lineage',
    )

    def get_studies(self, obj):
        return obj.studies

    samples = relations.SerializerMethodHyperlinkedRelatedField(
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

    children = relations.SerializerMethodHyperlinkedRelatedField(
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

    genomes = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_genomes',
        model=emg_models.Genome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:biomes-genomes-list',
        related_link_url_kwarg='lineage',
        related_link_lookup_field='lineage',
    )

    def get_genomes(self, obj):
        return None

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

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:publications-detail',
        lookup_field='pubmed_id',
    )

    # relationships
    studies = relations.SerializerMethodHyperlinkedRelatedField(
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

    samples = relations.SerializerMethodHyperlinkedRelatedField(
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

    samples = relations.SerializerMethodHyperlinkedRelatedField(
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

    analyses = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_analyses',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:pipelines-analyses-list',
        related_link_url_kwarg='release_version',
        related_link_lookup_field='release_version',
    )

    def get_analyses(self, obj):
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

    analyses_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Pipeline
        fields = '__all__'

    class JSONAPIMeta:
        included_resources = ['tools']


# ExperimentType serializer

class ExperimentTypeSerializer(ExplicitFieldsModelSerializer,
                               serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:experiment-types-detail',
        lookup_field='experiment_type',
    )

    # relationships
    samples = relations.SerializerMethodHyperlinkedRelatedField(
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

    runs = relations.SerializerMethodHyperlinkedRelatedField(
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

    analyses = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_analyses',
        model=emg_models.AnalysisJob,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:experiment-types-analyses-list',
        related_link_url_kwarg='experiment_type',
        related_link_lookup_field='experiment_type',
    )

    def get_analyses(self, obj):
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
        'assemblies': 'emgapi.serializers.AssemblySerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:runs-detail',
        lookup_field='accession'
    )

    # attributes
    experiment_type = serializers.SerializerMethodField()

    def get_experiment_type(self, obj):
        if obj.experiment_type is not None:
            return obj.experiment_type.experiment_type
        return None

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

    assemblies = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_assemblies',
        model=emg_models.Assembly,
        related_link_view_name='emgapi_v1:runs-assemblies-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi_v1:assemblies-detail',
        related_link_self_lookup_field='accession'
    )

    def get_assemblies(self, obj):
        return obj.assemblies.available(self.context['request'])

    pipelines = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_pipelines',
        model=emg_models.Pipeline,
        related_link_self_view_name='emgapi_v1:pipelines-detail',
        related_link_self_lookup_field='release_version'
    )

    def get_pipelines(self, obj):
        # TODO: push this to the manager
        return emg_models.Pipeline.objects \
            .filter(analyses__run=obj)

    analyses = emg_relations.HyperlinkedSerializerMethodResourceRelatedFieldWithoutData(
        many=True,
        read_only=True,
        source='get_analyses',
        model=emg_models.AnalysisJob,
        related_link_view_name='emgapi_v1:runs-analyses-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_analyses(self, obj):
        return None

    class Meta:
        model = emg_models.Run
        exclude = (
            'is_suppressed',
            'suppression_reason',
            'suppressed_at',
        )


class BaseDownloadSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    id = serializers.ReadOnlyField(source='alias')

    description = serializers.SerializerMethodField()

    def get_description(self, obj):
        if obj.description is not None:
            return {
                'label': obj.description.description_label,
                'description': obj.description.description
            }
        return None

    group_type = serializers.SerializerMethodField()

    def get_group_type(self, obj):
        if obj.group_type is not None:
            return obj.group_type.group_type
        return None

    file_format = serializers.SerializerMethodField()

    def get_file_format(self, obj):
        if obj.file_format is not None:
            return {
                'name': obj.file_format.format_name,
                'extension': obj.file_format.format_extension,
                'compression': obj.file_format.compression,
            }
        return None

    file_checksum = serializers.SerializerMethodField()

    def get_file_checksum(self, obj):
        return {
            'checksum': obj.file_checksum,
            'checksum-algorithm': obj.checksum_algorithm.name if obj.checksum_algorithm else ''
        }


class AssemblySerializer(ExplicitFieldsModelSerializer,
                         serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'runs': 'emgapi.serializers.RunSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:assemblies-detail',
        lookup_field='accession'
    )

    # attributes
    experiment_type = serializers.SerializerMethodField()

    def get_experiment_type(self, obj):
        if obj.experiment_type is not None:
            return obj.experiment_type.experiment_type
        return None

    # relationships
    runs = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_runs',
        model=emg_models.Run,
        related_link_view_name='emgapi_v1:assemblies-runs-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi_v1:runs-detail',
        related_link_self_lookup_field='accession'
    )

    def get_runs(self, obj):
        return obj.runs.available(self.context['request'])

    samples = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_samples',
        model=emg_models.Sample,
        related_link_self_view_name='emgapi_v1:samples-detail',
        related_link_self_lookup_field='accession'
    )

    def get_samples(self, obj):
        return obj.samples.available(self.context['request'])

    analyses = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_analyses',
        model=emg_models.AnalysisJob,
        related_link_view_name='emgapi_v1:assemblies-analyses-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
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
            .filter(analyses__assembly=obj)

    def get_analyses(self, obj):
        return None

    extra_annotations = relations.SerializerMethodHyperlinkedRelatedField(
        many=True,
        read_only=True,
        source='get_extra_annotations',
        model=emg_models.AssemblyExtraAnnotation,
        related_link_view_name='emgapi_v1:assembly-extra-annotations-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_extra_annotations(self, obj):
        return None

    class Meta:
        model = emg_models.Assembly
        exclude = (
            'study',
            'is_suppressed',
            'suppressed_at',
            'suppression_reason',
        )


class AssemblyExtraAnnotationSerializer(BaseDownloadSerializer):
    url = emg_fields.DownloadHyperlinkedIdentityField(
        view_name='emgapi_v1:assembly-extra-annotations-detail',
        lookup_field='alias',
    )

    class Meta:
        model = emg_models.AssemblyExtraAnnotation
        fields = (
            'id',
            'url',
            'alias',
            'file_format',
            'description',
            'group_type',
            'file_checksum'
        )


class RunExtraAnnotationSerializer(BaseDownloadSerializer):
    url = emg_fields.DownloadHyperlinkedIdentityField(
        view_name='emgapi_v1:run-extra-annotations-detail',
        lookup_field='alias',
    )

    class Meta:
        model = emg_models.RunExtraAnnotation
        fields = (
            'id',
            'url',
            'alias',
            'file_format',
            'description',
            'group_type',
            'file_checksum'
        )

class RetrieveAssemblySerializer(AssemblySerializer):

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
        pipelines = obj.analyses.values('pipeline_id').distinct()
        return emg_models.Pipeline.objects.filter(pk__in=pipelines)


class BasePipelineDownloadSerializer(BaseDownloadSerializer):
    pipeline = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:pipelines-detail',
        lookup_field='release_version'
    )


class StudyDownloadSerializer(BasePipelineDownloadSerializer):

    url = emg_fields.DownloadHyperlinkedIdentityField(
        view_name='emgapi_v1:studydownload-detail',
        lookup_field='alias',
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
            'file_checksum'
        )


class AnalysisJobDownloadSerializer(BasePipelineDownloadSerializer):

    url = emg_fields.DownloadHyperlinkedIdentityField(
        view_name='emgapi_v1:analysisdownload-detail',
        lookup_field='alias',
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
            'file_checksum'
        )


class BaseAnalysisSerializer(ExplicitFieldsModelSerializer,
                             serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'sample': 'emgapi.serializers.SampleSerializer',
        'downloads': 'emgapi.serializers.AnalysisJobDownloadSerializer',
        'assembly': 'emgapi.serializers.AssemblySerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:analyses-detail',
        lookup_field='accession'
    )

    # attributes
    accession = serializers.SerializerMethodField()

    def get_accession(self, obj):
        return obj.accession

    experiment_type = serializers.SerializerMethodField()

    def get_experiment_type(self, obj):
        if obj.experiment_type is not None:
            return obj.experiment_type.experiment_type
        return None

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

    downloads = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_downloads',
        model=emg_models.AnalysisJobDownload,
        related_link_view_name='emgapi_v1:analysisdownload-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_downloads(self, obj):
        if 'downloads' in utils.get_included_resources(self.context['request']):
            return obj.downloads
        return None

    taxonomy = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_taxonomy',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-taxonomy-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy(self, obj):
        return None

    taxonomy_lsu = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_taxonomy_lsu',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-taxonomy-lsu-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy_lsu(self, obj):
        return None

    taxonomy_ssu = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_taxonomy_ssu',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-taxonomy-ssu-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy_ssu(self, obj):
        return None

    taxonomy_itsonedb = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_taxonomy_itsonedb',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-taxonomy-itsonedb-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy_itsonedb(self, obj):
        return None

    taxonomy_itsunite = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_taxonomy_unite',
        model=m_models.Organism,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-taxonomy-unite-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_taxonomy_itsunite(self, obj):
        return None

    def get_taxonomy_unite(self, obj):
        return None

    go_terms = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_goterms',
        model=m_models.GoTerm,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-goterms-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_go_terms(self, obj):
        return None

    go_slim = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_goslim',
        model=m_models.GoTerm,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-goslim-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_go_slim(self, obj):
        return None

    interpro_identifiers = relations.SerializerMethodHyperlinkedRelatedField(  # NOQA
        source='get_interproidentifier',
        model=m_models.InterproIdentifier,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-interpro-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_interpro_identifiers(self, obj):
        return None

    antismash_gene_clusters = relations.SerializerMethodHyperlinkedRelatedField(  # NOQA
        source='get_antismashgeneclusters',
        model=m_models.AntiSmashGeneCluster,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-antismash-gene-clusters-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_antismash_gene_clusters(self, obj):
        return None

    genome_properties = relations.SerializerMethodHyperlinkedRelatedField(  # NOQA
        source='get_genomeproperties',
        model=m_models.GenomeProperty,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:analysis-genome-properties-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession'
    )

    def get_genome_properties(self, obj):
        return None

    class Meta:
        model = emg_models.AnalysisJob
        exclude = (
            're_run_count',
            'input_file_name',
            'result_directory',
            'is_production_run',
            'job_operator',
            'submit_time',
            'analysis_status',
            'pipeline',
            'external_run_ids',
            'secondary_accession',
            'is_suppressed',
            'suppressed_at',
            'suppression_reason',
        )


class AnalysisSerializer(BaseAnalysisSerializer):

    run = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:runs-detail',
        lookup_field='accession'
    )

    assembly = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:assemblies-detail',
        lookup_field='accession',
    )

    analysis_status = serializers.SerializerMethodField()

    def get_analysis_status(self, obj):
        if obj.analysis_status is not None:
            return obj.analysis_status.analysis_status
        return None

    class Meta:
        model = emg_models.AnalysisJob
        exclude = (
            're_run_count',
            'input_file_name',
            'result_directory',
            'is_production_run',
            'job_operator',
            'submit_time',
            'pipeline',
            'external_run_ids',
            'secondary_accession',
            'is_suppressed',
            'suppressed_at',
            'suppression_reason',
        )


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
            'sample',
        )


class SampleSerializer(ExplicitFieldsModelSerializer,
                       serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'biome': 'emgapi.serializers.BiomeSkinnySerializer',
        'runs': 'emgapi.serializers.RunSerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:samples-detail',
        lookup_field='accession'
    )

    # attributes
    biosample = serializers.CharField()

    latitude = serializers.FloatField()

    longitude = serializers.FloatField()

    sample_metadata = serializers.ListField()

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
        related_link_self_lookup_field='accession',
        allow_null=False
    )

    def get_studies(self, obj):
        return obj.studies.available(self.context['request'])

    runs = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        source='get_runs',
        model=emg_models.Run,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:samples-runs-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_runs(self, obj):
        if 'runs' in utils.get_included_resources(self.context['request']):
            return obj.runs.all()
        return None

    class Meta:
        model = emg_models.Sample
        exclude = (
            'primary_accession',
            'is_private',
            'is_suppressed',
            'suppression_reason',
            'suppressed_at',
            'metadata_received',
            'sequencedata_received',
            'sequencedata_archived',
            'submission_account_id',
        )


class RetrieveSampleSerializer(SampleSerializer):

    included_serializers = {
        'biome': 'emgapi.serializers.BiomeSkinnySerializer',
        'runs': 'emgapi.serializers.RunSerializer',
    }


class SampleGeoCoordinateSerializer(ExplicitFieldsModelSerializer,
                                    serializers.HyperlinkedModelSerializer):

    # workaround to provide multiple values in PK
    id = serializers.ReadOnlyField(source='lon_lat_pk')
    pk = serializers.ReadOnlyField(source='lon_lat_pk')

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    samples_count = serializers.IntegerField()

    class Meta:
        model = emg_models.SampleGeoCoordinate
        unique_together = (('latitude', 'longitude'),)
        fields = (
            'id',
            'pk',
            'longitude',
            'latitude',
            'samples_count'
        )


class SuperStudySerializer(ExplicitFieldsModelSerializer,
                           serializers.HyperlinkedModelSerializer):

    biomes_count = serializers.IntegerField()

    included_serializers = {
        'biomes': 'emgapi.serializers.BiomeSkinnySerializer',
        'flagship_studies': 'emgapi.serializers.StudySerializer',
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:super-studies-detail',
        lookup_field='super_study_id',
    )

    flagship_studies = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_flagship_studies',
        model=emg_models.Study,
        related_link_view_name='emgapi_v1:super-studies-flagship-studies-list',
        related_link_url_kwarg='super_study_id',
        related_link_lookup_field='super_study_id',
        related_link_self_view_name='emgapi_v1:studies-detail',
        related_link_self_lookup_field='accession',
    )

    def get_flagship_studies(self, obj):
        if 'flagship_studies' in utils.get_included_resources(self.context['request']):
            return obj.flagship_studies.all()
        return None

    # related studies are inferred from the biomes of the Super Sample
    related_studies = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_related_studies',
        model=emg_models.Study,
        related_link_view_name='emgapi_v1:super-studies-related-studies-list',
        related_link_url_kwarg='super_study_id',
        related_link_lookup_field='super_study_id',
        related_link_self_view_name='emgapi_v1:studies-detail',
        related_link_self_lookup_field='accession',
    )

    def get_related_studies(self, obj):
        return None

    biomes = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_biomes',
        model=emg_models.Biome,
        related_link_view_name='emgapi_v1:super-studies-biomes-list',
        related_link_url_kwarg='super_study_id',
        related_link_lookup_field='super_study_id',
        related_link_self_view_name='emgapi_v1:biomes-detail',
        related_link_self_lookup_field='lineage'
    )

    def get_biomes(self, obj):
        if 'biomes' in utils.get_included_resources(self.context['request']):
            return obj.biomes.all()
        return None

    related_genome_catalogues = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_related_genome_catalogues',
        model=emg_models.GenomeCatalogue,
        related_link_view_name='emgapi_v1:super-studies-related-genome-catalogues-list',
        related_link_url_kwarg='super_study_id',
        related_link_lookup_field='super_study_id',
        related_link_self_view_name='emgapi_v1:genome-catalogue-detail',
        related_link_self_lookup_field='accession',
    )

    def get_related_genome_catalogues(self, obj):
        if 'genome_catalogues' in utils.get_included_resources(self.context['request']):
            return obj.genome_catalgoues.all()
        return None

    class Meta:
        model = emg_models.SuperStudy
        fields = (
            'super_study_id',
            'title',
            'url_slug',
            'description',
            'url',
            'image_url',
            'biomes',
            'biomes_count',
            'flagship_studies',
            'related_studies',
            'related_genome_catalogues',
        )


class StudySerializer(ExplicitFieldsModelSerializer,
                      serializers.HyperlinkedModelSerializer):

    included_serializers = {
        'biomes': 'emgapi.serializers.BiomeSkinnySerializer',
        'downloads': 'emgapi.serializers.StudyDownloadSerializer',
        'samples': 'emgapi.serializers.SampleSerializer'
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:studies-detail',
        lookup_field='accession',
    )

    accession = serializers.SerializerMethodField()

    def get_accession(self, obj):
        return obj.accession

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
        related_link_self_lookup_field='lineage',
    )

    def get_biomes(self, obj):
        biomes = obj.samples \
            .available(self.context['request']) \
            .values('biome_id').distinct()
        return emg_models.Biome.objects \
            .filter(pk__in=biomes)

    publications = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        source='get_publications',
        model=emg_models.Publication,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:studies-publications-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_publications(self, obj):
        if 'publications' in utils.get_included_resources(self.context['request']):
            return obj.publications.all()
        return None

    downloads = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_downloads',
        model=emg_models.StudyDownload,
        related_link_view_name='emgapi_v1:studydownload-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_downloads(self, obj):
        if 'downloads' in utils.get_included_resources(self.context['request']):
            return obj.downloads.all()
        return None

    samples = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        source='get_samples',
        model=emg_models.Sample,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:studies-samples-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_samples(self, obj):
        if 'samples' in utils.get_included_resources(self.context['request']):
            return obj.samples.all()
        return None

    analyses = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_analyses',
        model=emg_models.AnalysisJob,
        related_link_view_name='emgapi_v1:studies-analyses-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_analyses(self, obj):
        if 'analyses' in utils.get_included_resources(self.context['request']):
            return obj.analyses.all()
        return None

    geocoordinates = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_geocoordinates',
        model=emg_models.SampleGeoCoordinate,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:studies-geoloc-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_geocoordinates(self, obj):
        return None

    # counters
    samples_count = serializers.IntegerField()

    class Meta:
        model = emg_models.Study
        exclude = (
            # TODO: remove biome when schema updated
            'biome',
            'project_id',
            'experimental_factor',
            'submission_account_id',
            'result_directory',
            'first_created',
            'study_status',
            'author_email',
            'author_name',
            'is_suppressed',
            'suppression_reason',
            'suppressed_at',
        )


class RetrieveStudySerializer(StudySerializer):

    included_serializers = {
        'publications': 'emgapi.serializers.PublicationSerializer',
        'samples': 'emgapi.serializers.SampleSerializer',
        'analyses': 'emgapi.serializers.AnalysisSerializer',
        'biomes': 'emgapi.serializers.BiomeSerializer',
        'downloads': 'emgapi.serializers.StudyDownloadSerializer',
    }

    studies = emg_relations.HyperlinkedSerializerMethodResourceRelatedField(
        many=True,
        read_only=True,
        source='get_studies',
        model=emg_models.Study,
        related_link_view_name='emgapi_v1:studies-studies-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
        related_link_self_view_name='emgapi_v1:studies-detail',
        related_link_self_lookup_field='accession'
    )

    def get_studies(self, obj):
        samples = emg_models.StudySample.objects \
            .filter(study_id=obj.study_id) \
            .values("sample_id")
        studies = emg_models.StudySample.objects \
            .filter(
                Q(sample_id__in=samples),
                ~Q(study_id=obj.study_id)
            ).values("study_id")
        queryset = emg_models.Study.objects.filter(study_id__in=studies) \
            .available(self.context['request']).distinct()
        return queryset


class LDStudySerializer(drf_serializers.ModelSerializer):

    identifier = serializers.SerializerMethodField()

    def get_identifier(self, obj):
        return obj.accession

    alternateName = serializers.SerializerMethodField() # noqa

    def get_alternateName(self, obj):  # noqa
        return obj.secondary_accession

    dateModified = serializers.SerializerMethodField() # noqa

    def get_dateModified(self, obj):  # noqa
        return obj.last_update

    name = serializers.SerializerMethodField() # noqa

    def get_name(self, obj):
        return obj.study_name

    description = serializers.SerializerMethodField()

    def get_description(self, obj):
        return obj.study_abstract

    url = drf_serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:studies-detail',
        lookup_field='accession',
    )

    def to_representation(self, instance):
        data = super(LDStudySerializer, self).to_representation(instance)
        return OrderedDict([
            ("@context", "http://schema.org"),
            ("@type", "DataCatalog"),
        ] + list(OrderedDict(data).items()))

    class Meta:
        model = emg_models.Study
        fields = (
            'identifier',
            'url',
            'alternateName',
            'name',
            'description',
            'dateModified',
        )


class LDAnalysisSerializer(drf_serializers.ModelSerializer):

    identifier = serializers.SerializerMethodField()

    def get_identifier(self, obj):
        return obj.accession

    dateModified = serializers.SerializerMethodField() # noqa

    def get_dateModified(self, obj):  # noqa
        return obj.complete_time

    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.external_run_ids

    keywords = serializers.SerializerMethodField()

    def get_keywords(self, obj):
        _keywords = [
            obj.instrument_platform,
            obj.instrument_model
        ]
        return _keywords

    measurementTechnique = serializers.SerializerMethodField() # noqa

    def get_measurementTechnique(self, obj):  # noqa
        if obj.experiment_type is not None:
            return obj.experiment_type.experiment_type
        return None

    url = drf_serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:analyses-detail',
        lookup_field='accession'
    )

    def to_representation(self, instance):
        data = super(LDAnalysisSerializer, self).to_representation(instance)
        return OrderedDict([
            ("@context", "http://schema.org"),
            ("@type", "Dataset"),
        ] + list(OrderedDict(data).items()))

    class Meta:
        model = emg_models.AnalysisJob
        fields = (
            'identifier',
            'url',
            'name',
            'measurementTechnique',
            'keywords',
            'dateModified',
        )


class CogCountSerializer(ExplicitFieldsModelSerializer):
    name = serializers.CharField(source='cog.name')
    description = serializers.CharField(source='cog.description')

    class Meta:
        model = emg_models.GenomeCogCounts
        fields = ('name', 'description', 'genome_count')


class KeggClassMatchSerializer(ExplicitFieldsModelSerializer):
    class_id = serializers.CharField(source='kegg_class.class_id')
    name = serializers.CharField(source='kegg_class.name')

    class Meta:
        model = emg_models.GenomeKeggClassCounts
        fields = ('class_id', 'name', 'genome_count')


class KeggModuleMatchSerializer(ExplicitFieldsModelSerializer):
    name = serializers.CharField(source='kegg_module.name')
    description = serializers.CharField(source='kegg_module.description')

    class Meta:
        model = emg_models.GenomeKeggModuleCounts
        fields = ('name', 'description', 'genome_count')


class AntiSmashCountSerializer(ExplicitFieldsModelSerializer):
    name = serializers.CharField(source='antismash_genecluster.name')
    description = serializers.CharField(source='antismash_genecluster.description')

    class Meta:
        model = emg_models.GenomeAntiSmashGCCounts
        fields = ('name', 'description', 'genome_count')


class GenomeSerializer(ExplicitFieldsModelSerializer):
    included_serializers = {
        'download': 'emgapi.serializers.GenomeDownloadSerializer',
        'catalogue': 'emgapi.serializers.GenomeCatalogueSerializer'
    }
    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:genomes-detail',
        lookup_field='accession',
    )

    downloads = relations.SerializerMethodHyperlinkedRelatedField(
        many=True,
        read_only=True,
        source='get_downloads',
        model=emg_models.GenomeDownload,
        related_link_view_name='emgapi_v1:genome-download-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_downloads(self, obj):
        return None

    kegg_class_matches = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_kegg_class_matches',
        model=emg_models.KeggClass,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:genome-kegg-class-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_kegg_class_matches(self, obj):
        return None

    kegg_modules_matches = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_kegg_module_matches',
        model=emg_models.KeggModule,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:genome-kegg-module-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_kegg_modules_matches(self, obj):
        return None

    cog_matches = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_cog_matches',
        model=emg_models.CogCat,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:genome-cog-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_cog_matches(self, obj):
        return None

    antismash_geneclusters = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_antismash_geneclusters',
        model=emg_models.AntiSmashGC,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:genome-antismash-genecluster-list',
        related_link_url_kwarg='accession',
        related_link_lookup_field='accession',
    )

    def get_antismash_geneclusters(self, obj):
        return None

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:biomes-detail',
        lookup_field='lineage',
    )

    catalogue = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:genome-catalogues-detail',
        lookup_field='catalogue_id'
    )

    geographic_range = serializers.ListField()

    geographic_origin = serializers.CharField()

    class Meta:
        model = emg_models.Genome
        exclude = ('result_directory',
                   'kegg_classes',
                   'kegg_modules',
                   'genome_set',
                   'pangenome_geographic_range',
                   'geo_origin')


class GenomeDownloadSerializer(BaseDownloadSerializer):
    url = emg_fields.DownloadHyperlinkedIdentityField(
        view_name='emgapi_v1:genome-download-detail',
        lookup_field='alias',
    )

    class Meta:
        model = emg_models.GenomeDownload
        fields = (
            'id',
            'url',
            'alias',
            'file_format',
            'description',
            'group_type',
            'file_checksum'
        )


def get_mag_catalogue_choices():
    return [
        (cat.catalogue_id, cat.name,)
        for cat in emg_models.GenomeCatalogue.objects.all()
    ]


class GenomeUploadSearchSerializer(drf_serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super(GenomeUploadSearchSerializer, self).__init__(*args, **kwargs)
        self.fields['mag_catalogue'] = ChoiceField(get_mag_catalogue_choices())

    file_uploaded = FileField()

    class Meta:
        fields = ['file_uploaded', 'mag_catalog']


class GenomeFragmentSearchSerializer(drf_serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super(GenomeFragmentSearchSerializer, self).__init__(*args, **kwargs)
        self.fields['catalogues_filter'] = serializers.MultipleChoiceField(get_mag_catalogue_choices())

    seq = serializers.CharField(
        min_length=50,
        max_length=5000,
        allow_null=False,
        help_text='DNA sequence (gene fragment) between 50 and 5000bp long.'
    )
    threshold = serializers.FloatField(
        min_value=0,
        max_value=1.0,
        default=0.4,
        help_text='Minimum k-mer similarity fraction for a MAG to be included in results. Default 0.4.'
    )

    class Meta:
        fields = ['seq', 'catalogues_filter', 'threshold']


class GenomeCatalogueDownloadSerializer(BaseDownloadSerializer):
    url = emg_fields.DownloadHyperlinkedIdentityField(
        view_name='emgapi_v1:genome-catalogue-downloads-detail',
        lookup_field='alias',
    )

    class Meta:
        model = emg_models.GenomeCatalogueDownload
        fields = (
            'id',
            'url',
            'alias',
            'file_format',
            'description',
            'group_type',
            'file_checksum'
        )


class GenomeCatalogueSerializer(ExplicitFieldsModelSerializer,
                                serializers.HyperlinkedModelSerializer):
    included_serializers = {
        'genomes': 'emgapi.serializers.GenomeSerializer',
        'download': 'emgapi.serializers.GenomeCatalogueDownloadSerializer'
    }

    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:genome-catalogues-detail',
        lookup_field='catalogue_id',
    )

    genomes = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_genomes',
        model=emg_models.Genome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:genome-catalogue-genomes-list',
        related_link_url_kwarg='catalogue_id',
        related_link_lookup_field='catalogue_id',
    )

    biome = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='emgapi_v1:biomes-detail',
        lookup_field='lineage',
    )

    def get_genomes(self, obj):
        return None

    # counters
    genome_count = serializers.IntegerField()

    downloads = relations.SerializerMethodHyperlinkedRelatedField(
        many=True,
        read_only=True,
        source='get_downloads',
        model=emg_models.GenomeCatalogueDownload,
        related_link_view_name='emgapi_v1:genome-catalogue-downloads-list',
        related_link_url_kwarg='catalogue_id',
        related_link_lookup_field='catalogue_id',
    )

    def get_downloads(self, obj):
        return None

    class Meta:
        model = emg_models.GenomeCatalogue
        fields = (
            'url',
            'name',
            'biome',
            'description',
            'genomes',
            'protein_catalogue_name',
            'protein_catalogue_description',
            'downloads',
            'genome_count',
            'unclustered_genome_count',
            'version',
            'last_update',
            'pipeline_version_tag',
            'ftp_url',
        )


class GenomeSetSerializer(ExplicitFieldsModelSerializer,
                          serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='emgapi_v1:genomeset-detail',
        lookup_field='name',
    )

    genomes = relations.SerializerMethodHyperlinkedRelatedField(
        source='get_genomes',
        model=emg_models.Genome,
        many=True,
        read_only=True,
        related_link_view_name='emgapi_v1:genomeset-genomes-list',
        related_link_url_kwarg='name',
        related_link_lookup_field='name',
    )

    def get_genomes(self, obj):
        return None

    class Meta:
        model = emg_models.GenomeSet
        fields = (
            'url',
            'name',
            'genomes',
        )


class CogCatSerializer(ExplicitFieldsModelSerializer):
    class Meta:
        model = emg_models.CogCat
        fields = '__all__'


class KeggModuleSerializer(ExplicitFieldsModelSerializer):
    class Meta:
        model = emg_models.KeggModule
        fields = '__all__'


class KeggClassSerializer(ExplicitFieldsModelSerializer):
    class Meta:
        model = emg_models.KeggClass
        fields = ('class_id', 'name')


class AntiSmashGCSerializer(ExplicitFieldsModelSerializer):
    class Meta:
        model = emg_models.AntiSmashGC
        fields = '__all__'

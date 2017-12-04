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

from rest_framework import routers

from . import views
from . import views_relations


router = routers.DefaultRouter(trailing_slash=False)

router.register(
    r'biomes',
    views.BiomeViewSet,
    base_name='biomes'
)

router.register(
    r'studies',
    views.StudyViewSet,
    base_name='studies'
)

router.register(
    r'samples',
    views.SampleViewSet,
    base_name='samples'
)

router.register(
    r'runs',
    views.RunViewSet,
    base_name='runs'
)

router.register(
    r'experiment-types',
    views.ExperimentTypeViewSet,
    base_name='experiment-types'
)

router.register(
    r'pipelines',
    views.PipelineViewSet,
    base_name='pipelines'
)

router.register(
    r'pipeline-tools',
    views.PipelineToolViewSet,
    base_name='pipeline-tools'
)

router.register(
    r'publications',
    views.PublicationViewSet,
    base_name='publications'
)

router.register(
    r'runs/(?P<accession>[a-zA-Z0-9_\-\,\s]+)/analysis',
    views.AnalysisResultViewSet,
    base_name='runs-pipelines'
)

router.register(
    r'runs/(?P<accession>[a-zA-Z0-9_\-\,\s]+)/pipelines',
    views.AnalysisViewSet,
    base_name='runs-pipelines'
)

router.register(
    r'pipeline-tools/(?P<tool_name>[^/]+)',
    views.PipelineToolVersionViewSet,
    base_name='pipeline-tools-version'
)


# relationship views
router.register(
    r'biomes/(?P<lineage>[^/]+)/children',
    views_relations.BiomeTreeViewSet,
    base_name='biomes-children'
)

router.register(
    r'biomes/(?P<lineage>[^/]+)/studies',
    views_relations.BiomeStudyRelationshipViewSet,
    base_name='biomes-studies'
)

router.register(
    r'biomes/(?P<lineage>[^/]+)/samples',
    views_relations.BiomeSampleRelationshipViewSet,
    base_name='biomes-samples'
)

router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/studies',
    views_relations.PublicationStudyRelationshipViewSet,
    base_name='publications-studies'
)

router.register(
    r'studies/(?P<accession>[a-zA-Z0-9]+)/samples',
    views_relations.StudySampleRelationshipViewSet,
    base_name='studies-samples'
)

# router.register(
#     r'pipelines/(?P<release_version>[0-9\.]+)/studies',
#     views_relations.PipelineStudyRelationshipViewSet,
#     base_name='pipelines-studies'
# )

router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/samples',
    views_relations.PipelineSampleRelationshipViewSet,
    base_name='pipelines-samples'
)

router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/analysis',
    views_relations.PipelineAnalysisRelationshipViewSet,
    base_name='pipelines-analysis'
)

router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/tools',
    views_relations.PipelinePipelineToolRelationshipViewSet,
    base_name='pipelines-pipeline-tools'
)

router.register(
    r'experiment-types/(?P<experiment_type>[a-zA-Z0-9]+)/samples',
    views_relations.ExperimentTypeSampleRelationshipViewSet,
    base_name='experiment-types-samples'
)

router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/samples',
    views_relations.PublicationSampleRelationshipViewSet,
    base_name='publications-samples'
)

router.register(
    r'samples/(?P<accession>[a-zA-Z0-9\-\_]+)/runs',
    views_relations.SampleRunRelationshipViewSet,
    base_name='samples-runs'
)

router.register(
    r'experiment-types/(?P<experiment_type>[a-zA-Z0-9]+)/runs',
    views_relations.ExperimentTypeRunRelationshipViewSet,
    base_name='experiment-types-runs'
)

router.register(
    r'experiment-types/(?P<experiment_type>[a-zA-Z0-9]+)/analysis',
    views_relations.ExperimentTypeAnalysisRelationshipViewSet,
    base_name='experiment-types-analysis'
)

router.register(
    r'samples/(?P<accession>[a-zA-Z0-9\-\_]+)/studies',
    views_relations.SampleStudiesRelationshipViewSet,
    base_name='samples-studies'
)

router.register(
    r'samples/(?P<accession>[a-zA-Z0-9\-\_]+)/metadata',
    views_relations.SampleMetadataRelationshipViewSet,
    base_name='samples-metadata'
)

mydata_router = routers.DefaultRouter(trailing_slash=False)

mydata_router.register(
    r'mydata',
    views.MyDataViewSet,
    base_name='mydata'
)

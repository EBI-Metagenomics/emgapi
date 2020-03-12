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
from django.conf.urls import url

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
    r'super-studies',
    views.SuperStudyViewSet,
    base_name='super-studies'
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
    r'assemblies',
    views.AssemblyViewSet,
    base_name='assemblies'
)

router.register(
    r'analyses',
    views.AnalysisJobViewSet,
    base_name='analyses'
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
    r'pipeline-tools/(?P<tool_name>[^/]+)',
    views.PipelineToolVersionViewSet,
    base_name='pipeline-tools-version'
)

router.register(
    r'analyses/(?P<accession>[^/]+)',
    views.AnalysisQCChartViewSet,
    base_name='analysis-qcchart'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/krona',
    views.KronaViewSet,
    base_name='analysis-krona'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/downloads',
    views.AnalysisResultDownloadsViewSet,
    base_name='analysisdownload'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/file',
    views.AnalysisResultDownloadViewSet,
    base_name='analysisdownload'
)

router.register(
    r'studies/(?P<accession>[^/]+)/downloads',
    views.StudiesDownloadsViewSet,
    base_name='studydownload'
)


# relationship views
router.register(
    r'studies/(?P<accession>[^/]+)/analyses',
    views_relations.StudyAnalysisResultViewSet,
    base_name='studies-analyses'
)

router.register(
    r'super-studies/(?P<super_study_id>[0-9\.]+)/flagship-studies',
    views_relations.SuperStudyFlagshipStudiesViewSet,
    base_name='super-studies-flagship-studies'
)

router.register(
    r'super-studies/(?P<super_study_id>[0-9\.]+)/related-studies',
    views_relations.SuperStudyRelatedStudiesViewSet,
    base_name='super-studies-related-studies'
)

router.register(
    r'runs/(?P<accession>[^/]+)/analyses',
    views_relations.RunAnalysisViewSet,
    base_name='runs-analyses'
)

router.register(
    r'runs/(?P<accession>[^/]+)/assemblies',
    views_relations.RunAssemblyViewSet,
    base_name='runs-assemblies'
)

router.register(
    r'assemblies/(?P<accession>[^/]+)/analyses',
    views_relations.AssemblyAnalysisViewSet,
    base_name='assemblies-analyses'
)

router.register(
    r'studies/(?P<accession>[^/]+)'
    r'/pipelines/(?P<release_version>[0-9\.]+)/file',
    views_relations.StudiesDownloadViewSet,
    base_name='studydownload'
)

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
    r'biomes/(?P<lineage>[^/]+)/genomes',
    views_relations.BiomeGenomeRelationshipViewSet,
    base_name='biomes-genomes'
)

router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/studies',
    views_relations.PublicationStudyRelationshipViewSet,
    base_name='publications-studies'
)

router.register(
    r'studies/(?P<accession>[^/]+)/geocoordinates',
    views_relations.StudyGeoCoordinateRelationshipViewSet,
    base_name='studies-geoloc'
)

router.register(
    r'studies/(?P<accession>[a-zA-Z0-9]+)/studies',
    views_relations.StudyStudyRelationshipViewSet,
    base_name='studies-studies'
)

router.register(
    r'studies/(?P<accession>[^/]+)/samples',
    views_relations.StudySampleRelationshipViewSet,
    base_name='studies-samples'
)

router.register(
    r'studies/(?P<accession>[^/]+)/publications',
    views_relations.StudyPublicationRelationshipViewSet,
    base_name='studies-publications'
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
    r'pipelines/(?P<release_version>[0-9\.]+)/analyses',
    views_relations.PipelineAnalysisRelationshipViewSet,
    base_name='pipelines-analyses'
)

router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/tools',
    views_relations.PipelinePipelineToolRelationshipViewSet,
    base_name='pipelines-pipeline-tools'
)

router.register(
    r'experiment-types/(?P<experiment_type>[^/]+)/samples',
    views_relations.ExperimentTypeSampleRelationshipViewSet,
    base_name='experiment-types-samples'
)

router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/samples',
    views_relations.PublicationSampleRelationshipViewSet,
    base_name='publications-samples'
)

router.register(
    r'samples/(?P<accession>[^/]+)/runs',
    views_relations.SampleRunRelationshipViewSet,
    base_name='samples-runs'
)

router.register(
    r'experiment-types/(?P<experiment_type>[^/]+)/runs',
    views_relations.ExperimentTypeRunRelationshipViewSet,
    base_name='experiment-types-runs'
)

router.register(
    r'experiment-types/(?P<experiment_type>[^/]+)/analyses',
    views_relations.ExperimentTypeAnalysisRelationshipViewSet,
    base_name='experiment-types-analyses'
)

router.register(
    r'samples/(?P<accession>[^/]+)/studies',
    views_relations.SampleStudiesRelationshipViewSet,
    base_name='samples-studies'
)

router.register(
    r'samples/(?P<accession>[^/]+)/metadata',
    views_relations.SampleMetadataRelationshipViewSet,
    base_name='samples-metadata'
)

mydata_router = routers.DefaultRouter(trailing_slash=False)
mydata_router.register(
    r'mydata',
    views.MyDataViewSet,
    base_name='mydata'
)

utils_router = routers.DefaultRouter(trailing_slash=False)
utils_router.register(
    r'utils',
    views.UtilsViewSet,
    base_name='csrf'
)

router.register(
    r'genomes',
    views.GenomeViewSet,
    base_name='genomes'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/cogs',
    views_relations.GenomeCogsRelationshipsViewSet,
    base_name='genome-cog'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/kegg-class',
    views_relations.GenomeKeggClassRelationshipsViewSet,
    base_name='genome-kegg-class'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/kegg-module',
    views_relations.GenomeKeggModuleRelationshipsViewSet,
    base_name='genome-kegg-module'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/kegg-class',
    views_relations.GenomeKeggClassRelationshipsViewSet,
    base_name='genome-kegg-class'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/antismash-genecluster',
    views_relations.GenomeAntiSmashGeneClustersRelationshipsViewSet,
    base_name='genome-antismash-genecluster'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/downloads',
    views.GenomeDownloadViewSet,
    base_name='genome-download'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/releases',
    views_relations.GenomeReleasesViewSet,
    base_name='genome-releases'
)
router.register(
    r'release',
    views.ReleaseViewSet,
    base_name='release'
)
router.register(
    r'release/(?P<version>[^/]+)/genomes',
    views_relations.ReleaseGenomesViewSet,
    base_name='release-genomes'
)

router.register(
    r'release/(?P<version>[^/]+)/downloads',
    views.ReleaseDownloadViewSet,
    base_name='release-download'
)

router.register(
    r'genomeset',
    views.GenomeSetViewSet,
    base_name='genomeset'
)

router.register(
    r'genomeset/(?P<name>[^/]+)/genomes',
    views_relations.GenomeSetGenomes,
    base_name='genomeset-genomes'
)

router.register(
    r'cogs',
    views.CogCatViewSet,
    base_name='cogs'
)

router.register(
    r'kegg-modules',
    views.KeggModuleViewSet,
    base_name='kegg-modules'
)

router.register(
    r'kegg-classes',
    views.KeggClassViewSet,
    base_name='kegg-classes'
)

router.register(
    r'antismash-geneclusters',
    views.AntiSmashGeneClustersViewSet,
    base_name='antismash-geneclusters'
)

urlpatterns = [
    url(r'^v1/banner-message',
        views.BannerMessageView.as_view(),
        name='banner-message'),
]

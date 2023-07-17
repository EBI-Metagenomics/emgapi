# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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
from django.conf import settings
from django.urls import path

from rest_framework import routers

from . import views
from . import views_relations

router = routers.DefaultRouter(trailing_slash=False)

router.register(
    r'biomes',
    views.BiomeViewSet,
    basename='biomes'
)

router.register(
    r'studies',
    views.StudyViewSet,
    basename='studies'
)

router.register(
    r'super-studies',
    views.SuperStudyViewSet,
    basename='super-studies'
)

router.register(
    r'samples',
    views.SampleViewSet,
    basename='samples'
)

router.register(
    r'runs',
    views.RunViewSet,
    basename='runs'
)

router.register(
    r'assemblies',
    views.AssemblyViewSet,
    basename='assemblies'
)

router.register(
    r'assemblies/(?P<accession>[^/]+)/extra-annotations',
    views.AssemblyExtraAnnotationViewSet,
    basename='assembly-extra-annotations'
)

router.register(
    r'runs/(?P<accession>[^/]+)/extra-annotations',
    views.RunExtraAnnotationViewSet,
    basename='run-extra-annotations'
)


router.register(
    r'analyses',
    views.AnalysisJobViewSet,
    basename='analyses'
)

router.register(
    r'experiment-types',
    views.ExperimentTypeViewSet,
    basename='experiment-types'
)

router.register(
    r'pipelines',
    views.PipelineViewSet,
    basename='pipelines'
)

router.register(
    r'pipeline-tools',
    views.PipelineToolViewSet,
    basename='pipeline-tools'
)

router.register(
    r'publications',
    views.PublicationViewSet,
    basename='publications'
)

router.register(
    r'pipeline-tools/(?P<tool_name>[^/]+)',
    views.PipelineToolVersionViewSet,
    basename='pipeline-tools-version'
)

router.register(
    r'analyses/(?P<accession>[^/]+)',
    views.AnalysisQCChartViewSet,
    basename='analysis-qcchart'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/krona',
    views.KronaViewSet,
    basename='analysis-krona'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/downloads',
    views.AnalysisResultDownloadsViewSet,
    basename='analysisdownload'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/file',
    views.AnalysisResultDownloadViewSet,
    basename='analysisdownload'
)

router.register(
    r'studies/(?P<accession>[^/]+)/downloads',
    views.StudiesDownloadsViewSet,
    basename='studydownload'
)


# relationship views
router.register(
    r'studies/(?P<accession>[^/]+)/analyses',
    views_relations.StudyAnalysisResultViewSet,
    basename='studies-analyses'
)

router.register(
    r'super-studies/(?P<super_study_id>[^/]+)/flagship-studies',
    views_relations.SuperStudyFlagshipStudiesViewSet,
    basename='super-studies-flagship-studies'
)

router.register(
    r'super-studies/(?P<super_study_id>[^/]+)/related-studies',
    views_relations.SuperStudyRelatedStudiesViewSet,
    basename='super-studies-related-studies'
)

router.register(
    r'super-studies/(?P<super_study_id>[^/]+)/related-genome-catalogues',
    views_relations.SuperStudyGenomeCataloguesViewSet,
    basename='super-studies-related-genome-catalogues'
)

router.register(
    r'runs/(?P<accession>[^/]+)/analyses',
    views_relations.RunAnalysisViewSet,
    basename='runs-analyses'
)

router.register(
    r'runs/(?P<accession>[^/]+)/assemblies',
    views_relations.RunAssemblyViewSet,
    basename='runs-assemblies'
)

router.register(
    r'assemblies/(?P<accession>[^/]+)/analyses',
    views_relations.AssemblyAnalysisViewSet,
    basename='assemblies-analyses'
)

router.register(
    r'assemblies/(?P<accession>[^/]+)/runs',
    views_relations.AssemblyRunsViewSet,
    basename='assemblies-runs'
)

router.register(
    r'studies/(?P<accession>[^/]+)'
    r'/pipelines/(?P<release_version>[0-9\.]+)/file',
    views_relations.StudiesDownloadViewSet,
    basename='studydownload'
)

router.register(
    r'biomes/(?P<lineage>[^/]+)/children',
    views_relations.BiomeTreeViewSet,
    basename='biomes-children'
)

router.register(
    r'biomes/(?P<lineage>[^/]+)/studies',
    views_relations.BiomeStudyRelationshipViewSet,
    basename='biomes-studies'
)

router.register(
    r'biomes/(?P<lineage>[^/]+)/samples',
    views_relations.BiomeSampleRelationshipViewSet,
    basename='biomes-samples'
)

router.register(
    r'biomes/(?P<lineage>[^/]+)/genomes',
    views_relations.BiomeGenomeRelationshipViewSet,
    basename='biomes-genomes'
)

router.register(
    r'biomes/(?P<lineage>[^/]+)/genome-catalogues',
    views_relations.BiomeGenomeCatalogueRelationshipViewSet,
    basename='biomes-genome-catalogues'
)

router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/studies',
    views_relations.PublicationStudyRelationshipViewSet,
    basename='publications-studies'
)

router.register(
    r'studies/(?P<accession>[^/]+)/geocoordinates',
    views_relations.StudyGeoCoordinateRelationshipViewSet,
    basename='studies-geoloc'
)

router.register(
    r'studies/(?P<accession>[a-zA-Z0-9]+)/studies',
    views_relations.StudyStudyRelationshipViewSet,
    basename='studies-studies'
)

router.register(
    r'studies/(?P<accession>[^/]+)/samples',
    views_relations.StudySampleRelationshipViewSet,
    basename='studies-samples'
)

router.register(
    r'studies/(?P<accession>[^/]+)/publications',
    views_relations.StudyPublicationRelationshipViewSet,
    basename='studies-publications'
)

# router.register(
#     r'pipelines/(?P<release_version>[0-9\.]+)/studies',
#     views_relations.PipelineStudyRelationshipViewSet,
#     basename='pipelines-studies'
# )

router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/samples',
    views_relations.PipelineSampleRelationshipViewSet,
    basename='pipelines-samples'
)

router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/analyses',
    views_relations.PipelineAnalysisRelationshipViewSet,
    basename='pipelines-analyses'
)

router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/tools',
    views_relations.PipelinePipelineToolRelationshipViewSet,
    basename='pipelines-pipeline-tools'
)

router.register(
    r'experiment-types/(?P<experiment_type>[^/]+)/samples',
    views_relations.ExperimentTypeSampleRelationshipViewSet,
    basename='experiment-types-samples'
)

router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/samples',
    views_relations.PublicationSampleRelationshipViewSet,
    basename='publications-samples'
)

router.register(
    r'samples/(?P<accession>[^/]+)/runs',
    views_relations.SampleRunRelationshipViewSet,
    basename='samples-runs'
)

router.register(
    r'experiment-types/(?P<experiment_type>[^/]+)/runs',
    views_relations.ExperimentTypeRunRelationshipViewSet,
    basename='experiment-types-runs'
)

router.register(
    r'experiment-types/(?P<experiment_type>[^/]+)/analyses',
    views_relations.ExperimentTypeAnalysisRelationshipViewSet,
    basename='experiment-types-analyses'
)

router.register(
    r'samples/(?P<accession>[^/]+)/studies',
    views_relations.SampleStudiesRelationshipViewSet,
    basename='samples-studies'
)

router.register(
    r'samples/(?P<accession>[^/]+)/metadata',
    views_relations.SampleMetadataRelationshipViewSet,
    basename='samples-metadata'
)

mydata_router = routers.DefaultRouter(trailing_slash=False)
mydata_router.register(
    r'mydata',
    views.MyDataViewSet,
    basename='mydata'
)

utils_router = routers.DefaultRouter(trailing_slash=False)
utils_router.register(
    r'utils',
    views.UtilsViewSet,
    basename='csrf'
)

router.register(
    r'genomes',
    views.GenomeViewSet,
    basename='genomes'
)

# Proxy Genome Search requests to microservice backend
router.register(
    r'genome-search',
    views.GenomeFragmentSearchViewSet,
    basename='genome-search'
)

# Sourmash search
router.register(
    r'genomes-search/gather',
    views.GenomeSearchGatherViewSet,
    basename='genomes-gather'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/cogs',
    views_relations.GenomeCogsRelationshipsViewSet,
    basename='genome-cog'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/kegg-class',
    views_relations.GenomeKeggClassRelationshipsViewSet,
    basename='genome-kegg-class'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/kegg-module',
    views_relations.GenomeKeggModuleRelationshipsViewSet,
    basename='genome-kegg-module'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/kegg-class',
    views_relations.GenomeKeggClassRelationshipsViewSet,
    basename='genome-kegg-class'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/antismash-genecluster',
    views_relations.GenomeAntiSmashGeneClustersRelationshipsViewSet,
    basename='genome-antismash-genecluster'
)

router.register(
    r'genomes/(?P<accession>[^/]+)/downloads',
    views.GenomeDownloadViewSet,
    basename='genome-download'
)

router.register(
    r'genome-catalogues',
    views.GenomeCatalogueViewSet,
    basename='genome-catalogues'
)

router.register(
    r'genome-catalogues/(?P<catalogue_id>[^/]+)/genomes',
    views_relations.GenomeCatalogueGenomeRelationshipViewSet,
    basename='genome-catalogue-genomes'
)

router.register(
    r'genome-catalogues/(?P<catalogue_id>[^/]+)/downloads',
    views.GenomeCatalogueDownloadViewSet,
    basename='genome-catalogue-downloads'
)

router.register(
    r'genomeset',
    views.GenomeSetViewSet,
    basename='genomeset'
)

router.register(
    r'genomeset/(?P<name>[^/]+)/genomes',
    views_relations.GenomeSetGenomes,
    basename='genomeset-genomes'
)

router.register(
    r'cogs',
    views.CogCatViewSet,
    basename='cogs'
)

router.register(
    r'kegg-modules',
    views.KeggModuleViewSet,
    basename='kegg-modules'
)

router.register(
    r'kegg-classes',
    views.KeggClassViewSet,
    basename='kegg-classes'
)

router.register(
    r'antismash-geneclusters',
    views.AntiSmashGeneClustersViewSet,
    basename='antismash-geneclusters'
)

urlpatterns = [
    path(r'v1/banner-message',
        views.BannerMessageView.as_view(),
        name='banner-message'),
    path(r'v1/ebi-search-download/<str:domain>',
        views.EBISearchCSVDownload.as_view(),
        name='ebi-search-download'),
    url(r'^v1/genomes-search/status/(?P<job_id>[^/]+)',
        views.GenomeSearchStatusView.as_view(),
        name='genomes-status'),
    url(r'^v1/genomes-search/results/(?P<job_id>[^/]+)',
        views.GenomeSearchResultsView.as_view(),
        name='genomes-results')
]

if settings.ADMIN:
    urlpatterns += [
        path(r'v1/biom-prediction',
            views.BiomePrediction.as_view(),
            name='biom-prediction')
    ]

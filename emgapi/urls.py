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
from rest_framework.routers import DefaultRouter
from rest_auth import views as rest_auth_views

from . import views
from . import views_relations


app_name = "emgapi"
urlpatterns = [

    url(
        r'^auth/login',
        rest_auth_views.LoginView.as_view(),
        name='rest_auth_login'
    ),

    url(
        r'^auth/logout',
        rest_auth_views.LogoutView.as_view(),
        name='rest_auth_logout'
    ),

]

router = DefaultRouter(trailing_slash=False)

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
    r'pipelines',
    views.PipelineViewSet,
    base_name='pipelines'
)

router.register(
    r'experiment-types',
    views.ExperimentTypeViewSet,
    base_name='experiment-types'
)

router.register(
    r'biomes',
    views.BiomeViewSet,
    base_name='biomes'
)

router.register(
    r'publications',
    views.PublicationViewSet,
    base_name='publications'
)

router.register(
    r'pipeline-tools',
    views.PipelineToolViewSet,
    base_name='pipeline-tools'
)

router.register(
    r'mydata',
    views.MyDataViewSet,
    base_name='mydata'
)


urlpatterns += router.urls

urlpatterns += [

    url(
        (r'^runs/(?P<accession>[a-zA-Z0-9_]+)/(?P<release_version>[0-9\.]+)$'),
        views.RunAPIView.as_view(),
        name='runs-pipelines-detail'
    ),

    url(
        (r'^pipeline-tools/(?P<tool_name>[\w+]+)/'
         r'(?P<version>[a-zA-Z0-9\-\.]+)$'),
        views.PipelineToolInstanceView.as_view(),
        name='pipeline-tools-detail'
    ),

]


# relationship views
relation_router = DefaultRouter(trailing_slash=False)

relation_router.register(
    r'biomes/(?P<lineage>[a-zA-Z0-9\:\-\s\(\)\<\>]+)/children',
    views_relations.BiomeTreeViewSet,
    base_name='biomes-children'
)

relation_router.register(
    r'biomes/(?P<lineage>[a-zA-Z0-9\:\-\s\(\)\<\>]+)/studies',
    views_relations.BiomeStudyRelationshipViewSet,
    base_name='biomes-studies'
)

relation_router.register(
    r'biomes/(?P<lineage>[a-zA-Z0-9\:\-\s\(\)\<\>]+)/samples',
    views_relations.BiomeSampleRelationshipViewSet,
    base_name='biomes-samples'
)

relation_router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/studies',
    views_relations.PublicationStudyRelationshipViewSet,
    base_name='publications-studies'
)

relation_router.register(
    r'studies/(?P<accession>[a-zA-Z0-9]+)/samples',
    views_relations.StudySampleRelationshipViewSet,
    base_name='studies-samples'
)

relation_router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/studies',
    views_relations.PipelineStudyRelationshipViewSet,
    base_name='pipelines-studies'
)

relation_router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/samples',
    views_relations.PipelineSampleRelationshipViewSet,
    base_name='pipelines-samples'
)

relation_router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/tools',
    views_relations.PipelinePipelineToolRelationshipViewSet,
    base_name='pipelines-tools'
)

relation_router.register(
    r'experiment-types/(?P<experiment_type>[a-zA-Z0-9]+)/samples',
    views_relations.ExperimentSampleRelationshipViewSet,
    base_name='experiment-types-samples'
)

relation_router.register(
    r'publications/(?P<pubmed_id>[0-9\.]+)/samples',
    views_relations.PublicationSampleRelationshipViewSet,
    base_name='publications-samples'
)

relation_router.register(
    r'samples/(?P<accession>[a-zA-Z0-9\-\_]+)/runs',
    views_relations.SampleRunRelationshipViewSet,
    base_name='samples-runs'
)

relation_router.register(
    r'samples/(?P<accession>[a-zA-Z0-9\-\_]+)/metadata',
    views_relations.SampleMetadataRelationshipViewSet,
    base_name='samples-metadata'
)


urlpatterns += relation_router.urls

urlpatterns += [

    url(
        (r'^runs/(?P<accession>[a-zA-Z0-9_]+)/(?P<release_version>[0-9\.]+)/'
         r'metadata$'),
        views_relations.RunMetadataView.as_view(),
        name='runs-pipelines-metadata-list'
    ),

]

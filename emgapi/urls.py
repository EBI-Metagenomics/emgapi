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

from . import views
from . import views_relations
from django.conf.urls import url
from rest_framework.routers import DefaultRouter


app_name = "emgapi"
urlpatterns = [

    url(
        (r'^runs/(?P<accession>[a-zA-Z0-9]+)/'
         r'pipelines/(?P<release_version>[0-9\.]+)$'),
        views.RunAPIView.as_view(),
        name='runs-pipelines-detail'
    ),

    url(
        r'^tools/(?P<tool_name>[\w+]+)/(?P<version>[a-zA-Z0-9\-\.]+)$',
        views.PipelineToolAPIView.as_view(),
        name='tools-detail'
    ),

    # url(
    #     (r'^metadata/(?P<name>(.*)+)/(?P<value>(.*)+)$'),
    #     views.SampleAnnAPIView.as_view(),
    #     name='metadata-detail'
    # ),

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
    r'experiments',
    views.ExperimentTypeViewSet,
    base_name='experiments'
)

router.register(
    r'biomes/(?P<lineage>[a-zA-Z0-9\:\-\s\(\)\<\>]+)',
    views.BiomeViewSet,
    base_name='biomes'
)

router.register(
    r'publications',
    views.PublicationViewSet,
    base_name='publications'
)

router.register(
    r'tools',
    views.PipelineToolViewSet,
    base_name='tools'
)

# router.register(
#     r'metadata',
#     views.SampleAnnsViewSet,
#     base_name='metadata'
# )


router.register(
    r'mydata',
    views.MyDataViewSet,
    base_name='mydata'
)

urlpatterns += router.urls


# relationship views
relation_router = DefaultRouter(trailing_slash=False)

relation_router.register(
    r'biomes/(?P<lineage>[a-zA-Z0-9\:\-\s\(\)\<\>]+)/studies',
    views_relations.BiomeStudyRelationshipViewSet,
    base_name='biomes-studies'
)

relation_router.register(
    r'publications/(?P<pub_id>[a-zA-Z0-9,]+)/studies',
    views_relations.PublicationStudyRelationshipViewSet,
    base_name='publications-studies'
)

relation_router.register(
    r'studies/(?P<accession>[a-zA-Z0-9]+)/samples',
    views_relations.StudySampleRelationshipViewSet,
    base_name='studies-samples'
)

relation_router.register(
    r'pipelines/(?P<release_version>[0-9\.]+)/samples',
    views_relations.PipelineSampleRelationshipViewSet,
    base_name='pipelines-samples'
)

relation_router.register(
    r'experiments/(?P<experiment_type>[a-zA-Z0-9]+)/samples',
    views_relations.ExperimentSampleRelationshipViewSet,
    base_name='experiments-samples'
)

relation_router.register(
    r'biomes/(?P<lineage>[a-zA-Z0-9\:\-\s\(\)\<\>]+)/samples',
    views_relations.BiomeSampleRelationshipViewSet,
    base_name='biomes-samples'
)

relation_router.register(
    r'publications/(?P<pub_id>[a-zA-Z0-9,]+)/samples',
    views_relations.PublicationSampleRelationshipViewSet,
    base_name='publications-samples'
)

relation_router.register(
    r'samples/(?P<accession>[a-zA-Z0-9]+)/runs',
    views_relations.SampleRunRelationshipViewSet,
    base_name='samples-runs'
)

urlpatterns += relation_router.urls

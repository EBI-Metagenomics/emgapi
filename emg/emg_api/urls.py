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
from django.conf.urls import url
from rest_framework.routers import DefaultRouter


app_name = "emg_api"
urlpatterns = [

    url(
        r'^runs/(?P<accession>[a-zA-Z0-9,_]+)/(?P<release_version>[0-9\.]+)$',
        views.RunAPIView.as_view(),
        name='runs-detail'
    ),

    # url(
    #     (r'^metadata/(?P<sample_accession>[a-zA-Z0-9,_]+)/'
    #      '(?P<var_id>[0-9]+)$'),
    #     views.SampleAnnAPIView.as_view(),
    #     name='metadata-detail'
    # ),

]

router = DefaultRouter(trailing_slash=False)

router.register(
    r'mydata',
    views.MyDataViewSet,
    base_name='mydata'
)

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

# router.register(
#     r'metadata',
#     views.SampleAnnsViewSet,
#     base_name='metadata'
# )

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
    r'publications',
    views.PublicationViewSet,
    base_name='publications'
)

urlpatterns += router.urls

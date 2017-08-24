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

# from django.conf.urls import url
from rest_framework_mongoengine.routers import DefaultRouter \
    as MongoDefaultRouter

from . import views as m_views
from . import other_views as o_views

app_name = "emgapimetadata"
urlpatterns = []

urlpatterns += [

    url(
        (r'^annotations/metadata$'),
        o_views.AnnotationMetadataAPIView.as_view(),
        name='annotations-metadata-list'
    ),

]

# MongoDB views
mongorouter = MongoDefaultRouter(trailing_slash=False)

mongorouter.register(
    r'annotations',
    m_views.AnnotationViewSet,
    base_name='annotations'
)

urlpatterns += mongorouter.urls


mongorelation_router = DefaultRouter(trailing_slash=False)

mongorelation_router.register(
    r'annotations/(?P<accession>[a-zA-Z0-9\:]+)/runs',
    m_views.AnnotationRunRelationshipViewSet,
    base_name='annotations-runs'
)

mongorelation_router.register(
    (r'runs/(?P<accession>[a-zA-Z0-9_]+)/(?P<release_version>[0-9\.]+)/'
     r'annotations'),
    m_views.AnalysisAnnotationRelViewSet,
    base_name='annotations-runs'
)

urlpatterns += mongorelation_router.urls

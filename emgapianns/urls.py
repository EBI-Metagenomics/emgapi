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

from rest_framework_mongoengine import routers as m_routers

from . import views as m_views


# MongoDB views
mongo_router = m_routers.DefaultRouter(trailing_slash=False)

mongo_router.register(
    r'annotations/go-terms',
    m_views.GoTermViewSet,
    base_name='goterms'
)
mongo_router.register(
    r'annotations/interpro-identifiers',
    m_views.InterproIdentifierViewSet,
    base_name='interproidentifier'
)

mongo_router.register(
    r'annotations/go-terms/(?P<accession>[a-zA-Z0-9\:]+)/analysis',
    m_views.GoTermRunRelationshipViewSet,
    base_name='goterms-analysis'
)

mongo_router.register(
    r'annotations/interpro-identifiers/(?P<accession>[a-zA-Z0-9\:]+)/analysis',
    m_views.InterproIdentifierRunRelationshipViewSet,
    base_name='interproidentifier-analysis'
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(
    (r'runs/(?P<accession>[a-zA-Z0-9_]+)/'
     r'pipelines/(?P<release_version>[0-9\.]+)/'
     r'go-terms'),
    m_views.AnalysisGoTermRelViewSet,
    base_name='runs-pipelines-goterms'
)

router.register(
    (r'runs/(?P<accession>[a-zA-Z0-9_]+)/'
     r'pipelines/(?P<release_version>[0-9\.]+)/'
     r'go-slim'),
    m_views.AnalysisGoSlimRelViewSet,
    base_name='runs-pipelines-goslim'
)

router.register(
    (r'runs/(?P<accession>[a-zA-Z0-9_]+)/'
     r'pipelines/(?P<release_version>[0-9\.]+)/'
     r'interpro-identifiers'),
    m_views.AnalysisInterproIdentifierRelViewSet,
    base_name='runs-pipelines-interpro'
)

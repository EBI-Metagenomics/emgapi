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
    r'annotations/go-terms/(?P<accession>[a-zA-Z0-9\:]+)/analyses',
    m_views.GoTermAnalysisRelationshipViewSet,
    base_name='goterms-analyses'
)

mongo_router.register(
    r'annotations/interpro-identifiers/(?P<accession>[a-zA-Z0-9\:]+)/analyses',
    m_views.InterproIdentifierAnalysisRelationshipViewSet,
    base_name='interproidentifier-analyses'
)

mongo_router.register(
    r'annotations/organisms',
    m_views.OrganismViewSet,
    base_name='organisms'
)

mongo_router.register(
    r'annotations/organisms/(?P<lineage>(.*))',
    m_views.OrganismTreeViewSet,
    base_name='organisms-children'
)

mongo_router.register(
    (r'annotations/organisms/(?P<lineage>[^/]+)/'
     r'analyses'),
    m_views.OrganismAnalysisRelationshipViewSet,
    base_name='organisms-analyses'
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(
    r'analyses/(?P<accession>[^/]+)/go-terms',
    m_views.AnalysisGoTermRelationshipViewSet,
    base_name='analysis-goterms'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/go-slim',
    m_views.AnalysisGoSlimRelationshipViewSet,
    base_name='analysis-goslim'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/interpro-identifiers',
    m_views.AnalysisInterproIdentifierRelationshipViewSet,
    base_name='analysis-interpro'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/taxonomy',
    m_views.AnalysisOrganismRelationshipViewSet,
    base_name='analysis-taxonomy'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/taxonomy/ssu',
    m_views.AnalysisOrganismSSURelationshipViewSet,
    base_name='analysis-taxonomy-ssu'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/taxonomy/lsu',
    m_views.AnalysisOrganismLSURelationshipViewSet,
    base_name='analysis-taxonomy-lsu'
)

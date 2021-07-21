#!/usr/bin/env python
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
from django.urls import path
from rest_framework import routers

from rest_framework_mongoengine import routers as m_routers

from . import views as m_views


# MongoDB views
mongo_router = m_routers.DefaultRouter(trailing_slash=False)

mongo_router.register(
    r'annotations/go-terms',
    m_views.GoTermViewSet,
    basename='goterms'
)

mongo_router.register(
    r'annotations/interpro-identifiers',
    m_views.InterproIdentifierViewSet,
    basename='interproidentifier'
)

mongo_router.register(
    r'annotations/kegg-modules',
    m_views.KeggModuleViewSet,
    basename='keggmodules'
)

mongo_router.register(
    r'annotations/pfam-entries',
    m_views.PfamEntryViewSet,
    basename='pfam'
)

mongo_router.register(
    r'annotations/kegg-orthologs',
    m_views.KeggOrthologViewSet,
    basename='kegg-orthologs'
)

mongo_router.register(
    r'annotations/genome-properties',
    m_views.GenomePropViewSet,
    basename='genome-properties'
)

mongo_router.register(
    r'annotations/antismash-gene-clusters',
    m_views.AntiSmashGeneClusterViewSet,
    basename='antismash-gene-clusters'
)

mongo_router.register(
    r'annotations/go-terms/<str:accession>/analyses',
    m_views.GoTermAnalysisRelationshipViewSet,
    basename='goterms-analyses'
)

mongo_router.register(
    r'annotations/interpro-identifiers/<str:accession>/analyses',
    m_views.InterproIdentifierAnalysisRelationshipViewSet,
    basename='interproidentifier-analyses'
)

mongo_router.register(
    r'annotations/kegg-modules/<str:accession>/analyses',
    m_views.KeggModuleAnalysisRelationshipViewSet,
    basename='keggmodule-analyses'
)

mongo_router.register(
    r'annotations/pfam-entries/<str:accession>/analyses',
    m_views.PfamAnalysisRelationshipViewSet,
    basename='pfam-analyses'
)

mongo_router.register(
    r'annotations/kegg-orthologs/<str:accession>/analyses',
    m_views.KeggOrthologRelationshipViewSet,
    basename='kegg-orthologs-analyses'
)

mongo_router.register(
    r'annotations/genome-properties/<str:accession>/analyses',
    m_views.GenomePropertyAnalysisRelationshipViewSet,
    basename='genome-properties-analyses'
)

mongo_router.register(
    r'annotations/antismash-gene-clusters/<str:accession>/analyses',
    m_views.AntiSmashGeneClusterAnalysisRelationshipViewSet,
    basename='antismash-gene-clusters-analyses'
)

mongo_router.register(
    r'annotations/organisms',
    m_views.OrganismViewSet,
    basename='organisms'
)

mongo_router.register(
    r'annotations/organisms/<str:lineage>',
    m_views.OrganismTreeViewSet,
    basename='organisms-children'
)

mongo_router.register(
    (r'annotations/organisms/<str:lineage>/'
     r'analyses'),
    m_views.OrganismAnalysisRelationshipViewSet,
    basename='organisms-analyses'
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(
    r'analyses/<str:accession>/contigs',
    m_views.AnalysisContigViewSet,
    basename='analysis-contigs'
)

router.register(
    r'analyses/<str:accession>/go-terms',
    m_views.AnalysisGoTermRelationshipViewSet,
    basename='analysis-goterms'
)

router.register(
    r'analyses/<str:accession>/go-slim',
    m_views.AnalysisGoSlimRelationshipViewSet,
    basename='analysis-goslim'
)

router.register(
    r'analyses/<str:accession>/interpro-identifiers',
    m_views.AnalysisInterproIdentifierRelationshipViewSet,
    basename='analysis-interpro'
)

router.register(
    r'analyses/<str:accession>/kegg-modules',
    m_views.AnalysisKeggModulesRelationshipViewSet,
    basename='analysis-kegg-modules'
)

router.register(
    r'analyses/<str:accession>/pfam-entries',
    m_views.AnalysisPfamRelationshipViewSet,
    basename='analysis-pfam-entries'
)

router.register(
    r'analyses/<str:accession>/kegg-orthologs',
    m_views.AnalysisKeggOrthologsRelationshipViewSet,
    basename='analysis-kegg-orthologs'
)

router.register(
    r'analyses/<str:accession>/genome-properties',
    m_views.AnalysisGenomePropertiesRelationshipViewSet,
    basename='analysis-genome-properties'
)

router.register(
    r'analyses/<str:accession>/antismash-gene-clusters',
    m_views.AnalysisAntiSmashGeneClustersRelationshipViewSet,
    basename='analysis-antismash-gene-clusters'
)

router.register(
    r'analyses/<str:accession>/taxonomy',
    m_views.AnalysisOrganismRelationshipViewSet,
    basename='analysis-taxonomy'
)

router.register(
    r'analyses/<str:accession>/taxonomy/ssu',
    m_views.AnalysisOrganismSSURelationshipViewSet,
    basename='analysis-taxonomy-ssu'
)

router.register(
    r'analyses/<str:accession>/taxonomy/lsu',
    m_views.AnalysisOrganismLSURelationshipViewSet,
    basename='analysis-taxonomy-lsu'
)

router.register(
    r'analyses/<str:accession>/taxonomy/itsonedb',
    m_views.AnalysisOrganismITSOneDBRelationshipViewSet,
    basename='analysis-taxonomy-itsonedb'
)

router.register(
    r'analyses/<str:accession>/taxonomy/unite',
    m_views.AnalysisOrganismITSUniteRelationshipViewSet,
    basename='analysis-taxonomy-unite'
)

urlpatterns = [
    path(r'v1/analyses/<str:accession>/taxonomy/overview',
        m_views.AnalysisTaxonomyOverview.as_view(),
        name='analysis-taxonomy-overview'),
]

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
    r'annotations/kegg-modules',
    m_views.KeggModuleViewSet,
    base_name='keggmodule'
)

mongo_router.register(
    r'annotations/pfam-entries',
    m_views.PfamEntryViewSet,
    base_name='pfam'
)

mongo_router.register(
    r'annotations/kegg-orthologs',
    m_views.KeggOrthologViewSet,
    base_name='kegg-orthologs'
)

mongo_router.register(
    r'annotations/genome-properties',
    m_views.GenomePropViewSet,
    base_name='genome-properties'
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
    r'annotations/kegg-modules/(?P<accession>[a-zA-Z0-9\:]+)/analyses',
    m_views.KeggModuleAnalysisRelationshipViewSet,
    base_name='keggmodule-analyses'
)

mongo_router.register(
    r'annotations/pfam-entries/(?P<accession>[a-zA-Z0-9\:]+)/analyses',
    m_views.PfamAnalysisRelationshipViewSet,
    base_name='pfam-analyses'
)

mongo_router.register(
    r'annotations/kegg-orthologs/(?P<accession>[a-zA-Z0-9\:]+)/analyses',
    m_views.KeggOrthologRelationshipViewSet,
    base_name='kegg-orthologs-analyses'
)

mongo_router.register(
    r'annotations/genome-properties/(?P<accession>[a-zA-Z0-9\:]+)/analyses',
    m_views.GenomePropertyAnalysisRelationshipViewSet,
    base_name='genome-properties-analyses'
)

mongo_router.register(
    r'annotations/organisms',
    m_views.OrganismViewSet,
    base_name='organisms'
)

mongo_router.register(
    r'annotations/organisms/(?P<lineage>[^/]+)',
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
    r'analyses/(?P<accession>[^/]+)/contigs',
    m_views.AnalysisContigViewSet,
    base_name='analysis-contigs'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/annotations',
    m_views.AnalysisContigAnnotationViewSet,
    base_name='analysis-annotations'
)

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
    r'analyses/(?P<accession>[^/]+)/kegg-modules',
    m_views.AnalysisKeggModulesRelationshipViewSet,
    base_name='analysis-keggmodules'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/pfam-entries',
    m_views.AnalysisPfamRelationshipViewSet,
    base_name='analysis-pfamentries'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/kegg-orthologs',
    m_views.AnalysisKeggOrthologsRelationshipViewSet,
    base_name='analysis-keggorthologs'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/genome-properties',
    m_views.AnalysisGenomePropertiesRelationshipViewSet,
    base_name='analysis-genomeproperties'
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

router.register(
    r'analyses/(?P<accession>[^/]+)/taxonomy/itsonedb',
    m_views.AnalysisOrganismITSOneDBRelationshipViewSet,
    base_name='analysis-taxonomy-itsonedb'
)

router.register(
    r'analyses/(?P<accession>[^/]+)/taxonomy/unite',
    m_views.AnalysisOrganismITSUniteRelationshipViewSet,
    base_name='analysis-taxonomy-unite'
)

urlpatterns = [
    url(r'analyses/(?P<accession>[^/]+)/taxonomy/overview',
        m_views.AnalysisTaxonomyOverview.as_view(),
        name='analysis-taxonomy-overview'),
]

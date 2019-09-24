#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

import logging
import urllib

from django.db.models import Q
from mongoengine.queryset.visitor import Q as M_Q

from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response

from emgapi import serializers as emg_serializers
from emgapi import models as emg_models
from emgapi import filters as emg_filters

from . import serializers as m_serializers
from . import models as m_models
from . import pagination as m_page
from . import viewsets as m_viewsets
from . import mixins as m_mixins


logger = logging.getLogger(__name__)


class GoTermViewSet(
    m_mixins.AnnotationRetrivalMixin,
    m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of GO terms.
    """
    annotation_model = m_models.GoTerm

    serializer_class = m_serializers.GoTermSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'GO:[0-9]+'

    def get_serializer_class(self):
        return super(GoTermViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of GO terms
        Example:
        ---
        `/annotations/go-terms`
        """
        return super(GoTermViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves GO term
        Example:
        ---
        `/annotations/go-terms/GO:009579`
        """
        return super(GoTermViewSet, self) \
            .retrieve(request, *args, **kwargs)


class InterproIdentifierViewSet(
    m_mixins.AnnotationRetrivalMixin,
    m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of InterPro identifiers.
    """
    annotation_model = m_models.InterproIdentifier

    serializer_class = m_serializers.InterproIdentifierSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'IPR[0-9]+'

    def get_serializer_class(self):
        return super(InterproIdentifierViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier`
        """
        return super(InterproIdentifierViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves InterPro identifier
        Example:
        ---
        `/annotations/interpro-identifier/IPR020405`
        """
        return super(InterproIdentifierViewSet, self) \
            .retrieve(request, *args, **kwargs)


class KeggModuleViewSet(
    m_mixins.AnnotationRetrivalMixin,
    m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of KEEG modules.
    """
    annotation_model = m_models.KeggModule

    serializer_class = m_serializers.KeggModuleSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'M[0-9]+'

    def get_serializer_class(self):
        return super(KeggModuleViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of KEGG modules
        Example:
        ---
        `/annotations/kegg-modules`
        """
        return super(KeggModuleViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves KEGG module
        Example:
        ---
        `/annotations/kegg-modules/M00127`
        """
        return super(KeggModuleViewSet, self) \
            .retrieve(request, *args, **kwargs)


class PfamEntryViewSet(
    m_mixins.AnnotationRetrivalMixin,
    m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of Pfem entries.
    """
    annotation_model = m_models.PfamEntry

    serializer_class = m_serializers.PfamSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'PF[0-9]+'

    def get_serializer_class(self):
        return super(PfamEntryViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Pfam entries
        Example:
        ---
        `/annotations/pfam-entries`
        """
        return super(PfamEntryViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a Pfram entry
        Example:
        ---
        `/annotations/pfam-entry/P0001`
        """
        return super(PfamEntryViewSet, self) \
            .retrieve(request, *args, **kwargs)


class KeggOrthologViewSet(
    m_mixins.AnnotationRetrivalMixin,
    m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of KEGG Ortholog.
    """
    annotation_model = m_models.KeggOrtholog

    serializer_class = m_serializers.KeggOrthologSerializer

    lookup_field = 'accession'
    lookup_value_regex = 'K[0-9]+'

    def get_serializer_class(self):
        return super(KeggOrthologViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of KO
        Example:
        ---
        `/annotations/ko`
        """
        return super(KeggOrthologViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a Kegg Ortholog
        Example:
        ---
        `/annotations/ko/ko00001`
        """
        return super(KeggOrthologViewSet, self) \
            .retrieve(request, *args, **kwargs)


class GenomePropViewSet(
    m_mixins.AnnotationRetrivalMixin,
    m_viewsets.ReadOnlyModelViewSet):
    """
    Provides list of Genome Properties.
    """
    annotation_model = m_models.GenomeProperty

    serializer_class = m_serializers.GenomePropertySerializer

    lookup_field = 'accession'
    lookup_value_regex = 'GenProp[0-9]+'

    def get_serializer_class(self):
        return super(GenomePropViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Genome properties
        Example:
        ---
        `/annotations/genome-properties`
        """
        return super(GenomePropViewSet, self) \
            .list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a Genome property
        Example:
        ---
        `/annotations/genome-properties/GenProp0063`
        """
        return super(GenomePropViewSet, self) \
            .retrieve(request, *args, **kwargs)


class GoTermAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given GO term
    Example:
    ---
    `/annotations/go-terms/GO:009579/analyses`
    """
    annotation_model = m_models.GoTerm

    def get_job_ids(self):
        job_ids = m_models.AnalysisJobGoTerm.objects \
            .filter(
                M_Q(go_slim__go_term=annotation) |
                M_Q(go_terms__go_term=annotation)
            ) \
            .distinct('job_id')
        return job_ids


class InterproIdentifierAnalysisRelationshipViewSet(  # NOQA
    m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given InterPro identifier
    Example:
    ---
    `/annotations/interpro-identifier/IPR020405/analyses`
    """
    annotation_model = m_models.InterproIdentifier

    def get_job_ids(self):
        return m_models.AnalysisJobInterproIdentifier.objects \
            .filter(M_Q(interpro_identifiers__interpro_identifier=annotation)) \
            .distinct('job_id')


class KeggModuleAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given KEGG module M00127 term
    Example:
    ---
    `/annotations/kegg-modules/M00127/analyses`
    """    
    annotation_model = m_models.KeggModule

    def get_job_ids(self):
        return m_models.AnalysisJobKeggModule.objects \
            .filter(M_Q(kegg_modules__module=annotation)) \
            .distinct('job_id')


class PfamAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given Pfam entey P00001 term
    Example:
    ---
    `/annotations/pfram-entries/P00001/analyses`
    """

    annotation_model = m_models.PfamEntry

    def get_job_ids(self):
        return m_models.AnalysisJobPfam.objects \
            .filter(M_Q(pfam_entries__pfam=annotation)) \
            .distinct('job_id')


class GenomePropertyAnalysisRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given Genome Property term
    Example:
    ---
    `/annotations/genome-properties/GenProp0063/analyses`
    """

    annotation_model = m_models.GenomeProperty

    def get_job_ids(self):
        return m_models.AnalysisJobGenomeProperty.objects \
            .filter(M_Q(genome_properties__genome_property=annotation)) \
            .distinct('job_id')


class KeggOrthologRelationshipViewSet(m_viewsets.AnalysisRelationshipViewSet):
    """
    Retrieves list of analysis results for the given Kegg Ortholog
    Example:
    ---
    `/annotations/kos/ko00001/analyses`
    """

    annotation_model = m_models.KeggOrtholog

    def get_job_ids(self):
        return m_models.AnalysisJobKeggOrtholog.objects \
            .filter(M_Q(ko_entries__ko=annotation)) \
            .distinct('job_id')


class AnalysisGoTermRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves GO terms for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/go-terms`
    """
    serializer_class = m_serializers.GoTermRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobGoTerm

    annotation_model_property = 'go_terms'

    analysis_job_filters = ~Q(experiment_type__experiment_type='amplicon') 


class AnalysisGoSlimRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves GO slim for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/go-slim`
    """
    serializer_class = m_serializers.GoTermRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobGoTerm

    annotation_model_property = 'go_slim'

    analysis_job_filters = ~Q(experiment_type__experiment_type='amplicon')


class AnalysisInterproIdentifierRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves InterPro identifiers for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/interpro-identifiers`
    """

    serializer_class = m_serializers.InterproIdentifierRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobInterproIdentifier

    annotation_model_property = 'interpro_identifiers'

    analysis_job_filters = ~Q(experiment_type__experiment_type='amplicon') 


class AnalysisPfamRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves Pfram entries for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/pfam-entries`
    """

    serializer_class = m_serializers.PfamRetrieveSerializer

    pagination_class = m_page.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobPfam

    annotation_model_property = 'pfam_entries'


class AnalysisKeggModulesRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves KEGG Module for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/kegg-modules`
    """

    serializer_class = m_serializers.KeggModuleRetrieveSerializer

    pagination_class = m_page.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobKeggModule

    annotation_model_property = 'kegg_modules'


class AnalysisKeggOrthologsRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves Kegg Orthologs for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/kos`
    """

    serializer_class = m_serializers.KeggOrthologRetrieveSerializer

    pagination_class = m_page.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobKeggOrtholog

    annotation_model_property = 'ko_entries'


class AnalysisGenomePropertiesRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """
    Retrieves GenomeProperties for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/genome-properties`
    """

    serializer_class = m_serializers.GenomePropertyRetrieveSerializer

    pagination_class = m_page.MaxSetPagination

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobGenomeProperty

    annotation_model_property = 'genome_properties'


class OrganismViewSet(m_viewsets.ListReadOnlyModelViewSet):

    """
    Provides list of Organisms.
    """

    serializer_class = m_serializers.OrganismSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'lineage'
    lookup_value_regex = '.*'

    def get_queryset(self):
        return m_models.Organism.objects.all()

    def get_serializer_class(self):
        return super(OrganismViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Organisms
        Example:
        ---
        `/annotations/organisms`
        """
        return super(OrganismViewSet, self) \
            .list(request, *args, **kwargs)


class OrganismTreeViewSet(m_viewsets.ListReadOnlyModelViewSet):
    """
    Provides list of Organisms.
    """

    serializer_class = m_serializers.OrganismSerializer

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'domain',
        'prefix',
        'lineage',
    )

    lookup_field = 'lineage'
    lookup_value_regex = '[^/]+'

    def get_queryset(self):
        lineage = urllib.parse.unquote(
            self.kwargs.get('lineage', None).strip())
        organism = m_models.Organism.objects \
            .filter(lineage=lineage) \
            .only('name').distinct('name')
        if len(organism) == 0:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        queryset = m_models.Organism.objects \
            .filter(M_Q(ancestors__in=organism) | M_Q(name__in=organism))
        return queryset

    def get_serializer_class(self):
        return super(OrganismTreeViewSet, self).get_serializer_class()

    def get_serializer_context(self):
        context = super(OrganismTreeViewSet, self).get_serializer_context()
        context['lineage'] = self.kwargs.get('lineage')
        return context

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of Organisms
        Example:
        ---
        `/annotations/organisms/Bacteria:Chlorobi/children`
        """
        return super(OrganismTreeViewSet, self) \
            .list(request, *args, **kwargs)


class AnalysisOrganismRelationshipViewSet(
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves 16SrRNA Taxonomic analysis for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/taxonomy`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy 
    
    annotation_model_property = 'taxonomy'


class AnalysisOrganismSSURelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves SSU Taxonomic analysis for the given accession
    Example: 
    ---
    `/analyses/MGYA00102827/taxonomy/ssu`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy
    
    annotation_model_property = 'taxonomy_ssu'


class AnalysisOrganismLSURelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves LSU Taxonomic analysis for the given accession
    Example: 
    ---
    `/analyses/MGYA00102827/taxonomy/lsu`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy

    annotation_model_property = 'taxonomy_lsu'


class AnalysisOrganismITSOneDBRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves ITSoneDB Taxonomic analysis for the given accession
    Example:
    ---
    `/analyses/MGYA00102827/taxonomy/itsonedb`
    ---
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy
 
    annotation_model_property = 'taxonomy_itsonedb'


class AnalysisOrganismITSUniteRelationshipViewSet(  # NOQA
    m_mixins.AnalysisJobAnnotationMixin,
    m_viewsets.ListReadOnlyModelViewSet):
    """Retrieves ITS UNITE Taxonomic analysis for the given accession
    Example: 
    ---
    `/analyses/MGYA00102827/taxonomy/unite`
    ---    
    """
    serializer_class = m_serializers.OrganismRetriveSerializer

    pagination_class = m_page.MaxSetPagination

    filter_backends = (
        filters.OrderingFilter,
    )

    ordering_fields = (
        'name',
        'prefix',
        'lineage',
    )

    lookup_field = 'accession'

    annotation_model = m_models.AnalysisJobTaxonomy

    annotation_model_property = 'taxonomy_itsunite'


class AnalysisTaxonomyOverview(APIView):
    """Get the counts for each taxonomic results for an analysis job.
    """

    def get(self, request, accession):
        """Get the AnalysisJob and then the AnalysisJobTaxonomy
        """        
        job = get_object_or_404(
            emg_models.AnalysisJob,
            Q(pk=int(accession.lstrip('MGYA')))
        )
        analysis = None
        try:
            analysis = m_models.AnalysisJobTaxonomy.objects \
                .get(analysis_id=str(job.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            raise Http404

        return Response({
            'accession': analysis.accession,
            'pipeline_version': analysis.pipeline_version,
            'taxonomy_count': len(getattr(analysis, 'taxonomy', [])),
            'taxonomy_ssu_count': len(getattr(analysis, 'taxonomy_ssu', [])),
            'taxonomy_lsu_count': len(getattr(analysis, 'taxonomy_lsu', [])),
            'taxonomy_itsunite_count': len(getattr(analysis, 'taxonomy_itsunite', [])),
            'taxonomy_itsonedb_count': len(getattr(analysis, 'taxonomy_itsonedb', []))
        })


class OrganismAnalysisRelationshipViewSet(m_viewsets.ListReadOnlyModelViewSet):

    serializer_class = emg_serializers.AnalysisSerializer

    filter_class = emg_filters.AnalysisJobFilter

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    ordering_fields = (
        'job_id',
    )

    ordering = ('-job_id',)

    search_fields = (
        '@sample__metadata__var_val_ucv',
    )

    lookup_field = 'lineage'

    def get_queryset(self):
        lineage = urllib.parse.unquote(
            self.kwargs.get(self.lookup_field, None).strip())
        organism = m_models.Organism.objects.filter(lineage=lineage) \
            .only('id')
        if len(organism) == 0:
            raise Http404(("Attribute error '%s'." % self.lookup_field))
        job_ids = m_models.AnalysisJobTaxonomy.objects \
            .filter(
                M_Q(taxonomy__organism__in=organism) |
                M_Q(taxonomy_lsu__organism__in=organism) |
                M_Q(taxonomy_ssu__organism__in=organism)
            ).distinct('job_id')
        return emg_models.AnalysisJob.objects \
            .filter(job_id__in=job_ids) \
            .available(self.request)

    def get_serializer_class(self):
        return emg_serializers.AnalysisSerializer

    def list(self, request, *args, **kwargs):
        """
        Retrieves list of analysis results for the given Organism
        Example:
        ---
        `/annotations/organisms/Bacteria:Chlorobi:OPB56/analysis`
        """

        return super(OrganismAnalysisRelationshipViewSet, self) \
            .list(request, *args, **kwargs)

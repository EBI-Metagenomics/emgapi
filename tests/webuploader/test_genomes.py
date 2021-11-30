#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
import os

from django.urls import reverse
from django.core.management import call_command

from rest_framework import status

from model_bakery import baker

import emgapi.models as emg_models

from test_utils.emg_fixtures import *  # noqa


class TestGenomes:
    """Genomes API tests
    """
    def _setup(self):
        downloads = (
            ("Protein sequence FASTA file of the species representative", "Predicted CDS (aa)",),
            ("DNA sequence FASTA file of the genome assembly of the species representative", "Nucleic Acid Sequence",),
            ("DNA sequence FASTA file index of the genome assembly of the species representative", "Nucleic Acid Sequence index",),
            ("Protein sequence of the accessory genome", "Protein sequence (accessory)",),
            ("Protein sequence of the core genome", "Protein sequence (core)",),
            ("eggNOG annotations of the protein coding sequences", "EggNog annotation",),
            ("eggNOG annotations of the core and accessory genes", "EggNog annotation (core and accessory)",),
            ("InterProScan annotation of the protein coding sequences", "InterProScan annotation",),
            ("InterProScan annotations of the core and accessory genes", "InterProScan annotation (core and accessory)",),
            ("Presence/absence binary matrix of the pan-genome across all conspecific genomes", "Gene Presence / Absence matrix",),
            ("Protein sequence FASTA file of core genes (>=90% of the " +
             "genomes with >=90% amino acid identity)", "Core predicted CDS",),
            ("Protein sequence FASTA file of accessory genes", "Accessory predicted CDS",),
            ("Protein sequence FASTA file of core and accessory genes", "Core & Accessory predicted CDS",),
            ("Genome GFF file with various sequence annotations", "Genome Annotation"),
            ("Phylogenetic tree of catalogue genomes", 'Phylogenetic tree of catalogue genomes'),
            ("Genome GFF file with antiSMASH geneclusters annotations", "Genome antiSMASH Annotation"),
            ("Tree generated from the pairwise Mash distances of conspecific genomes",
             "Pairwise Mash distances of conspecific genomes")
        )
        for d in downloads:
            emg_models.DownloadDescriptionLabel.objects.get_or_create(
                description=d[0],
                description_label=d[1]
            )

        file_formats = (
            ("TAB", "tab", False),
            ("GFF", "gff", False),
            ("JSON", "json", False),
            ("FAI", "fai", False),
            ("Newick format", "nwk", False)
        )
        for fformat in file_formats:
            emg_models.FileFormat.objects.get_or_create(
                format_name=fformat[0],
                format_extension=fformat[1],
                compression=fformat[2],
            )

    @pytest.mark.django_db
    def test_import_genomes(self, client):
        """Assert that the import worked for genome 'MGYG-HGUT-00776'
        """
        self._setup()
        baker.make('emgapi.Biome',
                   lineage='root:Host-Associated:Human:Digestive System:Large intestine')
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data/')
        call_command('import_genomes', path, 'genomes/uhgg/2.0', 'UHGG', '2.0',
                     'root:Host-Associated:Human:Digestive System:Large intestine')

        genome = emg_models.Genome.objects.get(accession='MGYG000000001')

        assert genome.accession == 'MGYG000000001'
        assert genome.completeness == 98.59
        assert genome.contamination == 0.7
        assert genome.eggnog_coverage == 93.78
        assert genome.ena_sample_accession == 'ERS370061'
        assert genome.ena_study_accession == 'ERP105624'
        assert genome.gc_content == 28.26
        assert genome.geographic_origin == 'Europe'
        assert genome.biome.lineage == 'root:Host-Associated:Human:Digestive System:Large intestine'
        assert genome.ipr_coverage == 86.42
        assert genome.length == 3219617
        assert genome.n_50 == 47258
        assert genome.nc_rnas == 63
        assert genome.num_contigs == 137
        assert genome.num_proteins == 3182
        assert genome.rna_16s == 99.74
        assert genome.rna_23s == 99.83
        assert genome.rna_5s == 88.24
        assert genome.taxon_lineage == "d__Bacteria;p__Firmicutes_A;c__Clostridia;o__Peptostreptococcales;" \
                                       "f__Peptostreptococcaceae;g__GCA-900066495;s__GCA-900066495 sp902362365"
        assert genome.trnas == 20
        assert genome.type == 'Isolate'

        url = reverse('emgapi_v1:genomes-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        resp_data = response.json()
        assert len(resp_data) == 3
        expected_ids = [
            'MGYG000000001',
            'MGYG000000002',
            'MGYG000000003'
        ]
        returned_ids = [d.get('attributes').get('accession') for d in resp_data['data']]
        assert expected_ids.sort() == returned_ids.sort()

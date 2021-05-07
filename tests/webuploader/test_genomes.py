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
            ("Phylogenetic tree of release genomes", 'Phylogenetic tree of release genomes'),
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
        """Assert tha the import worked for genome 'MGYG-HGUT-00776'
        """
        self._setup()
        baker.make('emgapi.Biome',
                   lineage='root:Host-Associated:Human:Digestive System:Large intestine')
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data/genomes/')
        call_command('import_genomes', path, '1.0')

        genome = emg_models.Genome.objects.get(accession='MGYG-HGUT-00776')

        assert genome.accession == 'MGYG-HGUT-00776'
        assert genome.completeness == 83.8
        assert genome.contamination == 1.9
        assert genome.eggnog_coverage == 89.98
        assert genome.ena_genome_accession == 'ERZ840115'
        assert genome.ena_sample_accession == 'DRS026637'
        assert genome.ena_study_accession == 'DRP003048'
        assert genome.gc_content == 47.61
        assert genome.genome_set.name == 'EBI'
        assert genome.geographic_origin == 'Asia'
        assert genome.biome.lineage == 'root:Host-Associated:Human:Digestive System:Large intestine'
        assert genome.ipr_coverage == 89.79
        assert genome.length == 1666477
        assert genome.n_50 == 8435
        assert genome.nc_rnas == 75
        assert genome.num_contigs == 234
        assert genome.num_proteins == 1537
        assert genome.rna_16s == 99.67
        assert genome.rna_23s == 90.6
        assert genome.rna_5s == 0.0
        assert genome.taxon_lineage == 'd__Bacteria;p__Firmicutes_C;c__Negativicutes;' \
                                       'o__Veillonellales;f__Dialisteraceae;g__UBA5809;' \
                                       's__UBA5809 sp002417965'
        assert genome.trnas == 17
        assert genome.type == 'MAG'
        assert genome.cmseq == 0.07
        assert genome.taxincons == 0.48

        url = reverse('emgapi_v1:genomes-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        resp_data = response.json()
        assert len(resp_data) == 3
        expected_ids = [
            'MGYG-HGUT-00776',
            'MGYG-HGUT-00777',
            'MGYG-HGUT-00778'
        ]
        returned_ids = [d.get('attributes').get('accession') for d in resp_data['data']]
        assert expected_ids.sort() == returned_ids.sort()

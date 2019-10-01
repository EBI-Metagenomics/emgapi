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
from collections import Counter

from emgapianns import models as m_models

from emgapi.utils import assembly_contig_coverage

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):
    help = 'Imports an assembly contigs and the annotations into Mongo'

    obj_list = list()
    rootpath = None
    result_dir = None

    def add_arguments(self, parser):
        parser.add_argument('accession', action='store', type=str,)
        parser.add_argument('--pipeline', action='store', dest='pipeline')
        parser.add_argument('--faix', action='store', type=str,
                            help='Fasta index file.', required=True)
        parser.add_argument('--gff', action='store', type=str,
                            help='GFF with the contigs annotations.', required=True)
        parser.add_argument('--min-length', action='store', type=int, default=500,
                            help='Only import contigs longer that this value.', required=False)

    def populate_from_accession(self, options):
        logger.info('Found {}'.format(len(self.obj_list)))
        for analysis_job in self.obj_list:
            self.load_contigs(analysis_job, options)

    def load_contigs(self, analysis_job, options):  # noqa: C901
        """Load the contigs in Mongo
        """
        logger.info('CLI {}'.format(options))

        faix = options['faix']
        gff = options['gff']
        min_length = options['min_length']

        # load the gff in memory
        gff_dict = {}
        with open(gff, 'r') as gff_file:
            logger.info('Parsing annotations from: {}'.format(gff))
            for line in gff_file:
                if '#' in line:
                    continue
                contig_id, _, _, _, _, _, _, _, atts = line.split('\t')
                if contig_id not in gff_dict:
                    gff_dict[contig_id] = {
                        'KEGG': [],
                        'COG': [],
                        'Pfam': [],
                        'InterPro': [],
                        'GO': []
                    }
                for category in atts.split(';'):
                    for possible_cat in ['KEGG', 'COG', 'Pfam', 'InterPro', 'GO']:
                        if category.startswith(possible_cat + '='):
                            values = [v.strip() for v in category.replace(possible_cat + '=', '').split(',') if v]
                            gff_dict[contig_id][possible_cat].extend(values)

        # Remove contigs
        m_models.AnalysisJobContig.objects.filter(
            analysis_id=str(analysis_job.job_id),
            accession=analysis_job.accession,
            job_id=analysis_job.job_id,
            pipeline_version=analysis_job.pipeline.release_version).delete()

        with open(faix, 'r') as fasta:
            new_contigs = []
            for line in fasta:
                contig_id, length, *_ = line.split('\t')

                annotations = gff_dict.get(contig_id, {})
                if min_length > int(length) or not annotations:
                    continue

                contig = m_models.AnalysisJobContig(
                    contig_id=contig_id.strip(),
                    length=length,
                    coverage=assembly_contig_coverage(contig_id),
                    analysis_id=str(analysis_job.job_id),
                    accession=analysis_job.accession,
                    job_id=analysis_job.job_id,
                    pipeline_version=analysis_job.pipeline.release_version
                )
                contig.keggs = list()
                contig.cogs = list()
                contig.pfams = list()
                contig.interpros = list()
                contig.gos = list()

                if 'KEGG' in annotations:
                    feature_count = Counter(annotations['KEGG'])
                    for feature in feature_count:
                        contig.keggs.append(
                            m_models.AnalysisJobKeggOrthologAnnotation(ko=feature, count=feature_count[feature])
                        )
                if 'COG' in annotations:
                    feature_count = Counter(annotations['COG'])
                    for feature in feature_count:
                        contig.cogs.append(
                            m_models.AnalysisJobCOGAnnotation(cog=feature, count=feature_count[feature])
                        )
                if 'Pfam' in annotations:
                    feature_count = Counter(annotations['Pfam'])
                    for feature in feature_count:
                        contig.pfams.append(
                            m_models.AnalysisJobPfamAnnotation(pfam_entry=feature, count=feature_count[feature])
                        )
                if 'InterPro' in annotations:
                    feature_count = Counter(annotations['InterPro'])
                    for feature in feature_count:
                        contig.interpros.append(
                            m_models.AnalysisJobInterproIdentifierAnnotation(
                                interpro_identifier=feature, count=feature_count[feature])
                        )
                if 'GO' in annotations:
                    feature_count = Counter(annotations['GO'])
                    for feature in feature_count:
                        contig.gos.append(
                            m_models.AnalysisJobGoTermAnnotation(go_term=feature, count=feature_count[feature])
                        )
                new_contigs.append(contig)
                if len(new_contigs) % 200 == 0:
                    m_models.AnalysisJobContig.objects.insert(new_contigs, load_bulk=False)
                    logger.info('Loading {} new contigs'.format(len(new_contigs)))
                    new_contigs = []
        if len(new_contigs):
            m_models.AnalysisJobContig.objects.insert(new_contigs, load_bulk=False)
            logger.info('Loading {} new contigs'.format(len(new_contigs)))

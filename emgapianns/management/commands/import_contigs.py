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
import os
import logging
from collections import Counter
import re

from emgapi.utils import assembly_contig_coverage
from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):
    help = 'Imports an assembly contigs and the annotations into Mongo'

    obj_list = list()
    rootpath = None
    result_dir = None

    @classmethod
    def _split(cls, string, sep=','):
        """String split modification, will not return [''] for empty strings
        it will return []
        """
        if not string:
            return []
        return [v.strip() for v in string.split(sep) if v]

    def add_arguments(self, parser):
        parser.add_argument('accession', action='store', type=str,)
        parser.add_argument('--pipeline', action='store', dest='pipeline')
        parser.add_argument('--batch-size', action='store', type=int, default=200,
                            help='Mongo DB insert batch size.')
        parser.add_argument('--faix', action='store', type=str,
                            help='Fasta index file.', required=True)
        parser.add_argument('--gff', action='store', type=str,
                            help='GFF with the contigs annotations.', required=True)
        parser.add_argument('--antismash', action='store', type=str,
                            help='antiSMASH gene clusters file (geneclusters.txt).')
        parser.add_argument('--kegg-modules', action='store', type=str,
                            help='KEGG Modules summary file.')
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
        kegg_modules = options['kegg_modules']
        antismash = options['antismash']
        min_length = options['min_length']
        batch_size = options['batch_size']

        logger.info('Starting the contigs import process for: ' + str(analysis_job.accession))

        # load the gff in memory
        annotations_dict = {}
        if not os.path.exists(gff):
            logger.error('GFF file does not exist')
            raise ValueError('GFF file does not exist')

        with open(gff, 'rt') as gff_file:
            logger.info('Parsing annotations from: {}'.format(gff))
            for line in gff_file:
                if line.startswith('#'):
                    continue
                contig_id, _, _, _, _, _, _, _, atts = line.split('\t')
                if contig_id not in annotations_dict:
                    annotations_dict[contig_id] = {
                        'KEGG': [],
                        'COG': [],
                        'Pfam': [],
                        'InterPro': [],
                        'GO': []
                    }
                for category in atts.split(';'):
                    for possible_cat in ['KEGG', 'COG', 'Pfam', 'InterPro', 'GO']:
                        if category.startswith(possible_cat + '='):
                            values = Command._split(category.replace(possible_cat + '=', ''))
                            annotations_dict[contig_id][possible_cat].extend(values)

        if antismash:
            logger.info('Loading antiSMASH')
            if os.path.exists(antismash):
                with open(antismash, 'rt') as as_file:
                    for line in as_file:
                        _, contig, cluster, *_ = line.split('\t')
                        contig_id = contig.replace(' ', '-')
                        # extend the annotations
                        if contig_id not in annotations_dict:
                            annotations_dict[contig_id] = {
                                'antiSMASH': []
                            }
                        if 'antiSMASH' not in annotations_dict[contig_id]:
                            annotations_dict[contig_id]['antiSMASH'] = []
                        annotations_dict[contig_id]['antiSMASH'].append(cluster)
            else:
                logger.warning('antiSMASH file does not exist. SKIPPING!')

        if kegg_modules:
            # KEGG Modules per contig is loaded from
            # the summary file
            logger.info('Loading the KEGG Modules')
            km_dict = {}
            if os.path.exists(kegg_modules):
                with open(kegg_modules, 'rt') as km_file:
                    next(km_file)
                    for line in km_file:
                        contig, module, completeness, _, _, matching, missing = line.split('\t')
                        # re-format removing the faa prefix
                        # ERZ782910.4199-NODE_4199_length_728_cov_2.072808_1 to
                        # ERZ782910.4199-NODE_4199_length_728_cov_2.072808
                        contig = re.sub(r'_\d+$', '', contig)
                        # store the modules per contig, one contig could
                        # have the same module several times
                        if contig not in km_dict:
                            km_dict[contig] = {}
                        if module not in km_dict[contig]:
                            km_dict[contig][module] = []
                        km_dict[contig][module].append(
                            [float(completeness), Command._split(matching), Command._split(missing)])
                # extend the annotations
                for contig, modules in km_dict.items():
                    if contig not in annotations_dict:
                        annotations_dict[contig] = {}
                    annotations_dict[contig].update(KEGGModules=modules)
            else:
                logger.warning('KEGG Modules files does not exist. SKIPPING!')

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

                annotations = annotations_dict.get(contig_id, {})
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

                if 'KEGG' in annotations:
                    contig.keggs = list()
                    feature_count = Counter(annotations['KEGG'])
                    for feature in feature_count:
                        contig.keggs.append(
                            m_models.AnalysisJobKeggOrthologAnnotation(ko=feature, count=feature_count[feature])
                        )
                if 'COG' in annotations:
                    contig.cogs = list()
                    feature_count = Counter(annotations['COG'])
                    for feature in feature_count:
                        contig.cogs.append(
                            m_models.AnalysisJobCOGAnnotation(cog=feature, count=feature_count[feature])
                        )
                if 'Pfam' in annotations:
                    contig.pfams = list()
                    feature_count = Counter(annotations['Pfam'])
                    for feature in feature_count:
                        contig.pfams.append(
                            m_models.AnalysisJobPfamAnnotation(pfam_entry=feature, count=feature_count[feature])
                        )
                if 'InterPro' in annotations:
                    contig.interpros = list()
                    feature_count = Counter(annotations['InterPro'])
                    for feature in feature_count:
                        contig.interpros.append(
                            m_models.AnalysisJobInterproIdentifierAnnotation(
                                interpro_identifier=feature, count=feature_count[feature])
                        )
                if 'GO' in annotations:
                    contig.gos = list()              
                    feature_count = Counter(annotations['GO'])
                    for feature in feature_count:
                        contig.gos.append(
                            m_models.AnalysisJobGoTermAnnotation(go_term=feature, count=feature_count[feature])
                        )
                if 'antiSMASH' in annotations:
                    contig.as_geneclusters = list()
                    feature_count = Counter(annotations['antiSMASH'])
                    for feature in feature_count:
                        contig.as_geneclusters.append(
                            m_models.AnalysisJobAntiSmashGCAnnotation(gene_cluster=feature,
                                                                      count=feature_count[feature])
                        )
                if 'KEGGModules' in annotations:
                    contig.kegg_modules = list()
                    for module, data in annotations['KEGGModules'].items():
                        for completeness, matching, missing in data:
                            contig.kegg_modules.append(
                                m_models.AnalysisJobKeggModuleAnnotation(module=module,
                                                                         completeness=completeness,
                                                                         matching_kos=matching or list(),
                                                                         missing_kos=missing or list())
                            )
                new_contigs.append(contig)
                if len(new_contigs) % batch_size == 0:
                    m_models.AnalysisJobContig.objects.insert(new_contigs, load_bulk=False)
                    logger.info('Creating {} new contigs'.format(len(new_contigs)))
                    new_contigs = []
        if len(new_contigs):
            m_models.AnalysisJobContig.objects.insert(new_contigs, load_bulk=False)
            logger.info('Creating {} new contigs'.format(len(new_contigs)))

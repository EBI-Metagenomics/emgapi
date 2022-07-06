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
import gzip

from emgapi.utils import assembly_contig_coverage
from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):
    help = 'Imports an assembly contigs and the annotations into Mongo'

    obj_list = list()
    rootpath = None
    result_dir = None
    PATHWAY_SUB_DIR = 'pathways-systems'

    @classmethod
    def _split(cls, string, sep=','):
        """String split modification, will not return [''] for empty strings
        it will return []
        """
        if not string:
            return []
        return [v.strip() for v in string.split(sep) if v]

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--batch-size', action='store', type=int, default=10000,
                            help='Mongo DB insert batch size.')
        parser.add_argument('--faix', action='store', type=str,
                            help='Fasta index file.', required=False)
        parser.add_argument('--gff', action='store', type=str,
                            help='GFF bgzip with the contigs annotations.', required=False)
        parser.add_argument('--antismash', action='store', type=str,
                            help='antiSMASH GFF bgzip.', required=False)
        parser.add_argument('--kegg-modules', action='store', type=str,
                            help='KEGG Modules summary file.', required=False)
        parser.add_argument('--min-length', action='store', type=int, default=500,
                            help='Only import contigs longer that this value.', required=False)

    def populate_from_accession(self, options):
        logger.info('Found {}'.format(len(self.obj_list)))
        for analysis_job in self.obj_list:
            self.load_contigs(analysis_job, options)

    def load_gff(self, gff, annotations_dict):
        """Load the GFF eggNOG data on the cache
        """
        if not os.path.exists(gff):
            logger.error('GFF file does not exist. Path:' + gff)
            raise ValueError('GFF file does not exist')

        with gzip.open(gff, 'rt') as gff_file:
            logger.info('Parsing annotations from: {}'.format(gff))
            for line in gff_file:
                if line.startswith('#'):
                    continue
                contig_id, *_, atts = line.split('\t')
                if contig_id not in annotations_dict:
                    annotations_dict[contig_id] = {
                        'kegg': [],
                        'cog': [],
                        'pfam': [],
                        'interpro': [],
                        'go': []
                    }
                for category in atts.split(';'):
                    for possible_cat in ['kegg', 'cog', 'pfam', 'interpro', 'go']:
                        if category.startswith(possible_cat + '='):
                            values = Command._split(category.replace(possible_cat + '=', ''))
                            annotations_dict[contig_id][possible_cat].extend(values)

    def load_antismash(self, antismash, annotations_dict):
        """Load antiSMASH file data on the cache
        """
        if not os.path.exists(antismash):
            logger.warning('antiSMASH file does not exist. SKIPPING!')
            return

        logger.info('Loading antiSMASH')
        with gzip.open(antismash, 'rt') as as_file:
            for line in as_file:
                if line.startswith('#'):
                    continue
                contig, *_, atts = line.split('\t')
                contig_id = contig.replace(' ', '-')
                contig_ann = annotations_dict.setdefault(contig_id, {'antismash': []})
                for at in atts.split(';'):
                    if 'as_gene_clusters' not in at:
                        continue
                    for at_cluster in at.split(','):
                        cluster = at_cluster.replace('as_gene_clusters=', '').replace('\n', '')
                        contig_ann.setdefault('antismash', []).append(cluster)
        logger.info('Loaded antiSMASH')

    def load_kegg_modules(self, kegg_modules, annotations_dict):
        """Load KEGG Modules and paths
        """
        if not os.path.exists(kegg_modules):
            logger.warning('KEGG Modules files does not exist. SKIPPING!')
            return
        # KEGG Modules per contig is loaded from
        # the summary file
        logger.info('Loading the KEGG Modules')
        km_dict = {}
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
                el = [float(completeness), Command._split(matching), Command._split(missing)]
                km_dict.setdefault(contig, {}) \
                       .setdefault(module, {}) \
                       .append(el)
        # extend the annotations
        for contig, modules in km_dict.items():
            if contig not in annotations_dict:
                annotations_dict[contig] = {}
            annotations_dict[contig].update(KEGGModules=modules)

    def load_contigs(self, analysis_job, options):
        """Load the contigs in Mongo
        """
        logger.info('CLI {}'.format(options))

        rootpath = options.get('rootpath', None)
        # no_antismash file detection
        if os.path.isfile(os.path.join(rootpath, analysis_job.result_directory, 'no_antismash')):
            logger.warning('No antismash results, SKIPPING!')
            return

        result_folder = os.path.join(rootpath, analysis_job.result_directory)
        result_file_prefix = analysis_job.input_file_name
        # ERZ782882_FASTA.fasta.bgz.fai
        default_faix_file_path = os.path.join(result_folder,
                                              "{}.{}".format(result_file_prefix, "fasta.bgz.fai"))
        faix = options['faix'] or default_faix_file_path
        # functional-annotation/ERZ782882_FASTA.contigs.annotations.gff.gz
        default_gff_file_path = os.path.join(result_folder, "functional-annotation",
                                             "{}.{}".format(result_file_prefix, "annotations.gff.bgz"))
        gff = options['gff'] or default_gff_file_path
        # TODO: calculation not implemented in pipeline yet.
        # kegg_modules = options['kegg_modules'] or root_file + '_summary.paths.kegg'
        # pathways-systems/ERZ782882_FASTA.antismash.gff.gz
        default_antismash_file_path = os.path.join(result_folder, "pathways-systems",
                                                   "{}.{}".format(result_file_prefix, "antismash.gff.bgz"))
        antismash = options['antismash'] or default_antismash_file_path

        min_length = options['min_length']
        batch_size = options['batch_size']

        logger.info('Starting the contigs import process for: ' + str(analysis_job.accession))

        annotations_dict = {}
        self.load_gff(gff, annotations_dict)
        self.load_antismash(antismash, annotations_dict)
        # TODO: calculation not implemented in pipeline yet.
        # self.load_kegg_modules(kegg_modules, annotations_dict)

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

                if 'kegg' in annotations:
                    kegg_feature_count = Counter(annotations['kegg'])
                    contig.has_kegg = bool(kegg_feature_count)
                    contig.keggs = map(
                        lambda f: m_models.AnalysisJobKeggOrthologAnnotation(
                            ko=f,
                            count=kegg_feature_count[f]),
                        kegg_feature_count)

                if 'cog' in annotations:
                    cog_feature_count = Counter(annotations['cog'])
                    contig.has_cog = bool(cog_feature_count)
                    contig.cogs = map(
                        lambda f: m_models.AnalysisJobCOGAnnotation(
                            cog=f,
                            count=cog_feature_count[f]),
                        cog_feature_count)

                if 'pfam' in annotations:
                    pfam_feature_count = Counter(annotations['pfam'])
                    contig.has_pfam = bool(pfam_feature_count)
                    contig.pfams = map(
                        lambda f: m_models.AnalysisJobPfamAnnotation(
                            pfam_entry=f,
                            count=pfam_feature_count[f]),
                        pfam_feature_count)

                if 'interpro' in annotations:
                    interpro_feature_count = Counter(annotations['interpro'])
                    contig.has_interpro = bool(interpro_feature_count)
                    contig.interpros = map(
                        lambda f: m_models.AnalysisJobInterproIdentifierAnnotation(
                            interpro_identifier=f,
                            count=interpro_feature_count[f]),
                        interpro_feature_count)

                if 'go' in annotations:
                    go_feature_count = Counter(annotations['go'])
                    contig.has_go = bool(go_feature_count)
                    contig.gos = map(
                        lambda f: m_models.AnalysisJobGoTermAnnotation(
                            go_term=f,
                            count=go_feature_count[f]),
                        go_feature_count)

                if 'antismash' in annotations:
                    antismash_feature_count = Counter(annotations['antismash'])
                    contig.has_antismash = bool(antismash_feature_count)
                    contig.as_geneclusters = map(
                        lambda f: m_models.AnalysisJobAntiSmashGCAnnotation(
                            gene_cluster=f,
                            count=antismash_feature_count[f]),
                        antismash_feature_count)

                if 'keggmodules' in annotations:
                    kegg_modules = annotations['keggmodules'].items()
                    contig.has_antismash = bool(kegg_modules)
                    contig.kegg_modules = map(
                        lambda km: m_models.AnalysisJobKeggModuleAnnotation(
                            module=km[0],
                            completeness=km[1][0],
                            matching_kos=km[1][1] or [],
                            missing_kos=km[1][2] or []),
                        kegg_modules)

                new_contigs.append(contig)
                if len(new_contigs) % batch_size == 0:
                    m_models.AnalysisJobContig.objects.insert(new_contigs, load_bulk=False)
                    logger.info('Creating {} new contigs'.format(len(new_contigs)))
                    new_contigs = []
        if len(new_contigs):
            m_models.AnalysisJobContig.objects.insert(new_contigs, load_bulk=False)
            logger.info('Creating {} new contigs'.format(len(new_contigs)))

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

import os
import csv
import logging

from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):

    FUNCTION_SUB_DIR = 'functional-annotation'
    PATHWAY_SUB_DIR = 'pathways-systems'

    def __init__(self):
        super().__init__()
        self.suffixes = ['.ips', '.ipr', '.go', '.go_slim', '.pfam', '.ko', '.gprops', '.antismash']
        self.pathway_suffixes = ['.gprops', '.antismash', '.kegg_pathways']
        self.kegg_pathway_suffix = ['.kegg_pathways']
        self.joined_suffixes = self.suffixes + self.kegg_pathway_suffix

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('suffix', nargs='?', type=str, default='.go_slim', choices=self.joined_suffixes,
                            help='Provide summary file suffix: ' + ' (default: %(default)s)')

    def populate_from_accession(self, options):
        logger.info("Found %d" % len(self.obj_list))
        for o in self.obj_list:
            self.find_path(o, options)

    @staticmethod
    def _check_source_file(source_file):
        """
            Returns FALSE if the given source does not exist or is empty.
        :param source_file:
        :return:
        """
        if not os.path.exists(source_file):
            logger.error('Path %r does not exist. SKIPPING!' % source_file)
            return False
        if not os.path.isfile(source_file):
            logger.error('Specified source %r is not a file. SKIPPING!' % source_file)
            return False
        if os.stat(source_file).st_size == 0:
            logger.error('Specified input file %r is empty. SKIPPING!' % source_file)
            return False
        return True

    def find_path(self, obj, options):
        rootpath = options.get('rootpath', None)
        self.suffix = options.get('suffix', None)

        # Output names and folders changed slightly between v4 and v5
        # This piece of code still supports both versions
        if self.suffix in self.suffixes:
            for infix in ['%s_summary%s', '%s.summary%s']:
                name = infix % (obj.input_file_name, self.suffix)
                # V5 introduced pathways and functional subfolders
                if options.get('pipeline') == "5.0":
                    sub_dir = self.FUNCTION_SUB_DIR
                    if self.suffix in self.pathway_suffixes:
                        sub_dir = self.PATHWAY_SUB_DIR
                    source_file = os.path.join(rootpath, obj.result_directory, sub_dir, name)
                else:
                    source_file = os.path.join(rootpath, obj.result_directory, name)
                if not self._check_source_file(source_file):
                    logger.info('Could not find: %s' % source_file)
                else:
                    logger.info('Found: %s' % source_file)
                    self._parse_and_load_summary_file(source_file, obj)
                    break
        elif self.suffix in self.kegg_pathway_suffix:
            # v5 only
            name = '%s.summary%s' % (obj.input_file_name, self.suffix)
            source_file = os.path.join(rootpath, obj.result_directory, self.PATHWAY_SUB_DIR, name)
            if not self._check_source_file(source_file):
                logger.info('Could not find: %s' % source_file)
            else:
                logger.info('Found: %s' % source_file)
                self.load_kegg_from_summary_file(obj, source_file)
        else:
            logger.warning("Suffix {} not accepted!".format(self.suffix))

    def load_go_from_summary_file(self, reader, obj):  # noqa
        try:
            run = m_models.AnalysisJobGoTerm.objects \
                .get(pk=str(obj.job_id))
        except m_models.AnalysisJobGoTerm.DoesNotExist:
            run = m_models.AnalysisJobGoTerm()
        run.analysis_id = str(obj.job_id)
        run.accession = obj.accession
        run.pipeline_version = obj.pipeline.release_version
        run.job_id = obj.job_id
        new_anns = []
        anns = []
        if self.suffix == '.go':
            run.go_terms = []
        if self.suffix == '.go_slim':
            run.go_slim = []
        for row in reader:
            try:
                row[0].lower().startswith('go:')
            except KeyError:
                pass
            else:
                ann = None
                try:
                    ann = m_models.GoTerm.objects.get(accession=row[0])
                except m_models.GoTerm.DoesNotExist:
                    ann = m_models.GoTerm(
                        accession=row[0],
                        description=row[1],
                        lineage=row[2],
                    )
                    new_anns.append(ann)
                if ann is not None:
                    anns.append(ann)
                    if self.suffix == '.go_slim':
                        rann = m_models.AnalysisJobGoTermAnnotation(
                            count=row[3],
                            go_term=ann
                        )
                        run.go_slim.append(rann)
                    elif self.suffix == '.go':
                        rann = m_models.AnalysisJobGoTermAnnotation(
                            count=row[3],
                            go_term=ann
                        )
                        run.go_terms.append(rann)
        if len(anns) > 0:
            logger.info(
                "Total %d Annotations for Run: %s" % (
                    len(anns), obj.accession))
            if len(new_anns) > 0:
                m_models.GoTerm.objects.insert(new_anns)
                logger.info(
                    "Created %d new GoTerm Annotations" % len(new_anns))
            if len(run.go_slim) > 0:
                logger.info("Go slim %d" % len(run.go_slim))
            if len(run.go_terms) > 0:
                logger.info("Go terms %d" % len(run.go_terms))
            run.save()
            logger.info("Saved Run %r" % run)

    def load_ipr_from_summary_file(self, reader, obj):  # noqa
        try:
            run = m_models.AnalysisJobInterproIdentifier.objects.get(
                pk=str(obj.job_id))
        except m_models.AnalysisJobInterproIdentifier.DoesNotExist:
            run = m_models.AnalysisJobInterproIdentifier()
        run.analysis_id = str(obj.job_id)
        run.accession = obj.accession
        version = obj.pipeline.release_version
        run.pipeline_version = version
        run.job_id = obj.job_id
        run.interpro_identifiers = []
        new_anns = []
        anns = []
        for row in reader:
            try:
                row[0].lower().startswith('ipr')
            except KeyError:
                pass
            else:
                ann = None
                try:
                    ann = m_models.InterproIdentifier.objects \
                        .get(accession=row[0])
                except m_models.InterproIdentifier.DoesNotExist:
                    ann = m_models.InterproIdentifier(
                        accession=row[0],
                        description=row[1],
                    )
                    new_anns.append(ann)
                if ann is not None:
                    anns.append(ann)
                    if self.suffix in ['.ipr']:
                        rann = m_models.AnalysisJobInterproIdentifierAnnotation(  # NOQA
                            count=row[2],
                            interpro_identifier=ann
                        )
                        run.interpro_identifiers.append(rann)
        if len(anns) > 0:
            logger.info(
                "Total %d Annotations for Run: %s %s" % (
                    len(anns), obj.accession, version))
            if len(new_anns) > 0:
                m_models.InterproIdentifier.objects.insert(new_anns)
                logger.info(
                    "Created %d new IPR Annotations" % len(new_anns))
            if len(run.interpro_identifiers) > 0:
                logger.info(
                    "Interpro identifiers %d" % len(run.interpro_identifiers))
            run.save()
            logger.info("Saved Run %r" % run)

    @staticmethod
    def load_kegg_from_summary_file(obj, summary_infile, delimiter=','):
        """Load KEGG Modules results for a job into Mongo.
        KEGG results are composed of 3 files:
            - summary file
            - matching ko per pathway
            - missing ko per pathway
        """
        try:
            analysis_keggs = m_models.AnalysisJobKeggModule.objects \
                .get(pk=str(obj.job_id))
        except m_models.AnalysisJobKeggModule.DoesNotExist:
            analysis_keggs = m_models.AnalysisJobKeggModule()

        analysis_keggs.analysis_id = str(obj.job_id)
        analysis_keggs.accession = obj.accession
        analysis_keggs.pipeline_version = obj.pipeline.release_version
        analysis_keggs.job_id = obj.job_id

        # drop previous annotations
        analysis_keggs.kegg_modules = []

        analysis_keggs.save()

        new_kmodules = set()
        annotations = []

        with open(summary_infile) as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            next(reader)  # skip header

            for accession, completeness, pathway_name, pathway_class, matching_kos, missing_kos in reader:
                accession = accession.strip()
                completeness = float(completeness)
                matching_kos_list = list(filter(None, matching_kos.strip().split(',')))
                missing_kos_list = list(filter(None, missing_kos.strip().split(',')))

                k_module = None
                try:
                    k_module = m_models.KeggModule.objects \
                        .get(accession=accession)
                except m_models.KeggModule.DoesNotExist:
                    k_module = m_models.KeggModule(
                        accession=accession,
                        name=pathway_name,
                        description=pathway_class
                    )
                    new_kmodules.add(k_module)

                kpann = m_models.AnalysisJobKeggModuleAnnotation(
                    module=k_module,
                    completeness=completeness,
                    matching_kos=matching_kos_list,
                    missing_kos=missing_kos_list
                )
                annotations.append(kpann)

            if len(new_kmodules):
                m_models.KeggModule.objects.insert(new_kmodules)
                logger.info(
                    'Created {} new KEGG Modules'.format(len(new_kmodules)))

            if len(annotations):
                analysis_keggs.kegg_modules.extend(annotations)
                logger.info(
                    'Created {} new KEGG Module Annotations'.format(len(annotations)))

        analysis_keggs.save()
        logger.info('Saved Run {analysis_keggs}')

    def load_summary_file(self, reader, obj, analysis_model, analysis_field,
                          entity_model, ann_model, ann_field):
        """Annotation summary file, generated with uniq.
        To generate this file for example:
        sed 's/\t/ /23g' KO.tbl | cut -f1,23 | sort | uniq -c
        """
        analysis = None
        try:
            analysis = analysis_model.objects \
                .get(pk=str(obj.job_id))
        except analysis_model.DoesNotExist:
            analysis = analysis_model()
        analysis.analysis_id = str(obj.job_id)
        analysis.accession = obj.accession
        analysis.pipeline_version = obj.pipeline.release_version
        analysis.job_id = obj.job_id

        referenced_entities = {}
        annotations = []

        # drop previous annotations
        setattr(analysis, analysis_field, [])
        analysis.save()

        for count, model_id, description in reader:
            count = int(count)

            entity = entity_model(
                accession=model_id,
                description=description
            )
            referenced_entities[model_id] = entity
            new_annotation = ann_model(count=count)
            setattr(new_annotation, ann_field, entity)
            annotations.append(new_annotation)

        if len(referenced_entities):
            existing_entities = entity_model.objects.filter(accession__in=referenced_entities.keys())
            for entity in existing_entities:
                referenced_entities.pop(entity.id)
            if referenced_entities:
                entity_model.objects.insert(referenced_entities)
            logger.info(
                'Created {} new entries'.format(len(referenced_entities)))

        if len(annotations):
            setattr(analysis, analysis_field, annotations)
            logger.info(
                'Created {} new annotations'.format(len(annotations)))

        analysis.save()
        logger.info('Saved {}'.format(analysis_field))

    def load_genome_properties(self, reader,  obj):
        """Genome properties import, using the output summary from GP
        File structure:
        "GenProp0678","C-type cytochrome biogenesis, system I","NO"|"YES"|"PARTIAL  "
        """
        analysis_genprop = None
        try:
            analysis_genprop = m_models.AnalysisJobGenomeProperty.objects \
                                                                 .get(pk=str(obj.job_id))
        except m_models.AnalysisJobGenomeProperty.DoesNotExist:
            analysis_genprop = m_models.AnalysisJobGenomeProperty()

        analysis_genprop.analysis_id = str(obj.job_id)
        analysis_genprop.accession = obj.accession
        analysis_genprop.pipeline_version = obj.pipeline.release_version
        analysis_genprop.job_id = obj.job_id

        new_entities = []
        annotations = []

        for gp_id, desc, presence in reader:
            gp = None
            try:
                gp = m_models.GenomeProperty.objects \
                    .get(accession=gp_id)
            except m_models.GenomeProperty.DoesNotExist:
                gp = m_models.GenomeProperty(
                    accession=gp_id,
                    description=desc
                )
                new_entities.append(gp)

            parsed_presence = None
            upper_presence = presence.upper() if presence else None
            if upper_presence == "YES":
                parsed_presence = m_models.AnalysisJobGenomePropAnnotation.YES_PRESENCE
            elif upper_presence == "NO":
                parsed_presence = m_models.AnalysisJobGenomePropAnnotation.NO_PRESENCE
            elif upper_presence == "PARTIAL":
                parsed_presence = m_models.AnalysisJobGenomePropAnnotation.PARTIAL_PRESENCE

            if not parsed_presence:
                raise ValueError("Invalid 'presence' value for genome properties row: {}"
                                 .format(" ".join(gp_id, desc, presence)))

            new_annotation = m_models.AnalysisJobGenomePropAnnotation(
                genome_property=gp,
                presence=parsed_presence
            )
            annotations.append(new_annotation)

        if len(new_entities):
            m_models.GenomeProperty.objects.insert(new_entities)
            logger.info(
                "Created {} new genome properties".format(len(new_entities)))

        if len(annotations):
            analysis_genprop.genome_properties = annotations
            logger.info(
                "Created {} new annotations".format(len(annotations)))

        analysis_genprop.save()
        logger.info("Saved Analysis annnotations Genome Properties")

    def _parse_and_load_summary_file(self, source_file, obj):
        logger.info('Loading: %s' % source_file)
        with open(source_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            if self.suffix == '.pfam':
                self.load_summary_file(reader,
                                       obj,
                                       m_models.AnalysisJobPfam,
                                       'pfam_entries',
                                       m_models.PfamEntry,
                                       m_models.AnalysisJobPfamAnnotation,
                                       'pfam_entry')
            elif self.suffix == '.ko':
                self.load_summary_file(reader,
                                       obj,
                                       m_models.AnalysisJobKeggOrtholog,
                                       'ko_entries',
                                       m_models.KeggOrtholog,
                                       m_models.AnalysisJobKeggOrthologAnnotation,
                                       'ko')
            elif self.suffix == '.gprops':
                self.load_genome_properties(reader, obj)
            elif self.suffix == '.antismash':
                self.load_summary_file(reader,
                                       obj,
                                       m_models.AnalysisJobAntiSmashGeneCluser,
                                       'antismash_gene_clusters',
                                       m_models.AntiSmashGeneCluster,
                                       m_models.AnalysisJobAntiSmashGCAnnotation,
                                       'gene_cluster')
            elif self.suffix in '.ips':
                self.load_summary_file(reader,
                                       obj,
                                       m_models.AnalysisJobInterproIdentifier,
                                       'interpro_identifiers',
                                       m_models.InterproIdentifier,
                                       m_models.AnalysisJobInterproIdentifierAnnotation,
                                       'interpro_identifier')
            elif self.suffix == '.ipr':
                self.load_ipr_from_summary_file(reader, obj)
            elif self.suffix in ('.go_slim', '.go'):
                self.load_go_from_summary_file(reader, obj)
            else:
                logger.warning("Suffix {} not accepted!".format(self.suffix))

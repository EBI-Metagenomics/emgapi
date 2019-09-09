#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import logging

from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            'suffix', nargs='?', type=str,
            default='.go_slim', choices=['.ipr', '.go', '.go_slim', '.kegg_paths', 
                                         '.pfam', '.ko', '.gprops'],
            help='summary: .go_slim, .go, .ipr, .kegg_paths, .pfam,' + 
                 'ko, .gprops (default: %(default)s)')

    def populate_from_accession(self, options):
        logger.info("Found %d" % len(self.obj_list))
        for o in self.obj_list:
            self.find_path(o, options)

    def find_path(self, obj, options):
        rootpath = options.get('rootpath', None)
        self.suffix = options.get('suffix', None)

        name = '%s_summary%s' % (obj.input_file_name, self.suffix)
        res = os.path.join(rootpath, obj.result_directory, name)
        logger.info('Found: %s' % res)
        
        if not os.path.exists(res):
            logger.error('Path %r exist. Empty file. SKIPPING!' % res)
            return
        if not os.path.isfile(res):
            logger.error('Path %r exist. No summary. SKIPPING!' % res)
            return
        if os.stat(res).st_size == 0:
            logger.error('Path %r doesn\'t exist. SKIPPING!' % res)
            return
        
        logger.info('Loading: %s' % res)
        with open(res) as csvfile:
            if self.suffix == '.kegg_paths':
                reader = csv.reader(csvfile, delimiter='\t')
                self.load_kegg_from_summary_file(reader, obj, rootpath)
            elif self.suffix == '.pfam':
                reader = csv.reader(csvfile, delimiter='\t')
                self.load_summary_file(reader, 
                                       obj,
                                       m_models.AnalysisJobPfam,
                                       'pfam_entries',
                                       m_models.PfamEntry,
                                       m_models.AnalysisJobPfamAnnotation,
                                       'pfam_entry')
            elif self.suffix == '.ko':
                reader = csv.reader(csvfile, delimiter='\t')
                self.load_summary_file(reader, 
                                       obj,
                                       m_models.AnalysisJobKeggOrtholog,
                                       'ko_entries',
                                       m_models.KeggOrtholog,
                                       m_models.AnalysisJobKeggOrthologAnnotation,
                                       'ko')
            elif self.suffix == '.gprops':
                reader = csv.reader(csvfile, delimiter='\t')
                self.load_summary_file(reader, 
                                       obj,
                                       m_models.AnalysisJobGenomeProperty,
                                       'genome_properties',
                                       m_models.GenomeProperty,
                                       m_models.AnalysisJobGenomePropAnnotation,
                                       'genome_property')
            else:
                reader = csv.reader(csvfile, delimiter=',')
                if self.suffix == '.ipr':
                    self.load_ipr_from_summary_file(reader, obj)
                elif self.suffix in ('.go_slim', '.go'):
                    self.load_go_from_summary_file(reader, obj)

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
                    if self.suffix == '.ipr':
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

    def load_kegg_from_summary_file(self, reader, obj, rootpath):
        """Load KEGG Modules results for a job into Mongo.
        KEGG results are outputed in 3 files:
        - summary file
        - matching ko per pathway
        - missing ko per pathway
        """
        try:
            analysis_keggs = m_models.AnalysisJobKeggModule.objects\
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

        # fetching the match and mismatch files
        def load_aux_file(filename):
            data_file = os.path.join(rootpath, obj.result_directory, filename)
            result = {}
            for module, completeness, ko_count, kos in self.get_reader(data_file, delimiter='\t'):
                result[module.strip()] = [
                    float(completeness),
                    int(ko_count),
                    [k.strip() for k in kos.split(',')]
            ]
            return result

        matches = load_aux_file('matching_ko_pathways.txt') # FIXME: hardcoded
        missings = load_aux_file('missing_ko_pathways.txt') # FIXME: hardcoded

        new_kmodules = []
        annotations = []

        next(reader) # skip header

        for accession, completeness, name, pclass in reader:
            accession = accession.strip()
            completeness = float(completeness)

            k_module = None
            try:
                k_module = m_models.KeggModule.objects \
                        .get(accession=accession)
            except m_models.KeggModule.DoesNotExist:
                k_module = m_models.KeggModule(
                    accession=accession,
                    name=name,
                    description=pclass
                )
                new_kmodules.append(k_module)

            kpann = m_models.AnalysisJobKeggModuleAnnotation(
                module=k_module,
                completeness=completeness,
                matching_kos=matches[accession][2],
                missing_kos=missings[accession][2]
            )
            annotations.append(kpann)

        if len(new_kmodules):
            m_models.KeggModule.objects.insert(new_kmodules)
            logger.info(
                f'Created {len(new_kmodules)} new KEGG Modules')

        if len(annotations):
            analysis_keggs.kegg_modules.extend(annotations)
            logger.info(
                f'Created {len(annotations)} new KEGG Module Annotations')

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

        new_entities = []
        annotations = []

        next(reader) # skip header

        for count_id, desciption in reader:
            count, model_id = count_id.strip().split(' ') 
            count = int(count)

            new_entity = None
            try:
                new_entity = entity_model.objects.get(accession=model_id)
            except entity_model.DoesNotExist:
                new_entity = entity_model(
                    accession=model_id,
                    description=desciption
                )
                new_entities.append(new_entity)
            new_annotation = ann_model(count=count)
            setattr(new_annotation, ann_field, new_entity)
            annotations.append(new_annotation)

        if len(new_entities):
            entity_model.objects.insert(new_entities)
            logger.info(
                f'Created {len(new_entities)} new entries')

        if len(annotations):
            setattr(analysis, analysis_field, annotations)
            logger.info(
                f'Created {len(annotations)} new annotations')

        analysis.save()
        logger.info('Saved {instance}')

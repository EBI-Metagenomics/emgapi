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
            default='.go_slim', choices=['.ipr', '.go', '.go_slim', '.kegg_paths', '.pfam'],
            help='summary: .go_slim, .go, .ipr, .kegg_paths, .pfam (default: %(default)s)')

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
                self.load_pfam_from_summary_file(reader, obj, rootpath)
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
        """Load KEGG results for a job into Mongo.
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

    def load_pfam_from_summary_file(self, reader, obj, rootpath):
        """Import PFam summary
        The PFam summary file is a .tsv.
        Each row has:
            Nro hits PFam accession \t Description
        Example:
             13 PF00001	7 transmembrane receptor (rhodopsin family)
            1418 PF00004 ATPase family associated with various cellular activities (AAA)
            27941 PF00005 ABC transporter
        """
        try:
            analysis_pfam = m_models.AnalysisJobPfam.objects\
                .get(pk=str(obj.job_id))
        except m_models.AnalysisJobPfam.DoesNotExist:
            analysis_pfam = m_models.AnalysisJobPfam()

        analysis_pfam.analysis_id = str(obj.job_id)
        analysis_pfam.accession = obj.accession
        analysis_pfam.pipeline_version = obj.pipeline.release_version
        analysis_pfam.job_id = obj.job_id

        # Drop previuos annotations
        analysis_pfam.pfam_entries = []

        analysis_pfam.save()

        new_pfams = []
        annotations = []

        next(reader) # skip header

        for count_id, desciption in reader:
            count, pfam_id = count_id.strip().split(' ') 
            count = int(count)

            pfam_entry = None
            try:
                pfam_entry = m_models.PfamEntry.objects \
                        .get(accession=pfam_id)
            except m_models.PfamEntry.DoesNotExist:
                pfam_entry = m_models.PfamEntry(
                    accession=pfam_id,
                    description=desciption
                )
                new_pfams.append(pfam_entry)
            
            pfam_ann = m_models.AnalysisJobPfamAnnotation(
                pfam_entry=pfam_entry,
                count=count
            )
            annotations.append(pfam_ann)

        if len(new_pfams):
            m_models.PfamEntry.objects.insert(new_pfams)
            logger.info(
                f'Created {len(new_pfams)} new Pfam entries')

        if len(annotations):
            analysis_pfam.pfam_entries.extend(annotations)
            logger.info(
                f'Created {len(annotations)} new Pfam Annotations')

        analysis_pfam.save()
        logger.info('Saved Run {analysis_pfam}')        
#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import logging
import os

from emgapi import models as emg_models
from emgapianns.management.lib.uploader_exceptions import UnexpectedVariableName
from ..lib import EMGBaseCommand
from emgapi.models import AnalysisJob

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--emg_db',
                            help='Target emg_db_name alias',
                            choices=['default', 'dev', 'prod'],
                            default='default')
        super(Command, self).add_arguments(parser)

    def populate_from_accession(self, options):
        logger.info("Found %d" % len(self.obj_list))
        for o in self.obj_list:
            self.find_path(o, options)

    def find_path(self, obj, options):
        rootpath = options.get('rootpath', None)
        emg_db = options['emg_db']

        for infile in ['qc_summary', 'functional-annotation/stats/interproscan.stats']:
            self.load_stats(rootpath, obj, infile, emg_db)
        self.import_rna_counts(rootpath=rootpath, job=obj, emg_db=emg_db)
        self.import_orf_stats(rootpath=rootpath, job=obj, emg_db=emg_db)

    def load_stats(self, rootpath, obj, input_file_name, emg_db):
        res = os.path.join(rootpath, obj.result_directory, input_file_name)

        if input_file_name == 'qc_summary':
            if not os.path.exists(res):  # Check existence of the v4.1 result file
                res = os.path.join(rootpath, obj.result_directory, 'charts', 'new.summary')

        if os.path.exists(res):
            if os.path.isfile(res):
                if os.stat(res).st_size > 0:
                    logger.info("Found: %s" % res)
                    with open(res) as csvfile:
                        reader = csv.reader(csvfile, delimiter='\t')
                        self.import_qc(reader, obj, emg_db)
                else:
                    logger.error("Path %r exist. Empty file. SKIPPING!" % res)
            else:
                logger.error("Path %r exist. No summary. SKIPPING!" % res)
        else:
            logger.error("Path %r doesn't exist. SKIPPING!" % res)

    @staticmethod
    def import_qc(reader, job, emg_db):
        anns = []
        for row in reader:
            var = None
            try:
                # The following if else case are a fix for older v4.1 uploads after we changed the labels
                # Could be removed when no more v4.1 results for uploading available
                if row[0] == "Nucleotide sequences with InterProScan match":
                    row[0] = "Reads with InterProScan match"
                elif row[0] == "Nucleotide sequences with predicted CDS":
                    row[0] = "Reads with predicted CDS"
                elif row[0] in ["Nucleotide sequences with predicted rRNA", "Nucleotide sequences with predicted RNA"]:
                    row[0] = "Reads with predicted RNA"
                #     End v4.1 fix
                var = emg_models.AnalysisMetadataVariableNames.objects.using(emg_db) \
                    .get(var_name=row[0])
            except emg_models.AnalysisMetadataVariableNames.DoesNotExist:
                var = emg_models.AnalysisMetadataVariableNames(var_name=row[0])
                var.save()
                # because PK is not AutoField
                var = emg_models.AnalysisMetadataVariableNames.objects.using(emg_db) \
                    .get(var_name=row[0])
            if var is not None:
                job_ann, created = emg_models.AnalysisJobAnn.objects.using(emg_db).update_or_create(
                    job=job, var=var,
                    defaults={'var_val_ucv': row[1]}
                )

                analysis_job = AnalysisJob.objects.get(job_id=job)
                analysis_summary = analysis_job.analysis_summary_json or []
                analysis_summary.append({
                    'key': job_ann.var.var_name,
                    'value': job_ann.var_val_ucv,
                })

                # Update analysis_summary_json with the modified array
                analysis_job.analysis_summary_json = analysis_summary
                analysis_job.save()

            anns.append(job_ann)
        logger.info("Total %d Annotations for Run: %s" % (len(anns), job))

    @staticmethod
    def import_rna_counts(rootpath, job, emg_db):
        logging.info("Loading RNA counts into the database...")
        res = os.path.join(rootpath, job.result_directory, 'RNA-counts')
        if os.path.exists(res):
            with open(res) as tsvfile:
                reader = csv.reader(tsvfile, delimiter='\t')
                for row in reader:
                    if not row: # skip empty lines at the end of the file
                        continue
                    try:
                        if row[0] == 'SSU count':
                            var_name = 'Predicted SSU sequences'
                        elif row[0] == 'LSU count':
                            var_name = 'Predicted LSU sequences'
                        elif not row[0]:
                            continue # Skip empty value rows
                        else:
                            logging.error("Unsupported variable name {}".format(row[0]))
                            raise UnexpectedVariableName

                        var = emg_models.AnalysisMetadataVariableNames.objects.using(emg_db) \
                            .get(var_name=var_name)

                        job_ann, created = emg_models.AnalysisJobAnn.objects.using(emg_db).update_or_create(
                            job=job, var=var,
                            defaults={'var_val_ucv': row[1]}
                        )
                        logging.info("{} successfully loaded into the database.".format(row[0]))

                    except emg_models.AnalysisMetadataVariableNames.DoesNotExist:
                        logging.error("Could not find variable name {} in the database even "
                                        "though it should be supported!".format(row[0]))
                        raise UnexpectedVariableName
        else:
            logging.warning("RNA counts file does not exist: {}".format(res))

    @staticmethod
    def import_orf_stats(rootpath, job, emg_db):
        logging.info("Loading ORF stats into the database...")
        res = os.path.join(rootpath, job.result_directory, 'functional-annotation/stats/orf.stats')
        if os.path.exists(res):
            with open(res) as tsvfile:
                reader = csv.reader(tsvfile, delimiter='\t')
                for row in reader:
                    try:
                        if row[0] == "Predicted CDS":
                            var_name = "Predicted CDS"
                        elif row[0] == "Contigs with predicted CDS":
                            var_name = "Contigs with predicted CDS"
                        elif row[0] in ["Contigs with predicted rRNA", "Contigs with predicted with rRNA",
                                        "Contigs with predicted RNA"]:
                            var_name = "Contigs with predicted RNA"
                        elif row[0] in ["Reads with predicted CDS", "Nucleotide sequences with predicted CDS"]:
                            var_name = "Reads with predicted CDS"
                        elif row[0] in ["Reads with predicted rRNA", "Nucleotide sequences with predicted rRNA",
                                        "Reads with predicted RNA"]:
                            var_name = "Reads with predicted RNA"
                        else:
                            msg = "Unsupported variable name {}".format(row[0])
                            logging.error(msg)
                            raise UnexpectedVariableName(msg)

                        var = emg_models.AnalysisMetadataVariableNames.objects.using(emg_db) \
                            .get(var_name=var_name)

                        job_ann, created = emg_models.AnalysisJobAnn.objects.using(emg_db).update_or_create(
                            job=job, var=var,
                            defaults={'var_val_ucv': row[1]}
                        )
                        logging.info("{} successfully loaded into the database.".format(row[0]))

                    except emg_models.AnalysisMetadataVariableNames.DoesNotExist:
                        msg = "Could not find variable name [{}|{}] in the database even though it should be supported!\n" \
                              "There are {} variables registered" \
                            .format(row[0], var_name, emg_models.AnalysisMetadataVariableNames.objects.count())
                        logging.error(msg)
                        raise UnexpectedVariableName(msg)
        else:
            logging.warning("orf.stats file does not exist: {}".format(res))

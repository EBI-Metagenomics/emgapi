#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import logging

from emgapi import models as emg_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):

    def populate_from_accession(self, options):
        logger.info("Found %d" % len(self.obj_list))
        for o in self.obj_list:
            self.find_path(o, options)

    def find_path(self, obj, options):
        rootpath = options.get('rootpath', None)
        res = os.path.join(
            rootpath, obj.result_directory, 'charts', 'new.summary')
        logger.info("Found: %s" % res)
        if os.path.exists(res):
            if os.path.isfile(res):
                logger.info("Found: %s" % res)
                with open(res) as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    logger.info("foo")
                    self.import_qc(reader, obj)
            else:
                logger.error("Path %r exist. No summary. SKIPPING!" % res)
        else:
            logger.error("Path %r doesn't exist. SKIPPING!" % res)

    def import_qc(self, reader, job):
        anns = []
        for row in reader:
            var = None
            try:
                var = emg_models.AnalysisMetadataVariableNames.objects \
                    .get(var_name=row[0])
            except emg_models.AnalysisMetadataVariableNames.DoesNotExist:
                var = emg_models.AnalysisMetadataVariableNames(var_name=row[0])
                var.save()
                # becuase PK is not AutoField
                var = emg_models.AnalysisMetadataVariableNames.objects \
                    .get(var_name=row[0])
            if var is not None:
                job_ann = emg_models.AnalysisJobAnn.objects.get_or_create(
                    job=job, var=var, var_val_ucv=row[1]
                )
                anns.append(job_ann)
        logger.info(
            "Total %d Annotations for Run: %s" % (len(anns), job))

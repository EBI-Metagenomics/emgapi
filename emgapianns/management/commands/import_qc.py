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
        res = os.path.join(rootpath, obj.result_directory)
        logger.info("Scanning path: %s" % res)
        if os.path.exists(res):
            if os.path.isdir(res):
                for root, dirs, files in os.walk(res, topdown=False):
                    for name in files:
                        if name in ('new.summary',):
                            with open(os.path.join(root, name)) as csvfile:
                                reader = csv.reader(csvfile, delimiter='\t')
                                self.import_qc(reader, obj)
            elif os.path.isfile(res):
                raise NotImplementedError("Give path to directory.")
        else:
            raise NotImplementedError("Path %r doesn't exist." % res)

    def import_qc(self, reader, job):
        anns = []
        for row in reader:
            try:
                var = emg_models.AnalysisMetadataVariableNames.objects \
                    .get(var_name=row[0])
            except emg_models.AnalysisMetadataVariableNames.DoesNotExist:
                var = emg_models.AnalysisMetadataVariableNames(var_name=row[0])
                var.save()
                # becuase PK is not AutoField
                var = emg_models.AnalysisMetadataVariableNames.objects \
                    .get(var_name=row[0])
            job_ann = emg_models.AnalysisJobAnn()
            job_ann.job = job
            job_ann.var = var
            job_ann.var_val_ucv = row[1]
            anns.append(job_ann)
        emg_models.AnalysisJobAnn.objects.bulk_create(anns)

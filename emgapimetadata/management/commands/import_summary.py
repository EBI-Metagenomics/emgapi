#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv

from django.core.management.base import BaseCommand

from emgapi import models as emg_models


class Command(BaseCommand):

    obj_list = list()
    rootpath = None
    accession = None

    def add_arguments(self, parser):
        parser.add_argument('accession', type=str)
        parser.add_argument('rootpath', type=str)

    def handle(self, *args, **options):
        self.rootpath = options.get('rootpath', None)
        self.accession = options.get('accession', None)
        self.find_accession(options)
        self.populate_from_accession()

    def find_accession(self, options):
        if self.accession:
            self.obj_list = emg_models.AnalysisJob.objects \
                .filter(sample__study__accession=self.accession).available()
            if len(self.obj_list) < 1:
                self.obj_list = emg_models.AnalysisJob.objects \
                    .filter(sample__accession=self.accession)
            if len(self.obj_list) < 1:
                self.obj_list = emg_models.AnalysisJob.objects \
                        .filter(accession=self.accession)
            if len(self.obj_list) < 1:
                raise AttributeError(
                    "Invalid accession: %s" % self.accession)

    def populate_from_accession(self):
        for o in self.obj_list:
            self.find_path(o)

    def find_path(self, obj):
        res = os.path.join(self.rootpath, obj.result_directory)
        print(obj.result_directory, obj.accession)
        if os.path.exists(res):
            if os.path.isdir(res):
                for root, dirs, files in os.walk(res, topdown=False):
                    for name in files:
                        if name in ('new.summary',):
                            with open(os.path.join(root, name)) as csvfile:
                                reader = csv.reader(csvfile, delimiter='\t')
                                self.import_summary(reader, obj)
            elif os.path.isfile(res):
                raise NotImplementedError("Give path to directory.")
        else:
            raise NotImplementedError("Path %r doesn't exist." % res)

    def import_summary(self, reader, job):
        anns = []
        for row in reader:
            print(row)
            try:
                var = emg_models.VariableNames.objects.get(var_name=row[0])
            except emg_models.VariableNames.DoesNotExist:
                var = emg_models.VariableNames(var_name=row[0])
                var.save()
                # becuase PK is not AutoField
                var = emg_models.VariableNames.objects.get(var_name=row[0])
            job_ann = emg_models.AnalysisJobAnn()
            job_ann.job = job
            job_ann.var = var
            job_ann.var_val_ucv = row[1]
            anns.append(job_ann)
        emg_models.AnalysisJobAnn.objects.bulk_create(anns)

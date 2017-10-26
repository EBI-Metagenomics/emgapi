#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from django.core.management.base import BaseCommand

from emgapi import models as emg_models

logger = logging.getLogger(__name__)


class EMGBaseCommand(BaseCommand):

    obj_list = list()
    rootpath = None
    accession = None

    def add_arguments(self, parser):
        parser.add_argument('accession', type=str)
        parser.add_argument('rootpath', type=str, default='')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.find_accession(options)
        self.populate_from_accession(options)

    def find_accession(self, options):
        self.accession = options.get('accession', None)
        if self.accession:
            print(emg_models.AnalysisJob.objects.all())
            self.obj_list = emg_models.AnalysisJob.objects \
                .filter(study__accession=self.accession).available()
            if len(self.obj_list) < 1:
                self.obj_list = emg_models.AnalysisJob.objects \
                    .filter(sample__accession=self.accession).available()
            if len(self.obj_list) < 1:
                self.obj_list = emg_models.AnalysisJob.objects \
                    .filter(accession=self.accession).available()
            if len(self.obj_list) < 1:
                logger.error(
                    "No runs %s, SKIPPING!" % self.accession)

    def populate_from_accession(self, options):
        raise NotImplementedError()

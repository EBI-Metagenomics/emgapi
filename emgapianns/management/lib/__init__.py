#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging

import csv

from django.core.management.base import BaseCommand
from django.db.models import Q
from emgapi import models as emg_models

logger = logging.getLogger(__name__)


class EMGBaseCommand(BaseCommand):
    obj_list = list()
    rootpath = None
    accession = None
    pipeline = None

    def add_arguments(self, parser):
        parser.add_argument(
            'accession',
            action='store',
            type=str,
        )
        parser.add_argument(
            'rootpath',
            action='store',
            type=str,
        )
        parser.add_argument(
            '--pipeline',
            help='Pipeline version',
            action='store',
            dest='pipeline',
            choices=['4.1', '5.0'], default='4.1'
        )

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.find_accession(options)
        self.populate_from_accession(options)

    def find_accession(self, options):
        self.accession = options.get('accession', None)
        self.pipeline = options.get('pipeline', None)

        if self.accession:
            queryset = emg_models.AnalysisJob.objects \
                .filter(
                    Q(study__secondary_accession=self.accession) |
                    Q(sample__accession=self.accession) |
                    Q(run__accession=self.accession) |
                    Q(assembly__accession=self.accession))
            if self.pipeline:
                queryset = queryset.filter(
                    Q(pipeline__release_version=self.pipeline)
                )
            self.obj_list = queryset.all()
            if len(self.obj_list) < 1:
                logger.error(
                    "No runs %s, SKIPPING!" % self.accession)

    def populate_from_accession(self, options):
        raise NotImplementedError()

    def get_reader(self, filename, delimiter=',', skip_header=True):
        """Given a filename return an iterator
        """
        if not os.path.exists(filename):
            logger.error("Path %r exist. Empty file. SKIPPING!" % filename)
            return
        if not os.path.isfile(filename):
            logger.error("Path %r exist.  SKIPPING!" % filename)
            return
        if os.stat(filename).st_size == 0:
            logger.error("Path %r doesn't exist. SKIPPING!" % filename)
            return

        csvfile = open(filename)
        reader = csv.reader(csvfile, delimiter=delimiter)
        if skip_header:
            next(reader)
        return reader

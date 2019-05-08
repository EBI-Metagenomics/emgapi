#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

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
            action='store',
            dest='pipeline'
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
                Q(run__accession=self.accession)
            )
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


class EMGGenomeCommand(BaseCommand):
    obj_list = list()
    rootpath = None
    accession = None
    release_version = None

    def add_arguments(self, parser):
        parser.add_argument('accession', action='store', type=str, )
        parser.add_argument('rootpath', action='store', type=str, )
        parser.add_argument('release_version', action='store', type=str, )

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        self.find_accession(options)
        self.populate_from_accession(options)

    def find_accession(self, options):
        self.accession = options.get('accession', None)
        self.release_version = options.get('release_version', None)

        if self.accession:
            queryset = emg_models.Genome.objects \
                .filter(accession=self.accession)

            self.obj_list = queryset.all()
            if len(self.obj_list) < 1:
                logger.error(
                    "No runs %s, SKIPPING!" % self.accession)

    def populate_from_accession(self, options):
        raise NotImplementedError()

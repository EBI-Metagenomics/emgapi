#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import logging

from emgapi import models as emg_models

# from ..lib import EMGBaseCommand
from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import a set of contigs for an analysis run'

    def add_arguments(self, parser):
        parser.add_argument('analysis_job', type=str)
        parser.add_argument('contigs_faix', type=str)

    def handle(self, *args, **options):
        """
        Import a set contigs for an analysis
        """
        accession = options['analysis_job']
        faix_path = options['contigs_faix']

        analysis_job = emg_models.AnalysisJob.objects.get(pk=accession)

        # open the faix and get the contigs names and lenghts
        to_create = []
        with open(faix_path, 'r') as faix:
            for line in faix:
                line_split = line.split('\t')
                to_create.append(emg_models.AnalysisJobContig(
                    name=line_split[0], 
                    length=int(line_split[1]), 
                    analysis_job=analysis_job))
            
        emg_models.AnalysisJobContig.objects.bulk_create(to_create, batch_size=500)

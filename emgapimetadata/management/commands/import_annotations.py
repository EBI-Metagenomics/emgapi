#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import codecs
from contextlib import closing

import requests
import csv

from django.core.management.base import BaseCommand

from emgapi import models as emg_models
from emgapimetadata import models as m_models


GO_URL = (
    "https://www.ebi.ac.uk/metagenomics/"
    "projects/{study}/samples/{sample}/runs/{analysis}/"
    "results/versions/{pipeline}/function/GOAnnotations"
)


class Command(BaseCommand):

    obj_list = list()
    rootpath = None
    accession = None

    def add_arguments(self, parser):
        parser.add_argument('accession', type=str)
        parser.add_argument('rootpath', nargs='?', type=str, default='')

    def handle(self, *args, **options):
        self.rootpath = options.get('rootpath', None)
        self.accession = options.get('accession', None)
        self.find_accession(options)
        self.populate_from_accession()

    def find_accession(self, options):
        if self.accession:
            self.obj_list = emg_models.AnalysisJob.objects \
                .filter(sample__study__accession=self.accession)
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
            if self.rootpath:
                self.find_path(o)
            else:
                attrs = {
                    'study': o.sample.study.accession,
                    'sample': o.sample.accession,
                    'analysis': o.accession,
                    'pipeline': o.pipeline.release_version,
                }
                resp = requests.get(GO_URL.format(**attrs), stream=True)
                with closing(resp) as r:
                    reader = csv.reader(
                        codecs.iterdecode(r.iter_lines(), 'utf-8'),
                        delimiter=',', quotechar='"')
                    self.import_go(
                        reader, o.accession,
                        o.pipeline.release_version)

    def find_path(self, obj):
        res = os.path.join(self.rootpath, obj.result_directory)
        if os.path.exists(res):
            if os.path.isdir(res):
                for root, dirs, files in os.walk(res, topdown=False):
                    for name in files:
                        with open(os.path.join(root, name)) as csvfile:
                            reader = csv.reader(csvfile, delimiter=',')
                            self.import_go(
                                reader, obj.accession,
                                obj.pipeline.release_version)
            elif os.path.isfile(res):
                raise NotImplementedError("Give path to directory.")
        else:
            raise NotImplementedError("Path '%r' doesn't exist." % res)

    def import_go(self, reader, accession, pipeline):
        run = m_models.AnalysisJob()
        run.accession = accession
        run.pipeline_version = pipeline
        new_anns = []
        anns = []
        for row in reader:
            try:
                row[0].lower().startswith('go:')
            except KeyError:
                pass
            else:
                ann = None
                try:
                    ann = m_models.Annotation.objects.get(accession=row[0])
                except m_models.Annotation.DoesNotExist:
                    ann = m_models.Annotation(
                        accession=row[0],
                        description=row[1],
                        lineage=row[2],
                    )
                    new_anns.append(ann)
                if ann is not None:
                    anns.append(ann)
                    rann = m_models.AnalysisJobAnnotation(
                        count=row[3],
                        annotation=ann
                    )
                    run.annotations.append(rann)
        if len(anns) > 0:
            if len(new_anns) > 0:
                m_models.Annotation.objects.insert(new_anns)
            run.save()

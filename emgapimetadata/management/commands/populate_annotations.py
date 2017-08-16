#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
from contextlib import closing

import requests
import csv

from django.core.management.base import BaseCommand
from django.core import exceptions

from emgapi import models as emg_models
from emgapimetadata import models as m_models


GO_URL = (
    "https://www.ebi.ac.uk/metagenomics/"
    "projects/{study}/samples/{sample}/runs/{analysis}/"
    "results/versions/{pipeline}/function/GOAnnotations"
)


class Command(BaseCommand):

    obj_list = list()

    def add_arguments(self, parser):
        # parser.add_argument('rootpath', type=str)
        parser.add_argument('accession', type=str)

    def handle(self, *args, **options):
        self.find_accession(options)
        self.populate_from_accession()

    # def populate_from_path(self, options):
    #     # check if path is valid
    #     _path = options.get('importpath', None)
    #     if os.path.exists(_path):
    #         if os.path.isdir(_path):
    #             for root, dirs, files in os.walk(_path, topdown=False):
    #                 for name in files:
    #                     accession = name.split("_")[0]
    #                     f = os.path.join(root, name)
    #                     self.import_go(f, accession, pipeline)
    #         # TODO: is file get dir:
    #         elif os.path.isfile(_path):
    #             raise NotImplemented("Give path to directory.")
    #     else:
    #         raise NotImplemented("Path doesn't exist.")

    def find_accession(self, options):
        _accession = options.get('accession', None)
        if _accession:
            try:
                self.obj_list = emg_models.AnalysisJob.objects \
                    .filter(sample__study__accession=_accession)
            except exceptions.FieldError:
                try:
                    self.obj_list = emg_models.AnalysisJob.objects \
                        .filter(sample__accession=_accession)
                except exceptions.FieldError:
                    self.obj_list = emg_models.AnalysisJob.objects \
                        .filter(accession=_accession)

    def populate_from_accession(self):
        for o in self.obj_list:
            # raise emg_models.AnalysisJob.DoesNotExist
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

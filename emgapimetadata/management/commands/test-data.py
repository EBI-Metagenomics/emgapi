#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv

from django.core.management.base import BaseCommand

from emgapimetadata import models as m_models


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('importpath', type=str)

    def handle(self, *args, **options):
        self.populate(options)

    def populate(self, options):
        # check if path is valid
        _path = options.get('importpath', None)
        if os.path.exists(_path):
            if os.path.isdir(_path):
                for root, dirs, files in os.walk(_path, topdown=False):
                    for name in files:
                        accession = name.split("_")[0]
                        f = os.path.join(root, name)
                        if name.endswith("go"):
                            self.import_go(f, accession)
            # TODO: is file get dir:
            elif os.path.isfile(_path):
                raise NotImplemented("Give path to directory.")
        else:
            raise NotImplemented("Path doesn't exist.")

    def import_go(self, f, accession):
        with open(f, newline='') as fcsv:
            reader = csv.reader(fcsv)
            run = m_models.Run()
            run.accession = "ERR700147"
            run.pipeline_version = "1.0"
            for row in reader:
                try:
                    ann = m_models.Annotation(
                        accession=row[0],
                        description=row[1],
                        lineage=row[2],
                    ).save()
                except:
                    ann = m_models.Annotation.objects.get(accession=row[0])
                rann = m_models.RunAnnotation()
                rann.count = row[3]
                rann.annotation = ann
                run.annotations.append(rann)
            # ranns = m_models.RunAnnotation.objects.insert(ranns)
            run.save()

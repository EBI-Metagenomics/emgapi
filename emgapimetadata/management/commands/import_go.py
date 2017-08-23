#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv

from emgapimetadata import models as m_models

from ..lib import EMGBaseCommand


class Command(EMGBaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('suffix', nargs='?', type=str, default='.go')

    def populate_from_accession(self, options):
        for o in self.obj_list:
            self.find_path(o, options)

    def find_path(self, obj, options):
        rootpath = options.get('rootpath', None)
        suffix = options.get('suffix', None)

        res = os.path.join(rootpath, obj.result_directory)
        if os.path.exists(res):
            if os.path.isdir(res):
                for root, dirs, files in os.walk(res, topdown=False):
                    for name in files:
                        if name.endswith(suffix):
                            with open(os.path.join(root, name)) as csvfile:
                                reader = csv.reader(csvfile, delimiter=',')
                                self.import_go(
                                    reader, obj.accession,
                                    obj.pipeline.release_version
                                )
                            continue
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

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import logging

from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

    def populate_from_accession(self, options):
        logger.info("Found %d" % len(self.obj_list))
        for o in self.obj_list:
            self.find_path(o, options)

    def find_path(self, obj, options):
        rootpath = options.get('rootpath', None)

        res = os.path.join(rootpath, obj.result_directory, 'taxonomy-summary')
        if os.path.exists(res):
            _f = None
            if obj.pipeline.release_version in ('1.0', '2.0', '3.0'):
                logger.info("Pipeline version: %s" %
                            obj.pipeline.release_version)
                _f = os.path.join(res, 'krona-input.txt')
            if _f is not None and os.path.exists(_f) and os.path.isfile(_f):
                logger.info("Found: %s" % _f)
                with open(_f) as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    self.load_organism_from_summary_file(
                        reader, obj
                    )
            else:
                logger.error("Path %r exist. No Taxonomy SKIPPING!" % res)
        else:
            logger.error("Path %r doesn't exist. SKIPPING!" % res)

    def load_organism_from_summary_file(self, reader, obj):  # noqa
        try:
            run = m_models.AnalysisJobTaxonomy.objects \
                .get(pk=str(obj.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            run = m_models.AnalysisJobTaxonomy()
        run.analysis_id = str(obj.job_id)
        run.accession = obj.accession
        run.pipeline_version = obj.pipeline.release_version

        for row in reader:
            try:
                row[0].lower()
            except KeyError:
                pass
            else:
                pass

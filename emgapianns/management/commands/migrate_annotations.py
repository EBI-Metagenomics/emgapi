#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('accession', type=str)

    def populate_from_accession(self, options):
        logger.info("Migration, found %d" % len(self.obj_list))
        for o in self.obj_list:
            self.migrate_annotations(o)

    def migrate_annotations(self, obj):
        accession = obj.accession
        if accession is not None:
            logger.info("Migrating %s" % accession)

            old_anls = m_models.AnalysisJobGoTerm.objects \
                .get(accession=accession)
            new_anls = m_models.AnalysisJobGoTerm2()
            new_anls.analysis_id = str(old_anls.job_id)
            new_anls.accession = old_anls.accession
            new_anls.pipeline_version = old_anls.pipeline_version
            new_anls.job_id = old_anls.job_id
            new_anls.go_terms = old_anls.go_terms
            new_anls.go_slim = old_anls.go_slim
            new_anls.save()

            logger.info("AnalysisJobGoTerm DONE!")

            old_anls = m_models.AnalysisJobInterproIdentifier.objects \
                .get(accession=accession)
            new_anls = m_models.AnalysisJobInterproIdentifier2()
            new_anls.analysis_id = str(old_anls.job_id)
            new_anls.accession = old_anls.accession
            new_anls.pipeline_version = old_anls.pipeline_version
            new_anls.job_id = old_anls.job_id
            new_anls.interpro_identifiers = old_anls.interpro_identifiers
            new_anls.save()

            logger.info("AnalysisJobInterproIdentifier DONE!")

        else:
            raise AttributeError("Accession %s not found" % accession)

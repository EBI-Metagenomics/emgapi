#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import logging

from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


ORGANISM_PREFIX = {
    '1.0': ['kingdom', 'phylum', 'class', 'order', 'family', 'genus',
            'species'],
    '2.0': ['kingdom', 'phylum', 'class', 'order', 'family', 'genus',
            'species'],
    '3.0': ['kingdom', 'phylum', 'class', 'order', 'family', 'genus',
            'species'],
    '4.0': ['super kingdom', 'kingdom', 'phylum', 'class', 'order', 'family',
            'genus', 'species'],
}


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
                    self.load_organism_from_summary_file(reader, obj)
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
        version = obj.pipeline.release_version
        run.pipeline_version = version

        new_orgs = list()
        orgs = []
        for row in reader:
            count = row[0]
            lineage = list(map(str.rstrip, row[1:]))
            if len(lineage) > 1:
                name = lineage[-1]
                ancestors = lineage[0:-1]
                parent = ancestors[-1]
                prefix = ORGANISM_PREFIX[version][len(ancestors)]
            else:
                ancestors = []
                parent = None
                try:
                    if len(lineage[0]) > 0:
                        name = lineage[0]
                        prefix = ORGANISM_PREFIX[version][len(ancestors)]
                    else:
                        name = "Unusigned"
                        prefix = None
                        lineage = ["Unusigned"]
                except KeyError:
                    name = "Unusigned"
                    prefix = None
                    lineage = ["Unusigned"]
            organism = None
            try:
                organism = m_models.Organism.objects.get(pk=":".join(lineage))
            except m_models.Organism.DoesNotExist:
                organism = m_models.Organism(
                    lineage=":".join(lineage), name=name, parent=parent,
                    ancestors=ancestors, prefix=prefix
                )
                new_orgs.append(organism)

            if organism is not None:
                orgs.append(organism)
                rorg = m_models.AnalysisJobOrganism(
                    count=count,
                    organism=organism
                )
                run.taxonomy.append(rorg)

        if len(orgs) > 0:
            logger.info(
                "Total %d Organisms for Run: %s %s" % (
                    len(orgs), obj.accession, version))
            if len(new_orgs) > 0:
                m_models.Organism.objects.insert(new_orgs)
                logger.info(
                    "Created %d new Organisms" % len(new_orgs))
            run.save()
            logger.info("Saved Run %r" % run)

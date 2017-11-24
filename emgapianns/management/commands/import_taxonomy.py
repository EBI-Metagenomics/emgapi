#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import logging
import re

from emgapianns import models as m_models

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


ORGANISM_RANK = {
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

    def load_data_from_file(self, f, obj):
        if f is not None and os.path.exists(f) and os.path.isfile(f):
            logger.info("Found: %s" % f)
            with open(f) as csvfile:
                reader = csv.reader(csvfile, delimiter='\t')
                self.load_organism_from_summary_file(reader, obj)
        else:
            logger.error("Path %r exist. No Taxonomy SKIPPING!" % f)

    def find_path(self, obj, options):
        rootpath = options.get('rootpath', None)
        res = os.path.join(rootpath, obj.result_directory)
        if os.path.exists(res):
            logger.info("Pipeline version: %s" %
                        obj.pipeline.release_version)
            if obj.pipeline.release_version in ('1.0',):
                _f = os.path.join(res, 'taxonomy-summary', 'krona-input.txt')
                if os.path.exists(_f):
                    logger.info("Taxonomy loading: %s" % _f)
                    with open(_f) as csvfile:
                        reader = csv.reader(csvfile, delimiter='\t')
                        self.load_organism_from_summary_file(
                            reader, obj, 'taxonomy')
            elif obj.pipeline.release_version in ('2.0', '3.0',):
                name = "%s_qiime_assigned_taxonomy.txt" % (obj.input_file_name)
                _f = os.path.join(res, 'cr_otus', name)
                if os.path.exists(_f):
                    logger.info("Taxonomy loading: %s" % _f)
                    with open(_f) as csvfile:
                        reader = csv.DictReader(csvfile, delimiter='\t')
                        self.load_organism_from_summary_file(
                            reader, obj, 'taxonomy', otu=True)
            elif obj.pipeline.release_version in ('4.0',):
                name = "%s_SSU.fasta.mseq.txt" % (obj.input_file_name)
                _f = os.path.join(res, 'taxonomy-summary', 'SSU', name)
                if os.path.exists(_f):
                    logger.info("SSU loading: %s" % _f)
                    with open(_f) as csvfile:
                        reader = csv.reader(csvfile, delimiter='\t')
                        self.load_organism_from_summary_file(
                            reader, obj, 'taxonomy_ssu')
                name = "%s_LSU.fasta.mseq.txt" % (obj.input_file_name)
                _f = os.path.join(res, 'taxonomy-summary', 'LSU', name)
                if os.path.exists(_f):
                    logger.info("LSU loading: %s" % _f)
                    with open(_f) as csvfile:
                        reader = csv.reader(csvfile, delimiter='\t')
                        self.load_organism_from_summary_file(
                            reader, obj, 'taxonomy_lsu')
            else:
                logger.error("Pipeline not supported SKIPPING!")
        else:
            logger.error("Path %r doesn't exist. SKIPPING!" % res)

    def _instantiate_entry(self, obj):
        try:
            run = m_models.AnalysisJobTaxonomy.objects \
                .get(pk=str(obj.job_id))
        except m_models.AnalysisJobTaxonomy.DoesNotExist:
            run = m_models.AnalysisJobTaxonomy()
        run.analysis_id = str(obj.job_id)
        run.accession = obj.accession
        run.pipeline_version = obj.pipeline.release_version
        run.job_id = obj.job_id
        return run

    def _get_unassigned(self, name):
        if len(name) < 1:
            raise AttributeError('Name not provided.')
        rank = None
        lineage = [name]
        hierarchy = {}
        domain = None
        ancestors = []
        parent = None
        return name, rank, lineage, hierarchy, domain, ancestors, parent

    def load_organism_from_summary_file(self, reader, obj, tax, otu=False):  # noqa
        run = self._instantiate_entry(obj)
        version = obj.pipeline.release_version
        new_orgs = dict()
        orgs = list()
        for row in reader:
            if otu:
                count = int(float(row[obj.accession]))
                _l = row['taxonomy'] \
                    .replace('Root;', '') \
                    .replace("/", "|").split(";")
                otu_id = row.get('#OTU ID', None)
            else:
                if len(row) < 1:
                    continue
                count = int(float(row[0]))
                _l = row[1:]
                otu_id = None

            def clean_prefix(s):
                return re.sub(r"[a-zA-Z]+__", "", s.rstrip())
            lineage = list(map(clean_prefix, _l))

            for l in reversed(lineage):
                if len(l) < 1:
                    lineage.remove(l)
                else:
                    break

            if len(lineage) > 1:
                hierarchy = {
                    r: a for r, a in zip(ORGANISM_RANK[version], lineage)
                }
                domain = lineage[0]
                name = lineage[-1]
                ancestors = lineage[0:-1]
                parent = ancestors[-1]
                rank = ORGANISM_RANK[version][len(ancestors)]
            else:
                try:
                    if lineage[0] not in ('Root',) and len(lineage[0]) > 0:
                        ancestors = []
                        parent = None
                        hierarchy = {
                            r: a for r, a in zip(ORGANISM_RANK[version],
                                                 lineage)
                        }
                        domain = lineage[0]
                        name = lineage[0]
                        rank = ORGANISM_RANK[version][len(ancestors)]
                    else:
                        name, rank, lineage, hierarchy, domain, ancestors, \
                            parent = self._get_unassigned("Unassigned")
                except IndexError:
                    name, rank, lineage, hierarchy, domain, ancestors,\
                        parent = self._get_unassigned("Unclassified")
                except KeyError:
                    name, rank, lineage, hierarchy, domain, ancestors,\
                        parent = self._get_unassigned("Unassigned")
            organism = None
            _lineage = ":".join(lineage)
            try:
                organism = m_models.Organism.objects.get(
                    lineage=_lineage, rank=rank,
                    pipeline_version=version
                )
            except m_models.Organism.DoesNotExist:
                # TODO: https://github.com/MongoEngine/mongoengine/issues/1685
                # pk = {'lineage': ":".join(lineage), 'version': version}
                pk = "{}|{}".format(_lineage, version)
                try:
                    organism = new_orgs[pk]
                except KeyError:
                    organism = m_models.Organism(
                        id=pk, lineage=_lineage, name=name, parent=parent,
                        ancestors=ancestors, hierarchy=hierarchy,
                        rank=rank, pipeline_version=version, domain=domain,
                    )
                    new_orgs[pk] = organism
                    orgs.append(organism)

            if organism is not None:
                rorg = m_models.AnalysisJobOrganism(
                    count=count, organism=organism, otu=otu_id
                )
                t = getattr(run, tax, list())
                t.append(rorg)
                setattr(run, tax, t)

        if len(orgs) > 0:
            logger.info(
                "Total %d Organisms for Run: %s %s" % (
                    len(orgs), obj.accession, version))
            if len(new_orgs) > 0:
                m_models.Organism.objects.insert(new_orgs.values())
                logger.info(
                    "Created %d new Organisms" % len(new_orgs))
            run.save()
            logger.info("Saved Run %r" % run)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2023 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re

from django.core.management import BaseCommand
from django.template.loader import render_to_string

from emgapi.models import AnalysisJob
from emgapianns.models import (
    AnalysisJobTaxonomy,
    AnalysisJobGoTerm,
    AnalysisJobInterproIdentifier,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate the XML dump of an analysis."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-a", "--accession", help="Analysis accession", required=True
        )
        parser.add_argument("-o", "--output", help="Output xml file", required=True)

    # TODO: this was ported directly from EBI Search Dump
    # we need to improve it, maybe move it to a template tag?
    # TODO: apply this to InterPro and GO annotations
    def unicode_and_clean(self, identifier, text):
        """Converts text to utf8 encoded string with xml subsitutions"""
        if not text:
            return text
        try:
            text = text.encode("utf8", "strict")
        except Exception as ex:
            match = re.search(r"in position (\d+)", str(ex))
            if match:
                position = int(match.group(1))
                matchStart = position - 15
                if matchStart < 0:
                    matchStart = 0
                matchEnd = position + 15
                if matchEnd > len(text):
                    matchEnd = len(text)
                logger.error(
                    f"Replacing '{identifier}' in {text[position]} [{text[matchStart:matchEnd]}]",
                    ex,
                )
                text = text[:position] + text[position + 1 :]
                text = self.unicode_and_clean(identifier, text)
            else:
                logger.error(f"Failed to convert: {identifier}.", ex)
        return text.decode("utf8")

    def handle(self, *args, **options):
        """Render an analysis using the EBI Search XML template"""
        # TODO: The migration for the analysis should be nearly done, code ported from: https://github.com/EBI-Metagenomics/MetagenomicsSearchDump
        # In that repo the analyses corresponds to the Run entries.
        accession: str = options["accession"]
        analysis: AnalysisJob = AnalysisJob.objects.get(job_id=accession)
        analysis_taxonomy: AnalysisJobTaxonomy = AnalysisJobTaxonomy.objects.get(
            analysis_id=str(analysis.job_id)
        )
        go_annotation: AnalysisJobGoTerm = AnalysisJobGoTerm.objects.get(
            pk=str(analysis.job_id)
        )
        ips_annotation: AnalysisJobInterproIdentifier = AnalysisJobInterproIdentifier.objects.get(
            pk=str(analysis.job_id)
        )

        biome_list = analysis.study.biome.lineage.split(":")[1:]

        taxonomy_lists = []
        taxonomy_attributes = [
            analysis_taxonomy.taxonomy,
            analysis_taxonomy.taxonomy_ssu,
            analysis_taxonomy.taxonomy_lsu,
            analysis_taxonomy.taxonomy_itsonedb,
            analysis_taxonomy.taxonomy_itsunite,
        ]
        for taxonomy_attribute in taxonomy_attributes:
            if taxonomy_attribute:
                for tax in taxonomy_attribute:
                    tax_lineage_list = list(filter(None, tax.lineage.split(":")))
                    if len(tax_lineage_list) > 1:
                        taxonomy_lists.append(
                            [
                                self.unicode_and_clean("tax", tax_el)
                                for tax_el in tax_lineage_list
                            ]
                        )

        # TODO: port these metadata "cleaning" rules.
        # if depth and len(depth) > 0:
        #     self.depth = checkIfNumerical(extID, depth)
        # if altitude and len(altitude) > 0:
        #     self.altitude = checkIfNumerical(extID, altitude)
        # if elevation and len(elevation) > 0:
        #     self.elevation = checkIfNumerical(extID, elevation)
        # if salinity and len(salinity) > 0:
        #     self.salinity = checkIfNumerical(extID, salinity)
        # if temperature and len(temperature) > 0:
        #     self.temperature = checkIfNumerical(extID, temperature)
        # if pH and len(pH) > 0:
        #     self.pH = checkIfNumerical(extID, pH[0])
        # if longitudeStart and len(longitudeStart) > 0:
        #     self.longitudeStart = encodeToUnicodeAndClean(extID, longitudeStart)
        # if longitudeEnd and len(longitudeEnd) > 0:
        #     self.longitudeEnd = checkIfNumerical(extID, longitudeEnd)
        # if latitudeStart and len(latitudeStart) > 0:
        #     self.latitudeStart = checkIfNumerical(extID, latitudeStart)
        # if latitudeEnd and len(latitudeEnd) > 0:
        #     self.latitudeEnd = checkIfNumerical(extID, latitudeEnd)

        # TODO: from this list (taken from )
        SAMPLE_ANNOTATIONS_ACCEPT_LIST = {
            "temperature": "temperature",
            "pH": "pH",
            "altitude": "altitude",
            "depth": "depth",
            "elevation": "elevation",
            "geographic location (elevation)": "elevation",
            "geographic location (depth)": "depth",
            "salinity": "salinity",
            "longitude start": "longitudeStart",
            "latitude start": "latitudeStart",
            "longitude end": "longitudeEnd",
            "latitude end": "latitudeEnd",
        }

        sample_metadata = {}
        for sample_metadata_entry in analysis.sample.metadata.all():
            if sample_metadata_entry.var.var_name in SAMPLE_ANNOTATIONS_ACCEPT_LIST:
                sample_metadata[
                    SAMPLE_ANNOTATIONS_ACCEPT_LIST[sample_metadata_entry.var.var_name]
                ] = sample_metadata_entry.var_val_ucv

        print(
            render_to_string(
                "ebi_search/analysis.xml",
                {
                    "analysis": analysis,
                    "analysis_biome": biome_list,
                    "analysis_taxonomies": taxonomy_lists,
                    "analysis_go_entries": go_annotation.go_terms,
                    "analysis_ips_entries": ips_annotation.interpro_identifiers,
                    "sample_metadata": sample_metadata,
                },
            )
        )

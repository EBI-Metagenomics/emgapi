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
import pathlib
from datetime import timedelta
from typing import Optional

from django.core.management import BaseCommand
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.utils import timezone

from emgapi.models import AnalysisJob
from emgapianns.models import (
    AnalysisJobTaxonomy,
    AnalysisJobGoTerm,
    AnalysisJobInterproIdentifier,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate the XML dump of analyses for EBI Search."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--full",
            action="store_true",
            help="Create a full snapshot rather than incremental.",
        )
        parser.add_argument("-o", "--output", help="Output dir for xml files", required=True)
        parser.add_argument("-c", "--chunk", help="Number of analyses per chunk", default=100, nargs='?', type=int)
        parser.add_argument("-m", "--max_pages", help="Max number of pages to dump", default=-1, type=int)

    def get_analysis_context(self, analysis: AnalysisJob):
        try:
            analysis_taxonomy: Optional[AnalysisJobTaxonomy] = AnalysisJobTaxonomy.objects.get(
                pk=str(analysis.job_id)
            )
        except AnalysisJobTaxonomy.DoesNotExist:
            logger.debug(f"Could not find analysis job taxonomy for {analysis.job_id}")
            analysis_taxonomy = None

        try:
            go_annotation: Optional[AnalysisJobGoTerm] = AnalysisJobGoTerm.objects.get(
                pk=str(analysis.job_id)
            )
        except AnalysisJobGoTerm.DoesNotExist:
            logger.debug(f"Could not find go terms for {analysis.job_id}")
            go_annotation = None

        try:
            ips_annotation: Optional[AnalysisJobInterproIdentifier] = AnalysisJobInterproIdentifier.objects.get(
                pk=str(analysis.job_id)
            )
        except AnalysisJobInterproIdentifier.DoesNotExist:
            logger.debug(f"Could not find IPS terms for {analysis.job_id}")
            ips_annotation = None

        biome_list = analysis.study.biome.lineage.split(":")[1:] or ['root']
        # to ensure there are no empty hierarchical fields

        taxonomy_lists = []
        if analysis_taxonomy:
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
                        tax_lineage_list = list(filter(None, tax.organism.pk.split('|')[0].split(":")))
                        if len(tax_lineage_list) > 1:
                            taxonomy_lists.append(
                                tax_lineage_list
                            )

        sample_numeric_fields_to_index = {
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

        sample_text_annotations_to_index = {
            "sequencing method": "sequencing_method",
            "geographic location (region and locality)": "location_name",
            "geographic location (country and/or sea,region)": "location_name",
            "disease status": "disease_status",
            "phenotype": "phenotype",
        }

        sample_annotations_to_index = sample_numeric_fields_to_index.copy()
        sample_annotations_to_index.update(sample_text_annotations_to_index)

        sample_metadata = {}
        for sample_metadata_entry in analysis.sample.metadata.all():
            if (vn := sample_metadata_entry.var.var_name) in sample_annotations_to_index:
                indexable_name = sample_annotations_to_index[vn]
                indexable_value = sample_metadata_entry.var_val_ucv

                if indexable_name in sample_numeric_fields_to_index.values():
                    try:
                        indexable_value = float(indexable_value.strip())
                    except ValueError:
                        logger.debug(
                            f"Could not float-parse supposedly numeric field {indexable_name} : {indexable_value}")
                        continue
                sample_metadata[
                    indexable_name
                ] = indexable_value

        if 'location_name' not in sample_metadata and analysis.sample.geo_loc_name:
            sample_metadata['location_name'] = analysis.sample.geo_loc_name
        return {
            "analysis": analysis,
            "analysis_biome": biome_list,
            "analysis_taxonomies": taxonomy_lists,
            "analysis_go_entries": [go.go_term.pk for go in go_annotation.go_terms] if go_annotation else [],
            "analysis_ips_entries": [ipr.interpro_identifier.pk for ipr in ips_annotation.interpro_identifiers] if ips_annotation else [],
            # .pk ensures the IPR and GO documents are not queried on mongo, which would have a big performance hit
            "sample_metadata": sample_metadata,
        }

    @staticmethod
    def write_without_blank_lines(fp, string):
        fp.write(
            "\n".join(
                filter(
                    str.strip,
                    string.splitlines()
                )
            )
        )

    def handle(self, *args, **options):
        """Dump EBI Search XML file of analyses"""
        is_full_snapshot: str = options["full"]
        output_dir: str = options["output"]
        chunk_size: int = options["chunk"]

        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

        analyses: QuerySet = AnalysisJob.objects_dump.available(None)

        if not is_full_snapshot:
            analyses = AnalysisJob.objects_for_indexing.to_add()

            removals = AnalysisJob.objects_for_indexing.to_delete()

            # produce incremental deletion file
            deletions_file = pathlib.Path(output_dir) / pathlib.Path('analyses-deletes.xml')
            with open(deletions_file, 'w') as d:
                self.write_without_blank_lines(d,
                    render_to_string(
                        "ebi_search/analyses-deletes.xml",
                        {
                            "removals": removals
                        }
                    )
                )

        paginated_analyses = Paginator(analyses, chunk_size)

        for page in paginated_analyses:
            if (mp := options["max_pages"]) >= 0:
                if page.number > mp:
                    logger.warning("Skipping remaining pages")
                    break
            logger.info(f"Dumping {page.number = }/{paginated_analyses.num_pages}")
            additions_file = pathlib.Path(output_dir) / pathlib.Path(f'analyses_{page.number:04}.xml')
            with open(additions_file, 'w') as a:
                self.write_without_blank_lines(a,
                    render_to_string(
                        "ebi_search/analyses.xml",
                        {
                            "additions": (self.get_analysis_context(analysis) for analysis in page),
                            "count": len(page)
                        }
                    )
                )
            nowish = timezone.now() + timedelta(minutes=1)
            # Small buffer into the future so that the indexing time remains ahead of auto-now updated times.

            for analysis in page:
                analysis.last_ebi_search_indexed = nowish

            AnalysisJob.objects.bulk_update(page, fields=["last_ebi_search_indexed"])

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

from django.core.management import BaseCommand
from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.utils import timezone

from emgapi.models import Study

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate the XML dump of studies for EBI Search."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--full",
            action="store_true",
            help="Create a full snapshot rather than incremental.",
        )
        parser.add_argument("-o", "--output", help="Output dir for xml files", required=True)


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

    @staticmethod
    def get_study_context(study: Study):
        biome_list = study.biome.lineage.split(":")[1:]

        return {
            "study": study,
            "biome_list": biome_list
        }

    def handle(self, *args, **options):
        """Dump EBI Search XML file of studies/projects"""
        is_full_snapshot: str = options["full"]
        output_dir: str = options["output"]

        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

        studies: QuerySet = Study.objects.available(None)

        if not is_full_snapshot:
            studies = Study.objects_for_indexing.to_add()

            removals = Study.objects_for_indexing.to_delete()

            # produce incremental deletion file
            deletions_file = pathlib.Path(output_dir) / pathlib.Path('projects-deletes.xml')
            with open(deletions_file, 'w') as d:
                self.write_without_blank_lines(d,
                    render_to_string(
                        "ebi_search/projects-deletes.xml",
                        {
                            "removals": removals
                        }
                    )
                )

        additions_file = pathlib.Path(output_dir) / pathlib.Path('projects.xml')
        with open(additions_file, 'w') as a:
            self.write_without_blank_lines(a,
                render_to_string(
                    "ebi_search/projects.xml",
                    {
                        "additions": (self.get_study_context(study) for study in studies),
                        "count": studies.count()
                    }
                )
            )

        nowish = timezone.now() + timedelta(minutes=1)
        # Small buffer into the future so that the indexing time remains ahead of auto-now updated times.

        for study in studies:
            study.last_indexed = nowish

        Study.objects.bulk_update(studies, fields=["last_indexed"])

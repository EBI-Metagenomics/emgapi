#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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

import json
import logging
import os
import glob

from emgapi.models import ChecksumAlgorithm, AnalysisJobDownload

from ..lib import EMGBaseCommand

logger = logging.getLogger(__name__)


class Command(EMGBaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("-a", "--algorithm",  type=str, choices=["SHA1", "MD5"], default="SHA1",
                            help="Checksum algorithm used.")

    def populate_from_accession(self, options):
        logger.info("Found %d" % len(self.obj_list))
        for analysis_job in self.obj_list:
            self.process(analysis_job, options)

    def process(self, analysis_job, options):
        """Import the checksums from the json outputs
        Example structure:
        {
            "qc-status": {
                "checksum": "sha1$da39a3ee5e6b4b0d3255bfef95601890afd80709",
                "basename": "QC-PASSED",
                "nameext": "",
                "nameroot": "QC-PASSED",
                "location": ".../ERZ1292616_FASTA_1/QC-PASSED",
                "class": "File",
                "size": 0
            }, {
            "qc-statistics_folder": {
                "basename": "qc-statistics",
                "nameext": "",
                "nameroot": "qc-statistics",
                "location": ".../ERZ1292616_FASTA_1/qc-statistics",
                "listing": [
                    {
                        "checksum": "sha1$8fdd43b4c32527615b6389d538028a0714daca0d",
                        "basename": "GC-distribution.out.full",
                        "size": 5203,
                        "class": "File",
                        "location": ".../GC-distribution.out.full"
                    }
            },...
        }
        """
        logger.info("CLI %r" % options)

        # a few helper variables
        self.analysis_job = analysis_job
        self.algorithm = ChecksumAlgorithm.objects.get(name=options["algorithm"])

        analysis_files = list(AnalysisJobDownload.objects.filter(job=analysis_job))
        self.aj_dict = {aj_d.realname: aj_d for aj_d in analysis_files}

        if not len(analysis_files):
            logger.warning("There are no files for " + str(analysis_job))
            return

        path = os.path.join(
            options.get("rootpath"),
            analysis_job.result_directory,
            "checksums-*.json")

        json_files = glob.glob(path)

        if not len(json_files):
            logger.warning("NO checksum files: " + path)
            return

        for json_file in json_files:
            logger.info("Processing %s" % json_file)
            with open(json_file, "r") as jf_handler:
                data = json.load(jf_handler)
                for value in data.values():
                    # there could be files or directories
                    entries = value if isinstance(value, list) else [value]
                    for entry in entries:
                        self.process_entry(entry)

    def process_entry(self, entry):
        r_type = entry.get("class")
        if r_type == "File":
            self.process_file(entry)
        elif r_type == "Directory":
            for sub_entry in entry.get("listing"):
                self.process_entry(sub_entry)

    def process_file(self, file_entry):
        """Process an File file_entry from the json file
        """
        checksum = file_entry.get("checksum").split("$")[1]
        basename = file_entry.get("basename")

        ajd_file = self.aj_dict.get(basename, None)

        if not ajd_file:
            logger.info("%s is not a file for %s" % (basename, self.analysis_job))
            return

        ajd_file.file_checksum = checksum
        ajd_file.checksum_algorithm = self.algorithm
        # TODO: use bulk_update when django is updated
        ajd_file.save()

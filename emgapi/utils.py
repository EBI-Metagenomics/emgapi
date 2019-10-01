# -*- coding: utf-8 -*-

# Copyright 2018 EMBL - European Bioinformatics Institute
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

from django.db.models import Q

logger = logging.getLogger(__name__)


def study_accession_query(accession):
    query = list()
    try:
        query.append(Q(pk=int(accession.lstrip('MGYS'))))
    except ValueError:
        query.append(
            Q(secondary_accession=accession) |
            Q(project_id=accession)
        )
    return query


def sample_study_accession_query(accession):
    query = list()
    try:
        query.append(Q(studies__pk=int(accession.lstrip('MGYS'))))
    except ValueError:
        query.append(
            Q(studies__secondary_accession=accession) |
            Q(studies__project_id=accession)
        )
    return query


def related_study_accession_query(accession):
    query = list()
    try:
        query.append(Q(study__pk=int(accession.lstrip('MGYS'))))
    except ValueError:
        query.append(
            Q(study__secondary_accession=accession) |
            Q(study__project_id=accession)
        )
    return query


def analysisjob_accession_query(accession):
    query = list()
    try:
        query.append(Q(pk=int(accession.lstrip('MGYA'))))
    except ValueError:
        pass
    return query


def assembly_contig_name(line):
    """Parses Mgnify (ENA) assembly contigs names and returns the contig name with no metadata.
    
    For example:
    ENA-OKXA01000001-OKXA01000001.1-human-gut-metagenome-strain-
    SKBSTL060-genome-assembly--contig:-NODE-1-length-34650-cov-6.786732
    get the the contig name: NODE-1-length-34650-cov-6.786732

    """
    return re.sub(r'[^\t=]*\-\-contig\:\-', '', line)

def assembly_contig_coverage(name):
    """From a contig name return the coverage (from the fasta name)

    Example:
    From NODE-1-length-34650-cov-6.786732 will return 6.786732 or '-' if failed. 
    """
    match = re.match(r'.*cov[-|_](?P<cov>\d*\.?\d*)', name)
    if match:
        return match.group('cov')
    return 0

# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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
import os
import re

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, FileResponse

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
    Example:
        ENA-OKXA01000001-OKXA01000001.1-human-gut-metagenome-strain-
        SKBSTL060-genome-assembly--contig:-NODE-1-length-34650-cov-6.786732
    will return the contig name: NODE-1-length-34650-cov-6.786732
    """
    return re.sub(r'[^\t=]*\-\-contig\:\-', '', line)


def assembly_contig_coverage(name):
    """From a contig name return the coverage (from the fasta name)
    Example:
        NODE-1-length-34650-cov-6.786732
    will return 6.786732 or 0 if failed.
    """
    match = re.match(r'.*cov[-|_](?P<cov>\d*\.?\d*)', name)
    if match:
        return match.group('cov')
    return 0


def parse_ebi_search_entry(entry, fields):
    """Convert EBI Search json entry to tuple
    """
    row = []
    entry_fields = entry.get("fields", {})
    for f in fields:
        value = entry_fields.get(f, [])
        if value:
            row.append(value[0] if len(value) else "")
    return row


def prepare_results_file_download_response(path_in_results, alias):
    """Create a response with NGINX redirect header set,
    or attach content if DOWNLOADS_BYPASS_NGINX is set.

    :param path_in_results: file path relative to RESULTS_DIR
    :param alias: filename alias for response
    :return: Http Response
    """
    response = HttpResponse()
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = \
        'attachment; filename={0}'.format(alias)

    # Workaround for non-nginx hosts, like running locally in docker
    if settings.DOWNLOADS_BYPASS_NGINX:
        logger.warning('DOWNLOADS_BYPASS_NGINX is true, so serving download directly as Django response '
                       '(not via NGINX redirect)')
        if str(path_in_results).endswith('zip'):
            return FileResponse(open(os.path.join(settings.RESULTS_DIR, path_in_results.lstrip('/')), 'rb'))
        with open(os.path.join(settings.RESULTS_DIR, path_in_results.lstrip('/')), 'r') as file:
            response.content = file.read()
    else:
        response['X-Accel-Redirect'] = '/results/{0}'.format(path_in_results.lstrip('/'))
    return response

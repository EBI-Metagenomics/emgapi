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

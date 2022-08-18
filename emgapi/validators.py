#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2022 EMBL - European Bioinformatics Institute
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

import re
from django.core.exceptions import ValidationError

STUDY_ACCESSION_RE = re.compile(r"(PRJ(E|D|N)[A-Z][0-9]+)|((E|D|S)RP[0-9]{6,})")
STUDY_ACCESSION_URL = "https://ena-docs.readthedocs.io/en/latest/submit/general-guide/accessions.html#accession-numbers"


def validate_ena_study_accession(value):
    """ENA Study/Project accession validation.
    Format: https://ena-docs.readthedocs.io/en/latest/submit/general-guide/accessions.html#accession-numbers
    """
    if not value or not STUDY_ACCESSION_RE.match(value):
        raise ValidationError(
            f"{value} is not an valid ENA Accession. Please check: {STUDY_ACCESSION_URL}"
        )

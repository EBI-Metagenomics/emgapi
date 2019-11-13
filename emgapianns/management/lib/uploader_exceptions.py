#!/usr/bin/env python
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


class AccessionNotRecognised(Exception):
    """Raised when the given run or analysis accession could not be recognised"""
    pass


class StudyNotBeRetrievedFromENA(Exception):
    """Raised when study could not be retrieved from the ENA API"""
    pass


class NoAnnotationsFoundError(Exception):
    """Raised when no annotations found in result files"""
    pass


class QCNotPassedError(Exception):
    """Raised when qc not passed flag file found"""
    pass


class CoverageCheckError(Exception):
    """Raised when coverage check fails due to missing expected files"""
    pass

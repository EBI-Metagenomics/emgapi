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
from enum import Enum


class Analysis(object):
    def __init__(self, secondary_study_accession, secondary_sample_accession, run_accession, experiment_type, **kwargs):
        self.secondary_study_accession = secondary_study_accession
        self.sample_accession = secondary_sample_accession
        self.run_accession = run_accession
        self.experiment_type = experiment_type


class Run(Analysis):
    def __init__(self, secondary_study_accession, secondary_sample_accession, run_accession, library_strategy):
        super().__init__(secondary_study_accession, secondary_sample_accession, run_accession, library_strategy)


class Assembly(Analysis):
    def __init__(self, secondary_study_accession, secondary_sample_accession, run_accession, analysis_accession, **kwargs):
        super().__init__(secondary_study_accession, secondary_sample_accession, run_accession, ExperimentType.ASSEMBLY)
        self.analysis_accession = analysis_accession


class ExperimentType(Enum):
    AMPLICON = 'AMPLICON'
    WGS = 'WGS'
    OTHER = 'OTHER'
    RNA_SEQ = 'RNA-Seq'
    ASSEMBLY = 'ASSEMBLY'

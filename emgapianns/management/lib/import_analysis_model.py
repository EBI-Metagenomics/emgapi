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
    def __init__(self, secondary_study_accession, secondary_sample_accession, run_accession, library_strategy,
                 library_source):
        super().__init__(secondary_study_accession, secondary_sample_accession, run_accession,
                         identify(library_strategy, library_source).value)


class Assembly(Analysis):
    def __init__(self, secondary_study_accession, secondary_sample_accession, run_accession, analysis_accession,
                 **kwargs):
        super().__init__(secondary_study_accession, secondary_sample_accession, run_accession, ExperimentType.ASSEMBLY)
        self.analysis_accession = analysis_accession


class ExperimentType(Enum):
    """
        In the EMG database we do store the following experiment types at the moment.
            - metatranscriptomic.
            - metagenomic.
            - amplicon.
            - assembly.
            - metabarcoding.
            - unknown.

        Short form explanation for the most common library strategy:
            WGS: Whole genome sequencing
            WXS: Whole exome sequencing
            WGA: Whole genome amplification
            RNA-Seq: RNA Sequencing
            Tn-Seq: Transposon sequencing
            POOLCLONE: Pooled clone sequencing

        A list of all library strategies can be found here:
        http://www.ebi.ac.uk/ena/submit/reads-library-strategy
    """
    AMPLICON = 'amplicon'
    METAGENOMIC = 'metagenomic'
    METATRANSCRIPTOMIC = 'metatranscriptomic'
    OTHER = 'other'
    METABARCODING = 'metabarcoding'
    ASSEMBLY = 'assembly'


def identify(library_strategy, library_source):
    if library_strategy == 'WGS' and library_source == 'METATRANSCRIPTOMIC':
        return ExperimentType.METATRANSCRIPTOMIC
    elif library_strategy == 'WGS' and (
            library_source == 'METAGENOMIC' or library_source == 'GENOMIC'):
        return ExperimentType.METAGENOMIC
    elif library_strategy == 'AMPLICON':
        return ExperimentType.AMPLICON
    elif library_strategy == 'RNA-Seq':
        return ExperimentType.METATRANSCRIPTOMIC
    elif library_strategy == 'WXS':
        return ExperimentType.METAGENOMIC
    elif library_strategy == 'ASSEMBLY':
        return ExperimentType.ASSEMBLY
    else:
        return ExperimentType.OTHER

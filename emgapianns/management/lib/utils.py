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
import glob
import logging
import os
import re


def is_run_accession(accession):
    return re.match(r'([ESD]RR\d{6,})', accession)


def is_assembly_accession(accession):
    return re.match(r'(ERZ\d{6,})', accession)


def retrieve_existing_result_dir(rootpath, accession):
    """
        Searches file system for existing result folder.

        Example absolute path:
        /nfs/production/interpro/metagenomics/results/2019/07/ERP108931/version_4.1/ERZ651/009/ERZ651769_FASTA/
    :param rootpath:
    :param accession:
    :return:
    """
    dest_pattern = ['2*', '*', 'version_*', '*', '00*', accession]
    prod_study_dir = os.path.join(rootpath, *dest_pattern)

    existing_result_dir = [d.replace(rootpath, '') for d in glob.glob(prod_study_dir)]
    if existing_result_dir:
        logging.info(f'Found prod dirs: {existing_result_dir}')

    if len(existing_result_dir) == 0:
        logging.info('No existing result dirs found')
        return None
    else:
        # Return latest dir (sorted by year/month descending)
        dir = sorted(existing_result_dir, reverse=True)[0]
        dir = dir.strip('/')
        return dir

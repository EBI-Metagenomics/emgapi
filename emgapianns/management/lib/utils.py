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
import sys

from emgapianns.management.lib.import_analysis_model import Run, Assembly, ExperimentType
from emgapianns.management.lib.uploader_exceptions import AccessionNotRecognised


def is_run_accession(accession):
    return re.match(r'([ESD]RR\d{6,})', accession)


def is_assembly_accession(accession):
    return re.match(r'(ERZ\d{6,})', accession)


def retrieve_existing_result_dir(rootpath, dest_pattern):
    """
        Searches file system for existing result folder.

        Example absolute path:
        /nfs/production/interpro/metagenomics/results/2019/07/ERP108931/version_4.1/ERZ651/009/ERZ651769_FASTA/
    :param rootpath:
    :param dest_pattern: e.g. ['2*', '*', 'version_*', '*', '00*', ERP000001s]
    :return:
    """
    prod_study_dir = os.path.join(rootpath, *dest_pattern)

    existing_result_dir = [d.replace(rootpath, '') for d in glob.glob(prod_study_dir)]
    if existing_result_dir:
        logging.info('Found result dirs: {}'.format(existing_result_dir))

    if len(existing_result_dir) == 0:
        logging.info('No existing result dirs found')
        return None
    else:
        # Return latest dir (sorted by year/month descending)
        dir = sorted(existing_result_dir, reverse=True)[0]
        dir = dir.strip('/')
        return dir


def parse_run_metadata(raw_metadata):
    """
        Parses metadata attributes out of ENA's API response.
    :param raw_metadata: dict
    :return:
    """
    try:
        study_accession = raw_metadata['secondary_study_accession']
        sample_accession = raw_metadata['secondary_sample_accession']
        run_accession = raw_metadata['run_accession']
        library_strategy = raw_metadata['library_strategy']
        # Convert library_strategy string to ExperimentType Enum
        return Run(study_accession, sample_accession, run_accession, ExperimentType[library_strategy])
    except KeyError as err:
        print("Could NOT retrieve all run metadata need from ENA's API: {0}".format(err))
        raise
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise


def parse_assembly_metadata(raw_metadata):
    """
        Parses metadata attributes out of ENA's API response.
    :param raw_metadata: dict
    :return:
    """
    try:
        study_accession = raw_metadata['secondary_study_accession']
        sample_accession = raw_metadata['secondary_sample_accession']
        run_accession = raw_metadata['analysis_alias']
        analysis_accession = raw_metadata['analysis_accession']
        return Assembly(study_accession, sample_accession, run_accession, analysis_accession)
    except KeyError as err:
        print("Could NOT retrieve all run metadata need from ENA's API: {0}".format(err))
        raise
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise


def is_assembly(accession):
    """
        Returns True if assembly accession and FALSE if run accession.
    :param accession:
    :return:
    """
    if is_assembly_accession(accession):
        return True
    elif is_run_accession(accession):
        return False
    else:
        raise AccessionNotRecognised


location_reg = r'^(.+) (N|S) (.+) (W|E)$'


def get_lat_long(s):
    try:
        latlng = re.findall(location_reg, s)
        m = latlng[0]
        lat = float(m[0])
        lng = float(m[2])
        if m[1] == 'S':
            lat *= -1
        if m[3] == 'W':
            lng *= -1
        return lat, lng
    except IndexError:
        return None, None

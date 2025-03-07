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
import unicodedata

from YamJam import yamjam

from emgapi import models as emg_models
from emgapianns.management.lib.downloadable_files import ChunkedDownloadFiles, UnchunkedDownloadFile
from emgapianns.management.lib.import_analysis_model import Assembly, Run
from emgapianns.management.lib.uploader_exceptions import \
    AccessionNotRecognised
import emgapianns.management.lib.sanity_check as sanity
from emgapianns.management.webuploader_configs import get_downloadset_config

study_accssion_re = r'([ESD]RP\d{6,})'
run_accession_re = r'([ESD]RR\d{6,})'
assembly_accession_re = r'(ERZ\d{6,})'


def is_study_accession(accession):
    return re.match(study_accssion_re, accession)


def get_run_accession(path):
    pattern = re.compile(run_accession_re)
    match = re.search(pattern, path)
    if match:
        if len(match.groups()) > 0:
            return match.groups()[0]
        else:
            raise Exception("Could not identify run accession from {}".format(path))
    else:
        logging.warning("Could not find any run accession in assembly name {}".format(path))
        return None


def is_run_accession(accession):
    return re.match(run_accession_re, accession)


def retrieve_existing_result_dir(rootpath, dest_pattern):
    """Searches file system for existing result folder.
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
        library_source = raw_metadata['library_source']
        # Convert library_strategy string to ExperimentType Enum
        return Run(study_accession, sample_accession, run_accession, library_strategy, library_source)
    except KeyError as err:
        print("Could NOT retrieve all run metadata need from ENA's API: {0}".format(err))
        raise
    except:  # noqa
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
    except:  # noqa
        print("Unexpected error:", sys.exc_info()[0])
        raise


def is_assembly(accession):
    """
        Returns True if assembly accession and FALSE if run accession.
    :param accession:
    :return:
    """
    if re.match(assembly_accession_re, accession):
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


def sanitise_fields(data):
    # Remove blank fields
    keys = list(data.keys())
    for k in keys:
        if type(data[k]) == str and len(data[k]) == 0:
            del data[k]

    return data


def get_accession_from_result_dir_path(result_dir_path):
    return (re.findall(run_accession_re, result_dir_path) or re.findall(assembly_accession_re, result_dir_path))[0]


def get_study_accession_from_rootpath(rootpath):
    return re.findall(study_accssion_re, rootpath)[0]


def get_study_dir(rootpath):
    split_path = rootpath
    while not is_study_accession(os.path.basename(split_path)):
        split_path = os.path.abspath(os.path.join(split_path, os.pardir))
        if len(split_path) < 9:
            raise ValueError(f'Could not retrieve study dir from {rootpath}')
    return split_path


def get_pipeline_version(rootpath):
    return re.findall(r'version_(\d+\.\d+)', rootpath)[0]


def sanitise_string(s):
    return unicodedata.normalize('NFKD', s)


def read_chunkfile(filename):
    with open(filename) as f:
        return [l.strip() for l in f.readlines()]


def get_study_summary_dir(study_dir):
    return os.path.join(study_dir, 'project-summary')


class DownloadFileDatabaseHandler:
    def __init__(self, emg_db_name):
        self.emg_db_name = emg_db_name

    @staticmethod
    def check_file_exists(path):
        filepath = os.path.join(*path)
        if not (os.path.exists(filepath) or os.path.isfile(filepath)):
            raise ValueError('{} does not exist and cannot be uploaded'.format(filepath))

    def save_study_download_file(self, study_download, study):
        try:
            path = [study_download.rootpath, study_download.subdir, study_download.realname]
            self.check_file_exists(path)
        except ValueError:
            if study_download.required:
                raise
            return
        defaults = {
            'description': self.get_download_label(study_download.desc_label),
            'group_type': self.get_download_group(study_download.group_type),
            'subdir': self.get_download_subdir(study_download.subdir),
            'file_format': self.get_file_format(study_download.file_format, study_download.compression)
        }
        pipeline_release = self.get_pipeline_release(study_download.pipeline)
        dl, _ = emg_models.StudyDownload.objects \
            .using(self.emg_db_name) \
            .update_or_create(study=study,
                              pipeline=pipeline_release,
                              alias=study_download.alias,
                              realname=study_download.realname,
                              defaults=defaults)
        return dl

    def save_download_file(self, download_file, analysis_job):
        try:
            if download_file.sub_dir:
                path = [download_file.result_dir, *os.path.split(download_file.sub_dir), download_file.realname]
            else:
                path = [download_file.result_dir, download_file.realname]
            self.check_file_exists(path)
        except ValueError:
            if download_file.required:
                raise
            return
        defaults = {
            'description': self.get_download_label(download_file.description_label),
            'group_type': self.get_download_group(download_file.group_type),
            'subdir': self.get_download_subdir(download_file.sub_dir),
            'file_format': self.get_file_format(download_file.file_format, download_file.compression)
        }
        dl, _ = emg_models.AnalysisJobDownload.objects \
            .using(self.emg_db_name) \
            .update_or_create(job=analysis_job,
                              pipeline=analysis_job.pipeline,
                              alias=download_file.alias,
                              realname=download_file.realname,
                              defaults=defaults)
        return dl

    def save_chunked_files(self, chunked_files, analysis_job):
        parent_dl = None
        if chunked_files.parent_file:
            parent_dl = self.save_download_file(chunked_files.parent_file, analysis_job)

        for chunked_file in chunked_files.chunked_files:
            child_dl = self.save_download_file(chunked_file, analysis_job)
            if parent_dl:
                child_dl.parent_id = parent_dl
                child_dl.save(using=self.emg_db_name)

    def get_download_group(self, group_type):
        try:
            return emg_models.DownloadGroupType.objects.using(self.emg_db_name).get(group_type=group_type)
        except emg_models.DownloadGroupType.DoesNotExist:
            raise emg_models.DownloadGroupType.DoesNotExist('Group type "{}" not found in db'.format(group_type))

    def get_download_label(self, desc_label):
        try:
            return emg_models.DownloadDescriptionLabel.objects.using(self.emg_db_name).get(
                description_label=desc_label)
        except emg_models.DownloadDescriptionLabel.DoesNotExist:
            raise emg_models.DownloadDescriptionLabel.DoesNotExist(
                'Download label "{}" not found in db'.format(desc_label))

    def get_pipeline_release(self, release_version):
        try:
            return emg_models.Pipeline.objects.using(self.emg_db_name).get(
                release_version=release_version)
        except emg_models.Pipeline.DoesNotExist:
            raise emg_models.Pipeline.DoesNotExist(
                'Pipeline release "{}" not found in db'.format(release_version))

    def get_download_subdir(self, subdir_name):
        if not subdir_name:
            return None
        try:
            return emg_models.DownloadSubdir.objects.using(self.emg_db_name).get(subdir=subdir_name)
        except emg_models.DownloadSubdir.DoesNotExist:
            raise emg_models.DownloadSubdir.DoesNotExist('Download subdir "{}" not found in db'.format(subdir_name))

    def get_file_format(self, format_name, compression):
        try:
            return emg_models.FileFormat.objects.using(self.emg_db_name).get(
                format_name=format_name,
                compression=compression)
        except emg_models.FileFormat.DoesNotExist:
            raise emg_models.FileFormat.DoesNotExist(
                'File format "{}" with compression {} not found in db'.format(format_name, compression))


class StudyDownload:
    def __init__(self, rootpath, file_config, pipeline):
        self.rootpath = rootpath
        self.pipeline = pipeline
        self.alias = file_config['alias']
        self.realname = file_config['real_name']
        self.subdir = file_config['subdir']
        self.required = file_config['_required']
        self.desc_label = file_config['description_label']
        self.group_type = file_config['group_type']
        self.compression = file_config['compression']
        self.file_format = file_config['format_name']


class DownloadSet:
    def __init__(self, rootpath, input_file_name, emg_db_name, config_file):
        self.rootpath = rootpath
        self.emg_db_name = emg_db_name
        self.input_file_name = input_file_name
        self.config = config_file

    def insert_files(self, analysis_job):
        for f in self.config:
            if f['downloadable']:
                if f['_chunked']:
                    self.insert_chunked_file(f, analysis_job)
                else:
                    self.insert_file(f, analysis_job)

    def insert_file(self, config, analysis_job):
        f = UnchunkedDownloadFile(config, self.rootpath, self.input_file_name)
        DownloadFileDatabaseHandler(self.emg_db_name).save_download_file(f, analysis_job)

    def insert_chunked_file(self, config, analysis_job):
        f = ChunkedDownloadFiles(config, self.rootpath, self.input_file_name)
        DownloadFileDatabaseHandler(self.emg_db_name).save_chunked_files(f, analysis_job)


def get_conf_downloadset(rootpath, input_file_name, emg_db_name, library_strategy, version, result_status=None):
    accession = input_file_name.split('_')[0]
    result_status = result_status or sanity.get_result_status(emg_db_name, accession)
    config = get_downloadset_config(version, library_strategy, result_status)
    #SSU.fasta and LSU.fasta could still be present. Do not upload for no_tax
    if result_status == 'no_tax':
        tax_fasta = ['Contigs encoding SSU rRNA', 'Contigs encoding LSU rRNA']
        filtered_config = [f for f in config if f['description_label'] not in tax_fasta]
    else:
        filtered_config = config
    return DownloadSet(rootpath, input_file_name, emg_db_name, filtered_config)


def get_result_dir(result_dir, substring="results/"):
    """
    :param result_dir:
    :param substring:
    :return:
    """
    pos = result_dir.find(substring)
    return result_dir[pos + len(substring):]


def read_backlog_config(config_path, db):
    BACKLOG_CONFIG = yamjam(config_path)
    backlog_config = BACKLOG_CONFIG.get('databases', {}).get(db)
    if not backlog_config:
        raise Exception(f"Could not find Backlog Config for db={db} in {config_path}")
    return {
        'raise_on_warnings': True,
        'autocommit': True,
        'database': backlog_config['NAME'],
        'port': backlog_config['PORT'],
        'host': backlog_config['HOST'],
        'user': backlog_config['USER'],
        'password': backlog_config['PASSWORD'],
    }


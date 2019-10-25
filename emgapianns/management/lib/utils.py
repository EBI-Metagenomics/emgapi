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
import pathlib
import re
import sys
import unicodedata

from emgapi import models as emg_models
from emgapianns.management.lib.import_analysis_model import Assembly, Run
from emgapianns.management.lib.uploader_exceptions import \
    AccessionNotRecognised
from emgapianns.management.webuploader_configs import get_downloadset_config

study_accssion_re = r'([ESD]RP\d{6,})'
run_accession_re = r'([ESD]RR\d{6,})'
assembly_accession_re = r'(ERZ\d{6,})'


def is_study_accession(accession):
    return re.match(study_accssion_re, accession)


def is_run_accession(accession):
    return re.match(run_accession_re, accession)


def is_assembly_accession(accession):
    return re.match(assembly_accession_re, accession)


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
        library_source = raw_metadata['library_source']
        # Convert library_strategy string to ExperimentType Enum
        return Run(study_accession, sample_accession, run_accession, library_strategy, library_source)
    except KeyError as err:
        print("Could NOT retrieve all run metadata need from ENA's API: {0}".format(err))
        raise
    except: # noqa
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
    except: # noqa
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
            raise ValueError('Could not retrieve study dir from {}'.format(rootpath))

    return split_path


def get_pipeline_version(rootpath):
    return re.findall(r'version_(\d+\.\d+)', rootpath)[0]


def sanitise_string(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')


def read_chunkfile(filename):
    with open(filename) as f:
        return [l.strip() for l in f.readlines()]


def get_study_summary_dir(study_dir):
    return os.path.join(study_dir, 'project-summary-tmp')


class Download:
    def __init__(self, emg_db_name, rootpath, input_file_name, file_config):
        if file_config['_accession_substitution'] == 'accession':
            input_file_name = input_file_name.split('_').pop(0)
        self.emg_db_name = emg_db_name
        self.rootpath = rootpath
        self.file_config = file_config
        self.alias = file_config['alias'].format(input_file_name)

        realname = file_config['real_name']
        self.realname = realname.format(input_file_name) if '{}' in realname else realname

        self.file_format = ''.join(pathlib.Path(realname).suffixes)

    def check_file_exists(self, path):
        filepath = os.path.join(*path)
        if not (os.path.exists(filepath) or os.path.isfile(filepath)):
            raise ValueError('{} does not exist and cannot be uploaded'.format(filepath))

    def save(self, analysis_job):
        return self._save(self.alias, self.realname, analysis_job)

    def _save(self, alias, realname, analysis_job):
        try:
            if self.file_config['subdir']:
                path = [self.rootpath, *os.path.split(self.file_config['subdir']), realname]
            else:
                path = [self.rootpath, realname]
            self.check_file_exists(path)
        except ValueError:
            if self.file_config['_required']:
                raise
            return
        defaults = {
            'description': self.get_download_label(),
            'group_type': self.get_download_group(),
            'subdir': self.get_download_subdir(),
            'file_format': self.get_file_format()
        }
        dl, _ = emg_models.AnalysisJobDownload.objects \
            .using(self.emg_db_name) \
            .update_or_create(job=analysis_job,
                              pipeline=analysis_job.pipeline,
                              alias=alias,
                              realname=realname,
                              defaults=defaults)
        return dl

    def get_download_group(self):
        group_type = self.file_config['group_type']
        try:
            return emg_models.DownloadGroupType.objects.using(self.emg_db_name).get(group_type=group_type)
        except emg_models.DownloadGroupType.DoesNotExist:
            raise emg_models.DownloadGroupType.DoesNotExist('Group type "{}" not found in db'.format(group_type))

    def get_download_label(self):
        desc_label = self.file_config['description_label']
        try:
            return emg_models.DownloadDescriptionLabel.objects.using(self.emg_db_name).get(
                description_label=desc_label)
        except emg_models.DownloadDescriptionLabel.DoesNotExist:
            raise emg_models.DownloadDescriptionLabel.DoesNotExist(
                'Download label "{}" not found in db'.format(desc_label))

    def get_download_subdir(self):
        subdir_name = self.file_config['subdir']
        if not subdir_name:
            return None
        try:
            return emg_models.DownloadSubdir.objects.using(self.emg_db_name).get(subdir=subdir_name)
        except emg_models.DownloadSubdir.DoesNotExist:
            raise emg_models.DownloadSubdir.DoesNotExist('Download subdir "{}" not found in db'.format(subdir_name))

    def get_file_format(self):
        try:
            return emg_models.FileFormat.objects.using(self.emg_db_name).get(
                format_name=self.file_config['format_name'],
                compression=self.file_config['compression'])
        except emg_models.FileFormat.DoesNotExist:
            raise emg_models.FileFormat.DoesNotExist(
                'File format "{}" with compression {} not found in db'.format(self.file_config['format_name'],
                                                                              self.file_config['compression']))


class StudyDownload(Download):
    def __init__(self, emg_db_name, rootpath, file_config, pipeline):
        self.emg_db_name = emg_db_name
        self.rootpath = rootpath
        self.file_config = file_config
        self.pipeline = pipeline

    def save(self, study):
        alias = self.file_config['alias']
        realname = self.file_config['real_name']
        self._save(alias, realname, study)

    def _save(self, alias, realname, study):
        try:
            path = [self.rootpath, os.pardir, self.file_config['subdir'], realname]
            self.check_file_exists(path)
        except ValueError:
            if self.file_config['_required']:
                raise
            return
        defaults = {
            'description': self.get_download_label(),
            'group_type': self.get_download_group(),
            'subdir': self.get_download_subdir(),
            'file_format': self.get_file_format()
        }
        dl, _ = emg_models.StudyDownload.objects \
            .using(self.emg_db_name) \
            .update_or_create(study=study,
                              pipeline=self.pipeline,
                              alias=alias,
                              realname=realname,
                              defaults=defaults)
        return dl


class ChunkedDownload(Download):
    def __init__(self, emg_db_name, rootpath, input_file_name, file_config):
        if file_config['_accession_substitution'] == 'accession':
            input_file_name = input_file_name.split('_').pop(0)
        self.emg_db_name = emg_db_name
        self.rootpath = rootpath
        self.file_config = file_config
        self.input_file_name = input_file_name
        self.exists = False

        chunk_filename = file_config['chunk_file']
        if '{}' in chunk_filename:
            chunk_filename = chunk_filename.format(input_file_name)

        chunk_filepath = os.path.join(self.rootpath, file_config['subdir'] or '', chunk_filename)
        if os.path.exists(chunk_filepath):
            self.exists = True
            self.chunks = read_chunkfile(chunk_filepath)
            if len(self.chunks) == 1:
                self.alias = file_config['alias'].format(input_file_name)
            self.file_format = ''.join(pathlib.Path(chunk_filename).suffixes)  # todo use config

    def save(self, analysis_job):
        if len(self.chunks) == 1:
            realname = self.chunks[0]
            realname = realname.format(self.input_file_name) if '{}' in realname else realname
            super()._save(self.alias, realname, analysis_job)
        else:
            parent_dl = self.save_parent_download(self.chunks.pop(0), analysis_job)
            for i, realname in enumerate(self.chunks):
                alias = self.get_chunk_name(i + 1)
                child_dl = super()._save(alias, realname, analysis_job)
                child_dl.parent_id = parent_dl
                child_dl.save(using=self.emg_db_name)

    def save_parent_download(self, realname, analysis_job):
        alias = self.get_chunk_name(1)
        return super()._save(alias, realname, analysis_job)

    def get_chunk_name(self, file_num):
        fmt_name = self.file_config['real_name'].format(self.input_file_name)
        name_path = pathlib.Path(fmt_name)
        return name_path.stem + '_' + str(file_num) + name_path.suffix


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

    def insert_file(self, f, analysis_job):
        f = Download(self.emg_db_name, self.rootpath, self.input_file_name, f)
        f.save(analysis_job)

    def insert_chunked_file(self, f, analysis_job):
        f = ChunkedDownload(self.emg_db_name, self.rootpath, self.input_file_name, f)
        if f.exists:
            f.save(analysis_job)


def get_conf_downloadset(rootpath, input_file_name, emg_db_name, experiment_type, version):
    config = get_downloadset_config(version, experiment_type)
    return DownloadSet(rootpath, input_file_name, emg_db_name, config)


def get_result_dir(result_dir, substring="results/"):
    """

    :param result_dir:
    :param substring:
    :return:
    """
    pos = result_dir.find(substring)
    return result_dir[pos + len(substring):]

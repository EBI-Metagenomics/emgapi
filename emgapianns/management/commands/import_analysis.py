#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getpass
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
import subprocess
import sys

from django.core.management import BaseCommand, call_command
from django.utils import timezone
from ena_portal_api import ena_handler

from emgapi import models as emg_models
from emgapianns.management.lib import utils
from emgapianns.management.lib.import_analysis_model import Assembly, Run, ExperimentType
from emgapianns.management.lib.sanity_check import SanityCheck
from emgapianns.management.lib.uploader_exceptions import QCNotPassedException, CoverageCheckException, FindResultFolderException
from emgapianns.management.lib.utils import get_conf_downloadset

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}

ena = ena_handler.EnaApiHandler()

"""
    Cl call:
        emgcli import_analysis <accession> 'root:Environmental:Aquatic:Marine' --pipeline 5.0
"""


class Command(BaseCommand):
    help = 'Imports new run and assembly annotation objects into EMG. The tool will import all associated objects like' \
           'studies, samples and assemblies as well. It will also populate MongoDB.'

    obj_list = list()
    rootpath = None
    nfs_public_rootpath = None

    emg_db = None
    biome = None
    accession = None
    version = None
    result_dir = None
    library_strategy = None

    def add_arguments(self, parser):
        parser.add_argument('--rootpath',
                            help="NFS root path of the results archive.",
                            default="/nfs/production/interpro/metagenomics/results/")
        parser.add_argument('--nfs-public-rootpath',
                            help="NFS public root path of the results archive.",
                            default="/nfs/public/ro/metagenomics/results/")
        parser.add_argument('accession', help="Specify run or assembly/analysis accession.")
        parser.add_argument('biome', help='Lineage of GOLD biome')
        parser.add_argument('library_strategy',
                            help='Library strategy',
                            choices=['AMPLICON', 'WGS', 'ASSEMBLY', 'RNA-Seq'])
        parser.add_argument('--pipeline', help='Pipeline version',
                            choices=['4.1', '5.0'], default='4.1')
        parser.add_argument('--database',
                            help='Target emg_db_name alias',
                            choices=['default', 'dev', 'prod'],
                            default='default')

    def handle(self, *args, **options):
        self.emg_db = options['database']
        self.rootpath = os.path.abspath(options['rootpath'])
        self.nfs_public_rootpath = os.path.abspath(options['nfs_public_rootpath'])
        self.accession = options['accession']
        self.biome = options['biome']
        self.library_strategy = options['library_strategy']
        self.version = options['pipeline']
        logger.info("CLI %r" % options)

        metadata = self.retrieve_metadata()
        secondary_study_accession = metadata.secondary_study_accession

        self.result_dir = self.__find_existing_result_dir(secondary_study_accession, self.accession, self.version)

        input_file_name = os.path.basename(self.result_dir)

        sanity_checker = SanityCheck(self.accession, self.result_dir, self.library_strategy, self.version)

        if not sanity_checker.passed_quality_control():
            raise QCNotPassedException("{} did not pass QC step!".format(self.accession))

        if not sanity_checker.passed_coverage_check():
            raise CoverageCheckException("{} did not pass QC step!".format(self.accession))

        study_dir = self.call_import_study(secondary_study_accession)

        self.call_import_sample(metadata)

        if isinstance(metadata, Run):
            self.call_import_run(metadata.run_accession)
        else:
            self.call_import_assembly(metadata.analysis_accession)

        analysis = self.create_or_update_analysis(metadata, input_file_name)
        self.upload_analysis_files(metadata.experiment_type.value, analysis, input_file_name)

        self.upload_statistics()

        self.populate_mongodb_taxonomy()

        if metadata.experiment_type != ExperimentType.AMPLICON:
            self.populate_mongodb_function_and_pathways()
        else:
            logging.info("Skipping the import of functional and pathway annotations!")

        if self.version in ['5.0'] and metadata.experiment_type == ExperimentType.ASSEMBLY:
            self.import_contigs()
        else:
            logging.info("Skipping the import procedure for the contig viewer!")

        self.__call_generate_study_summary(secondary_study_accession)
        self.__sync_study_summary_files(study_dir)

        logger.info("The upload of the run/assembly {} finished successfully.".format(self.accession))

    def __find_existing_result_dir(self, secondary_study_accession, run_accession, version):
        """

        :param run_accession:
        :param version:
        :return:
        """
        logging.info("Finding result directory...")
        directory = os.path.join(self.rootpath, '2019')
        study_folder = self.__find_folder(directory, search_pattern=secondary_study_accession, recursive=True)

        directory = os.path.join(study_folder, 'version_{}/'.format(version))
        result_folder = self.__find_folder(directory, search_pattern=run_accession, maxdepth=3)
        logging.info("Found the following result folder:\n{}".format(result_folder))
        return result_folder

    def call_import_study(self, secondary_study_accession):
        study_dir = utils.get_result_dir(utils.get_study_dir(self.result_dir))
        call_command('import_study',
                     secondary_study_accession,
                     self.biome,
                     '--study_dir', study_dir)
        return study_dir

    def call_import_sample(self, metadata):
        call_command('import_sample',
                     metadata.sample_accession,
                     '--biome', self.biome)

    def call_import_run(self, run_accession):
        call_command('import_run', run_accession, '--biome', self.biome)

    def call_import_assembly(self, analysis_accession):
        call_command('import_assembly', analysis_accession, '--result_dir', self.result_dir, '--biome', self.biome)

    def __call_generate_study_summary(self, secondary_study_accession):
        """
            Example call:
            ERP117125 4.1 --rootpath /home/maxim/software-projects/emgapi/tests/test-input/results --database default

        :param study_accession:
        :return:
        """
        logger.info('Generating study summary {}'.format(secondary_study_accession))
        call_command('import_study_summary', secondary_study_accession, self.version, '--database', self.emg_db,
                     '--rootpath', self.rootpath)

    def __sync_study_summary_files(self, study_dir):
        logging.info("Syncing project summary files over to NFS public...")
        nfs_prod_dest = os.path.join(self.rootpath, study_dir, 'version_{}/{}'.format(self.version, 'project-summary'))
        nfs_public_dest = os.path.join(self.nfs_public_rootpath, study_dir, 'version_{}/'.format(self.version))
        logging.info("From: " + nfs_prod_dest)
        logging.info("To: " + nfs_public_dest)

        rsync_options = ['-rtDzv']

        more_rsync_options = ['--no-owner', '--no-perms', '--prune-empty-dirs', '--exclude', '*.lsf',
                              '--delete-excluded', '--chmod=Do-w,Fu+x,Fg+x,Fo+r']
        rsync_cmd = ["sudo", "-H", "-u", "emg_adm", "rsync"] + rsync_options + more_rsync_options + [nfs_prod_dest,
                                                                                                     nfs_public_dest]

        subprocess.check_call(rsync_cmd)
        logging.info("Synchronisation is done.")

    def retrieve_metadata(self):
        """
            Please note: Overwrite library strategy. Use library strategy given as a program argument.
        :return:
        """
        logger.info("Retrieving metadata...")
        is_assembly = utils.is_assembly(self.accession)
        logger.info("Identified assembly accession: {0}".format(is_assembly))

        if is_assembly:
            # assembly = ena.get_assembly(assembly_name=self.accession)
            assembly = ena.get_assembly(assembly_name=self.accession,
                                        fields='secondary_study_accession,secondary_sample_accession,'
                                               'analysis_alias,analysis_accession')
            if 'sample_accession' in assembly:
                del assembly['sample_accession']
            if 'analysis_alias' in assembly:
                assembly['run_accession'] = assembly['analysis_alias']
                del assembly['analysis_alias']
            analysis = Assembly(**assembly)
        else:  # Run accession detected
            run = ena.get_run(run_accession=self.accession,
                              fields='secondary_study_accession,secondary_sample_accession,'
                                     'run_accession,library_strategy,library_source')
            # Overwrite library strategy.
            run['library_strategy'] = self.library_strategy
            if 'sample_accession' in run:
                del run['sample_accession']
            analysis = Run(**run)
        return analysis

    def get_emg_study(self, secondary_study_accession):
        return emg_models.Study.objects.using(self.emg_db).get(secondary_accession=secondary_study_accession)

    def get_emg_sample(self, sample_accession):
        return emg_models.Sample.objects.using(self.emg_db).get(accession=sample_accession)

    def get_emg_run(self, run_accession):
        return emg_models.Run.objects.using(self.emg_db).get(accession=run_accession)

    def get_emg_assembly(self, assembly_accession):
        return emg_models.Assembly.objects.using(self.emg_db).get(accession=assembly_accession)

    def get_pipeline_by_version(self):
        return emg_models.Pipeline.objects.using(self.emg_db).get(release_version=self.version)

    def get_analysis_status(self, description):
        return emg_models.AnalysisStatus.objects.using(self.emg_db).get(analysis_status=description)

    def get_experiment_type(self, experiment_typ):
        return emg_models.ExperimentType.objects.using(self.emg_db).get(experiment_type=experiment_typ)

    def create_or_update_analysis(self, metadata, input_file_name):
        logging.info("Creating/updating analysis jobs...")
        pipeline = self.get_pipeline_by_version()
        study = self.get_emg_study(metadata.secondary_study_accession)
        sample = self.get_emg_sample(metadata.sample_accession)

        defaults = {
            'study': study,
            'sample': sample,
            'result_directory': utils.get_result_dir(self.result_dir),
            're_run_count': 0,
            'input_file_name': input_file_name,
            # Removed due to (1406, "Data too long for column 'IS_PRODUCTION_RUN' at row 1")
            # 'is_production_run': 1,
            'analysis_status': self.get_analysis_status('completed'),
            'submit_time': timezone.now(),
            'complete_time': timezone.now(),
            'job_operator': getpass.getuser()
        }
        comp_key = {
            'pipeline': pipeline
        }

        if isinstance(metadata, Run):
            run = self.get_emg_run(metadata.run_accession)
            comp_key.update({
                'external_run_ids': run.accession,
                'run': run,
                'secondary_accession': run.accession
            })
            defaults['instrument_model'] = run.instrument_model
            defaults['instrument_platform'] = run.instrument_platform
            defaults['experiment_type'] = run.experiment_type
            defaults['run_status_id'] = run.status_id
        else:
            run = self.get_emg_run(metadata.run_accession)
            assembly = self.get_emg_assembly(metadata.analysis_accession)
            comp_key.update({
                'external_run_ids': assembly.accession,
                'assembly': assembly,
            })
            defaults['experiment_type'] = self.get_experiment_type('assembly')
            defaults['instrument_model'] = run.instrument_model
            defaults['instrument_platform'] = run.instrument_platform
            defaults['run_status_id'] = run.status_id
        analysis, _ = emg_models.AnalysisJob.objects.using(self.emg_db) \
            .update_or_create(**comp_key, defaults=defaults)
        logging.info("Analysis job successfully created.")
        return analysis

    def upload_analysis_files(self, experiment_type, analysis_job, input_file_name):
        logging.info("Creating downloadable files...")
        dl_set = get_conf_downloadset(self.result_dir, input_file_name,
                                      self.emg_db, experiment_type, self.version)
        dl_set.insert_files(analysis_job)
        logging.info("Downloadable files successfully created.")

    def upload_statistics(self):
        """
            Please note that the name of the import module is misleading as this is not just about QC stats but also
            about functional stats
        :return:
        """
        logger.info('Importing statistics...')
        call_command('import_qc', self.accession, self.rootpath, '--pipeline', self.version)
        logger.info('Stats successfully imported.')

    def populate_mongodb_taxonomy(self):
        logger.info('Importing Taxonomy data...')
        call_command('import_taxonomy', self.accession, self.rootpath, '--pipeline', self.version)
        logger.info('Taxonomy data successfully imported.')

    def populate_mongodb_function_and_pathways(self):
        logger.info('Importing functional and pathway data...')
        for sum_type in ['.ipr', '.go', '.go_slim', '.paths.kegg', '.pfam', '.ko', '.paths.gprops', '.antismash']:
            call_command('import_summary', self.accession, self.rootpath, sum_type, '--pipeline', self.version)

    def import_contigs(self):
        logger.info('Importing contigs...')
        call_command('import_contigs', self.accession, '--pipeline', self.version, '--faix')

    def __find_folder(self, directory, search_pattern, maxdepth=2, recursive=False):
        """

        :param dest_pattern:
        :return: e.g. 2017/11/ERP104174/
        """
        study_folder = self.__call_find(directory, "{}*".format(search_pattern), maxdepth)

        if study_folder:
            if len(study_folder) > 1:
                sys.exit(f'Found more than 1 result directory: {study_folder}')
            else:
                logging.info(f'Found result dir: {study_folder}')
                return study_folder[0]

        elif recursive:
            self.__find_folder(self.rootpath, search_pattern, maxdepth=3)
        else:
            sys.exit('Could not find result directory for: {}'.format(search_pattern))

    @staticmethod
    def __call_find(directory, name, maxdepth=2):
        """

        :param dest_pattern:
        :return: e.g. 2017/11/ERP104174/
        """
        try:
            find_cmd = ["find", directory, "-maxdepth", str(maxdepth), "-name", name, "-type", "d"]
            logging.debug("Calling;\n{}".format(find_cmd))
            stdout = subprocess.check_output(find_cmd)

            stdout = stdout.decode('utf-8').rstrip("\n\r")
            return stdout.splitlines()
        except subprocess.CalledProcessError:
            raise FindResultFolderException
        except UnicodeError:
            raise FindResultFolderException

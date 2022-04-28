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

import logging
import os
import re
import subprocess
import sys
import getpass

from django.core.management import BaseCommand, call_command
from django.utils import timezone
from django.conf import settings
from ena_portal_api import ena_handler

from emgapi import models as emg_models
from emgapianns.management.lib import utils
from emgapianns.management.lib.import_analysis_model import Assembly, Run, ExperimentType
from emgapianns.management.lib.sanity_check import SanityCheck
from emgapianns.management.lib.uploader_exceptions import QCNotPassedException, CoverageCheckException, \
    FindResultFolderException
from emgapianns.management.lib.utils import get_conf_downloadset

logger = logging.getLogger(__name__)

ena = ena_handler.EnaApiHandler()

"""
    Cl call:
        emgcli import_analysis <accession> 'root:Environmental:Aquatic:Marine' --pipeline 5.0
"""


def setup_logging(options):
    verbosity = options.get('verbosity', None)
    log_level = logging.WARN
    if verbosity:
        if verbosity > 1:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
    logging.basicConfig(format='%(levelname)s %(asctime)s - %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p',
                        level=log_level)


class Command(BaseCommand):
    help = 'Imports new run and assembly annotation objects into EMG. The tool will import all associated objects like' \
           'studies, samples and assemblies as well. It will also populate MongoDB.'

    obj_list = list()
    rootpath = None

    emg_db = None
    biome = None
    accession = None
    version = None
    result_dir = None
    library_strategy = None
    force_study_summary = False

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--rootpath',
                            help="NFS production root path of the results archive.",
                            default=settings.RESULTS_PRODUCTION_DIR)
        parser.add_argument('accession', help="Specify run or assembly/analysis accession.")
        parser.add_argument('biome', help='Lineage of GOLD biome')
        parser.add_argument('library_strategy',
                            help='Library strategy',
                            choices=['AMPLICON', 'WGS', 'ASSEMBLY', 'RNA-Seq', 'WGA'])
        parser.add_argument('--pipeline', help='Pipeline version',
                            choices=['4.1', '5.0'], default='5.0')
        parser.add_argument('--database',
                            help='Target emg_db_name alias',
                            choices=['default', 'dev', 'prod'],
                            default='default')
        parser.add_argument('--force-study-summary', dest='force_study_summary', action='store_true', default=False)

    def handle(self, *args, **options):
        setup_logging(options)
        self.emg_db = options['database']

        if not options['rootpath']:
            raise ValueError("rootpath (RESULTS_PRODUCTION_DIR setting) cannot by empty)")

        self.rootpath = os.path.abspath(options['rootpath'])
        self.accession = options['accession']
        self.biome = options['biome']
        self.library_strategy = options['library_strategy']
        self.version = options['pipeline']
        self.force_study_summary = options['force_study_summary']
        logger.info("CLI %r" % options)

        metadata = self.retrieve_metadata()
        secondary_study_accession = metadata.secondary_study_accession

        self.result_dir = self.__find_existing_result_dir(secondary_study_accession, self.accession, self.version)

        input_file_name = os.path.basename(self.result_dir)

        sanity_checker = SanityCheck(self.accession, self.result_dir, self.library_strategy, self.version, emg_db=self.emg_db)
        sanity_checker.check_file_existence()

        sanity_checker.run_quality_control_check()

        sanity_checker.run_coverage_check()

        study_dir = utils.get_result_dir(utils.get_study_dir(self.result_dir))

        call_command('import_study',
                     secondary_study_accession,
                     self.biome,
                     '--study_dir', study_dir)

        call_command('import_sample',
                     metadata.sample_accession,
                     '--biome', self.biome)

        if isinstance(metadata, Run):
            call_command('import_run', metadata.run_accession, '--biome', self.biome, '--library_strategy', self.library_strategy)
        else:
            call_command('import_assembly', metadata.analysis_accession, '--biome', self.biome)

        analysis = self.create_or_update_analysis(metadata, input_file_name)
        self.upload_analysis_files(self.library_strategy, analysis, input_file_name)

        self.upload_statistics()

        self.populate_mongodb_taxonomy()

        if metadata.experiment_type != ExperimentType.AMPLICON:
            self.populate_mongodb_function_and_pathways()
        else:
            logging.info("Skipping the import of functional and pathway annotations!")

        if self.version in ['5.0'] and metadata.experiment_type == ExperimentType.ASSEMBLY:
            logger.info('Importing contigs...')
            call_command('import_contigs', self.accession, self.rootpath, '--pipeline', self.version)
        else:
            logging.info("Skipping the import procedure for the contig viewer!")

        if self.force_study_summary:
            self.__call_generate_study_summary(secondary_study_accession)

        logger.info("The upload of the run/assembly {} finished successfully.".format(self.accession))

    def __find_existing_result_dir(self, secondary_study_accession, run_accession, version):
        """Find the results folder 
        """
        logging.info("Finding result directory...")
        # FIXME: remove hardcoded value.
        directory = os.path.join(self.rootpath, '2022')
        study_folder = self.__find_folder(directory, search_pattern=secondary_study_accession, recursive=True)

        # find version_{} folder
        result_folder = []
        if len(study_folder) == 0:
            # TODO: replace with raise CommandError
            sys.exit('Could not find result directory for: {}'.format(secondary_study_accession))
        for cur_study_folder in study_folder:
            directory = os.path.join(cur_study_folder, 'version_{}/'.format(version))
            result_folder += self.__find_folder(directory, search_pattern=run_accession, maxdepth=3)

        # if len(result_folder) > 1: take the latest created version_{} folder
        if len(result_folder) == 0:
            # TODO: replace with raise CommandError
            sys.exit('Could not find result directory for: {}'.format(run_accession))
        else:
            latest_folder = max(result_folder, key=os.path.getctime)
            logging.info("Found the following result folder:\n{}".format(latest_folder))
            return latest_folder

    def __call_generate_study_summary(self, secondary_study_accession):
        """
            Example call:
            ERP117125 4.1 --rootpath /home/maxim/software-projects/emgapi/tests/test-input/results --database default

        :param study_accession:
        :return:
        """
        logger.info('Generating study summary {}'.format(secondary_study_accession))
        call_command('create_study_summary', secondary_study_accession, self.version, '--database', self.emg_db,
                     '--rootpath', self.rootpath)

    def retrieve_metadata(self):
        """
        Please note: Overwrite library strategy. Use library strategy given as a program argument.
        :return:
        """
        logger.info("Retrieving metadata...")
        is_assembly = utils.is_assembly(self.accession)
        logger.info("Identified assembly accession: {0}".format(is_assembly))

        if is_assembly:
            assembly_fields = ",".join([
                "secondary_study_accession",
                "secondary_sample_accession",
                "analysis_alias",
                "analysis_accession",
                # the following fields are not
                # currently in use but I left them there
                # because they could be useful in the future
                "sequencing_method",
                "assembly_software",
                "assembly_quality",
                "description"
            ])
            assembly = ena.get_assembly(assembly_name=self.accession, fields=assembly_fields)
            if 'sample_accession' in assembly:
                del assembly['sample_accession']
            # Try to parse out the run accession from the analysis alias
            # This generally works for most MGnify produced assemblies
            # Please note: external assemblies might not have this!
            if 'analysis_alias' in assembly:
                pattern = re.compile(r'([EDS]RR\d{6,})')
                search_string = assembly['analysis_alias']
                match = re.search(pattern, search_string)
                if match:
                    if len(match.groups()) > 0:
                        run_accession = match.group(1)
                    else:
                        run_accession = assembly['analysis_alias']
                    assembly['run_accession'] = run_accession
                else:
                    assembly['run_accession'] = None
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
            defaults['run_status_id'] = run.status_id.pk
        else:
            assembly = self.get_emg_assembly(metadata.analysis_accession)
            comp_key.update({
                'external_run_ids': assembly.accession,
                'assembly': assembly,
            })
            defaults['experiment_type'] = self.get_experiment_type('assembly')
            # TODO: run_status_id should be renamed to status_id
            defaults['run_status_id'] = assembly.status_id.pk
            if metadata.run_accession:
                run = self.get_emg_run(metadata.run_accession)
                defaults['instrument_model'] = run.instrument_model
                defaults['instrument_platform'] = run.instrument_platform

        analysis, _ = emg_models.AnalysisJob.objects.using(self.emg_db) \
            .update_or_create(**comp_key, defaults=defaults)
        logging.info("Analysis job successfully created.")
        return analysis

    def upload_analysis_files(self, library_strategy, analysis_job, input_file_name):
        logging.info("Creating downloadable files...")
        dl_set = get_conf_downloadset(self.result_dir, input_file_name,
                                      self.emg_db, library_strategy, self.version)
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
        for sum_type in ['.ips', '.ipr', '.go', '.go_slim', '.pfam', '.ko', '.gprops', '.antismash', '.kegg_pathways']:
            call_command('import_summary', self.accession, self.rootpath, sum_type, '--pipeline', self.version)

    def __find_folder(self, directory, search_pattern, maxdepth=2, recursive=False):
        """
        Find a folder.
        :param dest_pattern:
        :return: e.g. 2017/11/ERP104174/
        """
        study_folder = self.__call_find(directory, "{}*".format(search_pattern), maxdepth)
        #omit any assembly result folders
        study_folder = [x for x in study_folder if 'assemblies' not in x]

        if study_folder:
            if len(study_folder) > 1:
                logging.info(f'Found more than 1 result directory: {study_folder}')
            else:
                logging.info(f'Found result dir: {study_folder}')
            return study_folder

        elif recursive:
            return self.__find_folder(self.rootpath, search_pattern, maxdepth=3)
        else:
            logging.info('Could not find result directory for: {}'.format(search_pattern))
            return []

    @staticmethod
    def __call_find(directory, name, maxdepth=2):
        """
        Call the find unix tool
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
            return []  #  raise FindResultFolderException
        except UnicodeError:
            raise FindResultFolderException

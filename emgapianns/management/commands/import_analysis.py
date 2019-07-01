import logging
import os

from django.core.management import BaseCommand

from emgapi import models as emg_models

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}


class Command(BaseCommand):
    obj_list = list()
    rootpath = None
    genome_folders = None

    database = None

    def add_arguments(self, parser):
        parser.add_argument('rootpath', action='store', type=str, )
        # parser.add_argument('--update', action='store_true')
        parser.add_argument('--database', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.rootpath = os.path.realpath(options.get('rootpath').strip())
        if not os.path.exists(self.rootpath):
            raise FileNotFoundError('Results dir {} does not exist'
                                    .format(self.rootpath))
        self.database = options['database']
        logger.info("CLI %r" % options)

        raw_accession = self.get_accession()

        raw_metadata = self.get_raw_metadata()

        self.sanity_check_dir(raw_metadata)

        study_accession = raw_metadata['secondary_study_accession']

        study = self.get_or_create_study(study_accession)

        publication = self.get_or_create_publication()
        self.link_study_publication(study, publication)

        sample = self.get_or_create_sample(raw_metadata['sample_accession'])
        self.link_study_sample(study, sample)

        analysis = self.get_or_create_analysis(raw_metadata)

        if self.is_run(raw_metadata):
            run = self.get_or_create_run(raw_metadata)
            self.link_run_sample(run, sample)
            self.link_analysis_run(analysis, run)
        elif self.is_assembly(raw_metadata):
            assembly = self.get_or_create_assembly(raw_metadata)
            self.link_assembly_sample(assembly, sample)
            self.link_analysis_assembly(analysis, assembly)
        else:
            raise ValueError(
                'Could not determine if object is run or assembly from accession.')

        # TODO if assembly is linked to run create RunAssembly object

        self.load_api_files(raw_accession, self.rootpath)

    def sanity_check_dir(self):
        pass

    def get_accession(self):
        pass
        # TODO get accession from directory path

    def get_raw_metadata(self):
        pass
        # TODO get metadata of raw data
        # TODO MAIN WORKFLOW

    def get_or_create_study(self, study_accession):
        pass

    def get_or_create_publication(self):
        pass

    def link_study_publication(self, study, publication):
        pass

    def get_or_create_sample(self):
        pass

    def get_or_create_run(self, raw_metadata):
        pass

    def link_study_sample(self, study, sample):
        pass

    def link_run_sample(self, run, sample):
        pass

    def link_analysis_run(self, analysis, run):
        pass

    def link_analysis_assembly(self, analysis, assembly):
        pass

    def link_assembly_sample(self, assembly, sample):
        pass

    def get_or_create_analysis(self, raw_metadata):
        pass

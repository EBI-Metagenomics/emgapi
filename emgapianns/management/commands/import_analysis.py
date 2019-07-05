import logging
import os
from glob import glob
from django.core.management import BaseCommand

logger = logging.getLogger(__name__)

cog_cache = {}
ipr_cache = {}
kegg_cache = {}

"""
    Cl call:
        emgcli import_analysis <primary_accession> /home/maxim/
    Draft
    Inputs:
        - Accessions: Study, Sample and (run or assembly)
        - Path to the result directory
"""


class Importer:

    def __init__(self, rootpath, accession):
        self.rootpath = os.path.realpath(rootpath).strip()
        self.accession = accession
        self.existence_check()

    def existence_check(self):
        if not os.path.exists(self.rootpath):
            raise FileNotFoundError('Results dir {} does not exist'.format(self.rootpath))

    def sanity_check_dir(self):
        """
            Step 1: Search run/assembly result folder
            Step 2: Perform sanity check_all on result folder
        :return:
        """
        # Step 1
        self.retrieve_existing_result_dir()

        pass

    def retrieve_existing_result_dir(self):
        """
            Search file system for existing result folder
            TODO: Write unit test
        :param accession:
        :return:
        """
        dest_pattern = ['2*', '*', self.accession]
        prod_study_dir = os.path.join(self.rootpath, *dest_pattern)

        existing_result_dir = [d.replace(self.prod_dir, '') for d in glob.glob(prod_study_dir)]
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


class Command(BaseCommand):
    help = 'Imports new objects into EMG.'

    obj_list = list()
    rootpath = None
    genome_folders = None

    database = None

    def add_arguments(self, parser):
        parser.add_argument('accession',
                            help='ENA primary accession for run or assembly',
                            type=str,
                            action='store')
        parser.add_argument('--prod_dir',
                            help="NFS root path of the results archive",
                            default='/nfs/production/interpro/metagenomics/results/')

        # parser.add_argument('--update', action='store_true')
        #  parser.add_argument('--database', type=str, default='default')

    def handle(self, *args, **options):
        importer = Importer(
            options.get('prod_dir'),
            options['accession']
        )

        logger.info("CLI %r" % options)

        raw_accession = importer.get_accession()

        raw_metadata = importer.get_raw_metadata()

        importer.sanity_check_dir()

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

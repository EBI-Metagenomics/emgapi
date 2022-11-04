import logging
import os
from pathlib import Path

from emgapi import models as emg_models

from django.core.management import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Imports a directory of GFFs that as 'extra assembly annotations', " \
           "i.e. annotations from tools that aren't part of the analysis pipelines."

    obj_list = list()
    results_directory = None
    gffs_dir = None
    tool = None

    def add_arguments(self, parser):
        parser.add_argument(
            'results_directory',
            action='store',
            type=str
        )
        parser.add_argument(
            'gffs_directory',
            action='store',
            type=str,
            help='The folder within `results_directory` where the GFF files are, e.g. "sanntis/"'
        )
        parser.add_argument(
            'tool',
            action='store',
            type=str,
            help='The type of annotation (e.g. sanntis)',
            choices=['sanntis']
        )

    def handle(self, *args, **options):
        logger.info(options)

        self.results_directory = os.path.realpath(options.get('results_directory').strip())

        if not os.path.exists(self.results_directory):
            raise FileNotFoundError(f'Results dir {self.results_directory} does not exist')

        gffs_directory = options['gffs_directory'].strip()
        self.gffs_dir = os.path.join(self.results_directory, gffs_directory)
        if not os.path.exists(self.gffs_dir):
            raise FileNotFoundError(f'GFFs dir {self.gffs_dir} does not exist')

        if options.get('tool') == 'sanntis':
            logger.info('Looking for SanntiS-style GFFs')
            for file in Path(self.gffs_dir).glob('**/*.gff'):
                logger.info(f'Handling GFF file {file}')
                erz = file.name.split('.')[0]
                try:
                    assembly = emg_models.Assembly.objects.get(accession=erz)
                except emg_models.Assembly.DoesNotExist:
                    logger.warning(f'No Assembly found for sanntis GFF {erz}')
                    continue
                logger.info(f'Will upload sanntis GFF for {erz}')
                self.upload_sanntis_gff_file(assembly, gffs_directory, file.name)

    def upload_sanntis_gff_file(
        self,
        assembly,
        subdir,
        filename,
    ):
        description_label, created = emg_models.DownloadDescriptionLabel \
            .objects \
            .get_or_create(description_label='SanntiS annotation', defaults={
                "description": "SMBGC Annotation using Neural Networks Trained on Interpro Signatures"
        })
        if created:
            logger.info(f'Added new download description label {description_label}')

        fmt = emg_models.FileFormat \
            .objects \
            .filter(format_extension='gff', compression=False) \
            .first()

        subdir_obj, created = emg_models.DownloadSubdir.objects.get_or_create(subdir=subdir)
        if created:
            logger.info(f'Added new downloads subdir {subdir_obj}')

        group = emg_models.DownloadGroupType.objects.get(
            group_type='Functional analysis'
        )

        alias = f'{assembly.accession}-sanntis.gff'

        defaults = {
            'alias': alias,
            'description': description_label,
            'file_format': fmt,
            'group_type': group,
            'realname': os.path.basename(filename),
            'subdir': subdir_obj
        }

        dl, created = emg_models.AssemblyExtraAnnotation.objects.update_or_create(
            defaults,
            assembly=assembly,
            alias=alias,
        )

        logger.info(f'{"Created" if created else "Updated"} download {dl}')
        return dl

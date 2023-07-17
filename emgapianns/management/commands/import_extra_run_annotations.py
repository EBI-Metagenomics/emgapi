import logging
import os
from pathlib import Path

from emgapi import models as emg_models

from django.core.management import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Imports a directory of GFFs that as 'extra run annotations', " \
           "i.e. annotations from tools that aren't part of the analysis pipelines." \
           "GFFs may (preferably) be wrapped into self-describing RO Crates."

    obj_list = list()
    results_directory = None
    gffs_dir = None
    tool = None

    fmt_cache = {}
    desc_label_cache = {}
    group_cache = {}
    subdir_cache = {}

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
            help='The folder within `results_directory` where the GFF/ROCrate files are, e.g. "crates/"'
        )
        parser.add_argument(
            'tool',
            action='store',
            type=str,
            help='The type of annotation (e.g. rocrate)',
            choices=['rocrate']
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

        # if options.get('tool') == 'sanntis':
        #     logger.info('Looking for SanntiS-style GFFs')
        #     for file in Path(self.gffs_dir).glob('**/*.gff'):
        #         logger.info(f'Handling GFF file {file}')
        #         erz = file.name.split('.')[0]
        #         try:
        #             run = emg_models.Run.objects.get(accession=erz)
        #         except emg_models.Run.DoesNotExist:
        #             logger.warning(f'No Run found for sanntis GFF {erz}')
        #             continue
        #         logger.info(f'Will upload sanntis GFF for {erz}')
        #         self.upload_sanntis_gff_file(run, gffs_directory, file.name)

        if options.get('tool') == 'rocrate':
            logger.info('Looking for RO Crates (.zips')
            for file in Path(self.gffs_dir).glob('**/*.zip'):
                logger.info(f'Handling RO Crate Zip file {file}')
                erz = 'ERZ' + file.name.split('ERZ')[1].strip('.zip')
                try:
                    run = emg_models.Run.objects.get(accession=erz)
                except emg_models.Run.DoesNotExist:
                    logger.warning(f'No Run found for RO Crate apparent ERZ {erz}')
                    continue
                logger.info(f'Will upload RO Crate for {erz}')
                self.upload_rocrate(run, gffs_directory, file.name)

    # def upload_sanntis_gff_file(
    #     self,
    #     run,
    #     subdir,
    #     filename,
    # ):
    #     description_label = self.desc_label_cache.get('SanntiS annotation')
    #     if not description_label:
    #         description_label, created = emg_models.DownloadDescriptionLabel \
    #             .objects \
    #             .get_or_create(description_label='SanntiS annotation', defaults={
    #                 "description": "SMBGC Annotation using Neural Networks Trained on Interpro Signatures"
    #             })
    #         if created:
    #             logger.info(f'Added new download description label {description_label}')
    #         self.desc_label_cache[description_label.description_label] = description_label
    #
    #     fmt = self.fmt_cache.setdefault(
    #         'gff',
    #         emg_models.FileFormat.objects
    #         .filter(format_extension='gff', compression=False)
    #         .first()
    #     )
    #
    #     subdir_obj = self.subdir_cache.get(subdir)
    #     if not subdir_obj:
    #         subdir_obj, created = emg_models.DownloadSubdir.objects.get_or_create(subdir=subdir)
    #         if created:
    #             logger.info(f'Added new downloads subdir {subdir_obj}')
    #         self.subdir_cache[subdir] = subdir_obj
    #
    #     group = self.group_cache.setdefault(
    #         'Functional analysis',
    #         emg_models.DownloadGroupType.objects.get(
    #             group_type='Functional analysis'
    #         )
    #     )
    #
    #     alias = f'{run.accession}-sanntis.gff'
    #
    #     defaults = {
    #         'alias': alias,
    #         'description': description_label,
    #         'file_format': fmt,
    #         'group_type': group,
    #         'realname': os.path.basename(filename),
    #         'subdir': subdir_obj
    #     }
    #
    #     dl, created = emg_models.RunExtraAnnotation.objects.update_or_create(
    #         defaults,
    #         run=run,
    #         alias=alias,
    #     )
    #
    #     logger.info(f'{"Created" if created else "Updated"} download {dl}')
    #     return dl

    def upload_rocrate(
        self,
        run,
        subdir,
        filename,
    ):
        description_label = self.desc_label_cache.get('Analysis RO Crate')
        if not description_label:
            description_label, created = emg_models.DownloadDescriptionLabel \
                .objects \
                .get_or_create(description_label='Analysis RO Crate', defaults={
                    "description": "Self-describing analysis workflow product packaged as RO Crate"
                })
            if created:
                logger.info(f'Added new download description label {description_label}')
            self.desc_label_cache[description_label.description_label] = description_label

        fmt = self.fmt_cache.get('RO Crate')
        if not fmt:
            fmt, created = emg_models.FileFormat \
                .objects \
                .get_or_create(format_name='RO Crate', defaults={
                    "format_extension": "zip",
                    "compression": True
                })
            if created:
                logger.info(f'Added new file format {fmt}')
            self.fmt_cache[fmt.format_name] = fmt

        subdir_obj = self.subdir_cache.get(subdir)
        if not subdir_obj:
            subdir_obj, created = emg_models.DownloadSubdir.objects.get_or_create(subdir=subdir)
            if created:
                logger.info(f'Added new downloads subdir {subdir_obj}')
            self.subdir_cache[subdir] = subdir_obj

        group = self.group_cache.get('Analysis RO Crate')
        if not group:
            group, created = emg_models.DownloadGroupType.objects.get_or_create(group_type='Analysis RO Crate')
            if created:
                logger.info(f'Added new download group type {group}')
            self.group_cache[group.group_type] = group

        alias = os.path.basename(filename)

        defaults = {
            'alias': alias,
            'description': description_label,
            'file_format': fmt,
            'group_type': group,
            'realname': os.path.basename(filename),
            'subdir': subdir_obj
        }

        dl, created = emg_models.RunExtraAnnotation.objects.update_or_create(
            defaults,
            run=run,
            alias=alias,
        )

        logger.info(f'{"Created" if created else "Updated"} download {dl}')
        return dl

import logging
import os
from emgapi import models as emg_models

from django.core.management import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    obj_list = list()
    results_directory = None
    genome_folders = None
    catalogue_obj = None
    catalogue_dir = None

    database = None

    def add_arguments(self, parser):
        parser.add_argument(
            "results_directory",
            action="store",
            type=str,
        )
        parser.add_argument(
            "gffs_directory",
            action="store",
            type=str,
            help="The folder within `results_directory` where the GFF files are. "
            'e.g. "emerald/"',
        )
        parser.add_argument("--database", type=str, default="default")

    def handle(self, *args, **options):
        self.results_directory = os.path.realpath(
            options.get("results_directory").strip()
        )

        if not os.path.exists(self.results_directory):
            raise FileNotFoundError(
                "Results dir {} does not exist".format(self.results_directory)
            )

        gffs_directory = options["gffs_directory"].strip()
        self.gffs_dir = os.path.join(self.results_directory, gffs_directory)
        self.database = options["database"]

    def prepare_file_upload(
        self, desc_label, file_format, filename, group_name=None, subdir_name=None
    ):

        obj = {}
        desc = (
            emg_models.DownloadDescriptionLabel.objects.using(self.database)
            .filter(description_label=desc_label)
            .first()
        )
        obj["description"] = desc
        if desc is None:
            logger.error("Desc_label missing: {0}".format(desc_label))
            quit()

        fmt = (
            emg_models.FileFormat.objects.using(self.database)
            .filter(format_extension=file_format, compression=False)
            .first()
        )
        obj["file_format"] = fmt

        name = os.path.basename(filename)
        obj["realname"] = name
        obj["alias"] = name

        if group_name:
            group = (
                emg_models.DownloadGroupType.objects.using(self.database)
                .filter(group_type=group_name)
                .first()
            )
            obj["group_type"] = group

        if subdir_name:
            subdir = (
                emg_models.DownloadSubdir.objects.using(self.database)
                .filter(subdir=subdir_name)
                .first()
            )
            obj["subdir"] = subdir

        return obj

    def upload_gff_file(
        self,
        analysis,
        directory,
        desc_label,
        filename,
        group_type,
        subdir,
        require_existent_and_non_empty,
    ):
        defaults = self.prepare_file_upload(
            desc_label, "gff", filename, group_type, subdir
        )
        path = os.path.join(directory, subdir, filename)
        if not (os.path.isfile(path) and os.path.getsize(path) > 0):
            if require_existent_and_non_empty:
                raise FileNotFoundError(
                    f"Required file at {path} either missing or empty"
                )
            else:
                logger.warning(
                    f"File not found or empty at {path}. This is allowable, but will not be uploaded."
                )
                return
        assembly = analysis.assembly
        if not assembly:
            raise Exception(f"Analysis {analysis} has no Assembly")

        emg_models.AssemblyExtraAnnotation.objects.using(
            self.database
        ).update_or_create(
            assembly=analysis, alias=defaults["alias"], defaults=defaults
        )

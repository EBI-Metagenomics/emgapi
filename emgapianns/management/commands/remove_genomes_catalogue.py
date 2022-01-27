import logging

from django.core.management import BaseCommand

from emgapi import models as emg_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    catalogue_id = None
    database = None

    def add_arguments(self, parser):
        parser.add_argument('catalogue_id', action='store', type=str, help='Example: human-gut-v1-0')
        parser.add_argument(
            '--confirm', action="store_true", dest='confirm',
            help='Do not prompt for confirmation.',
        )
        parser.add_argument('--database', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.database = options['database']
        self.catalogue_id = options['catalogue_id'].strip()

        logger.info("CLI %r" % options)

        try:
            catalogue = emg_models.GenomeCatalogue.objects.using(self.database).get(catalogue_id=self.catalogue_id)
        except emg_models.GenomeCatalogue.DoesNotExist:
            logger.error('Catalogue was not found')
            quit(1)
        else:
            confirm = 'y' if options['confirm'] else input(f'Are you sure you want to delete {self.catalogue_id}? [y/N]')
            if confirm in ['y', 'Y', 'yes']:
                logger.info(f'Deleting catalogue {self.catalogue_id}')
                catalogue.delete(using=self.database)

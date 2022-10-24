import logging
import json
import sys

from django.core.management import BaseCommand

from emgapi.models import VariableNames

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('variable_names_file', action='store', type=str, )
        parser.add_argument('--database', action='store', type=str,
                            default='default')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)

        if VariableNames.objects.exists():
            logger.error('VARIABLE_NAMES table is not empty. Exiting.')
            sys.exit('VARIABLE_NAMES table must be empty before importing')

        with open(options['variable_names_file']) as f:
            vars = json.load(f)

        var_name_objs = []
        for var in vars:
            var_name_objs.append(VariableNames(**{k.lower(): v for k, v in var.items()}))

        VariableNames.objects.bulk_create(var_name_objs)
        logger.info(f'Created {len(var_name_objs)} Variable Names')

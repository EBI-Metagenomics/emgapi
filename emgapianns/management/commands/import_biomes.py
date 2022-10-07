import logging
import json
import sys

from django.core.management import BaseCommand

from emgapi.models import Biome

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('biome_hierarchy_file', action='store', type=str, )
        parser.add_argument('--database', action='store', type=str,
                            default='default')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)

        if Biome.objects.exists():
            logger.error('BIOME table is not empty. Exiting.')
            sys.exit('BIOME table must be empty before importing')

        with open(options['biome_hierarchy_file']) as f:
            biomes = json.load(f)

        biome_objs = []
        for biome in biomes:
            biome_objs.append(Biome(**{k.lower(): v for k, v in biome.items()}))

        Biome.objects.bulk_create(biome_objs)
        logger.info(f'Created {len(biome_objs)} Biomes')

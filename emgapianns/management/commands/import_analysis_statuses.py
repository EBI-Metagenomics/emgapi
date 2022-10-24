import logging
import json
import sys

from django.core.management import BaseCommand

from emgapi.models import AnalysisStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('analysis_statuses_file', action='store', type=str, )
        parser.add_argument('--database', action='store', type=str,
                            default='default')

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)

        if AnalysisStatus.objects.exists():
            logger.error('ANALYSIS_STATUS table is not empty. Exiting.')
            sys.exit('ANALYSIS_STATUS table must be empty before importing')

        with open(options['analysis_statuses_file']) as f:
            statuses = json.load(f)

        status_objs = []
        for status in statuses:
            status_objs.append(AnalysisStatus(**{k.lower(): v for k, v in status.items()}))

        AnalysisStatus.objects.bulk_create(status_objs)
        logger.info(f'Created {len(status_objs)} Analysis Statuses')

import logging

from django.core.management import BaseCommand
from django.db import IntegrityError

from emgapi import models as emg_models
from emgapianns.management.lib.genome_util import read_tsv_w_headers

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    obj_list = list()
    kegg_cache = {}

    database = None

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('cog_desc_file', action='store', type=str, )
        parser.add_argument('--database', action='store', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.database = options['database']
        logger.info("CLI %r" % options)
        entries = self.read_cog_file(options['cog_desc_file'])
        for entry in entries:
            cog_letter, cog_desc = entry['name'], entry['description']
            self.save_cog_entry(cog_letter, cog_desc)

    def read_cog_file(self, cog_file):
        return read_tsv_w_headers(cog_file)

    def save_cog_entry(self, cog_letter, cog_desc):
        try:
            entry = emg_models.CogCat(name=cog_letter,
                                      description=cog_desc)
            entry.save(using=self.database)
        except IntegrityError:
            entry = emg_models.CogCat.objects.using(self.database) \
                .get(name=cog_letter)
            entry.description = cog_desc
            entry.save(using=self.database)

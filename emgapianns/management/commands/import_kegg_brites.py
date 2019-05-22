import logging
import json
import re

from django.core.management import BaseCommand
from django.db import IntegrityError

from emgapi import models as emg_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    obj_list = list()
    kegg_cache = {}

    def add_arguments(self, parser):
        parser.add_argument('kegg_ontology_file', action='store', type=str, )

    def handle(self, *args, **options):
        logger.info("CLI %r" % options)
        entries = self.read_kegg_orthology(options['kegg_ontology_file'])

        for kegg_id, kegg_data in entries.items():
            self.save_kegg_entry(kegg_id, kegg_data)

    def read_kegg_orthology(self, kegg_ontology_file):
        with open(kegg_ontology_file) as f:
            kegg = json.load(f)
        entries = {}

        def find_nodes(node, parent_id=None, depth=0):
            match = re.findall('^([^K]\d+) ([^[]*)', node['name'])
            if len(match) > 0:
                node_id, node_name = match[0]
                if node_id not in entries:
                    entries[node_id] = [node_name, parent_id]

                children = node.get('children') or []
                for child in children:
                    find_nodes(child, parent_id=node_id, depth=depth + 1)

        for child_node in kegg['children']:
            find_nodes(child_node)
        return entries

    def save_kegg_entry(self, kegg_id, data):
        name, parent_id = data
        parent = self.kegg_cache.get(parent_id)
        try:
            entry = emg_models.KeggEntry(brite_id=kegg_id,
                                         brite_name=name,
                                         parent=parent)
            entry.save()
        except IntegrityError:
            entry = emg_models.KeggEntry.objects \
                .get(brite_id=kegg_id)
            entry.brite_name = name
            entry.parent = parent
            entry.save()

        self.kegg_cache[kegg_id] = entry

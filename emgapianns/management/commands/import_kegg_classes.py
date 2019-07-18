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

    database = None

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('kegg_class_ontology_file', action='store', type=str, )
        parser.add_argument('--database', action='store', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.database = options['database']
        logger.info("CLI %r" % options)
        entries = self.read_kegg_orthology(options['kegg_class_ontology_file'])

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
        defs = {
            'name': name,
            'parent': parent
        }
        entry, _ = emg_models.KeggClass.objects.using(self.database).update_or_create(class_id=kegg_id, defaults=defs)
        self.kegg_cache[kegg_id] = entry

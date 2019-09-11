import logging
import json
import re

from django.core.management import BaseCommand

from emgapi import models as emg_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    obj_list = list()
    kegg_cache = {}

    database = None

    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument('kegg_module_ontology_file', action='store', type=str, )
        parser.add_argument('--database', action='store', type=str,
                            default='default')

    def handle(self, *args, **options):
        self.database = options['database']
        logger.info("CLI %r" % options)
        entries = self.read_kegg_orthology(options['kegg_module_ontology_file'])

        for module_name, description in entries.items():
            self.save_kegg_module(module_name, description)

    def read_kegg_orthology(self, kegg_ontology_file):
        with open(kegg_ontology_file) as f:
            kegg = json.load(f)
        entries = {}

        def find_nodes(node):
            match = re.findall('(M\d+)\s+([^[]*)', node['name'])  # noqa: W605
            if len(match) > 0:
                node_name, node_description = match[0]
                if node_name not in entries:
                    entries[node_name] = node_description
            children = node.get('children') or []
            for child in children:
                find_nodes(child)

        for child_node in kegg['children']:
            find_nodes(child_node)
        return entries

    def save_kegg_module(self, name, description):
        defs = {
            'name': name,
            'description': description
        }
        entry, _ = emg_models.KeggModule.objects.using(self.database).update_or_create(name=name, defaults=defs)
        self.kegg_cache[name] = entry

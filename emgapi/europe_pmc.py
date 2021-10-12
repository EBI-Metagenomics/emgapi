import itertools

import requests
from django.conf import settings
from django.http import Http404

TITLE = 'title'
DESCRIPTION = 'description'
ANNOTATIONS = 'annotations'

# based on http://blog.europepmc.org/2020/11/europe-pmc-publications-metagenomics-annotations.html
annotation_type_humanize_map = {
    'Sample-Material': {TITLE: 'Sample material', DESCRIPTION: 'Sample from which the microbiome is extracted'},
    'Body-Site': {TITLE: 'Body site', DESCRIPTION: 'Host body region/structure where microbiome is found'},
    'Host': {TITLE: 'Host', DESCRIPTION: 'The organism where the microbiome is found'},
    'Engineered': {TITLE: 'Engineered environment', DESCRIPTION: 'Microbiome’s man-made environment'},
    'Ecoregion': {TITLE: 'Ecoregion', DESCRIPTION: 'Microbiome’s natural environment'},
    'Date': {TITLE: 'Date', DESCRIPTION: 'Sampling date'},
    'Place': {TITLE: 'Place', DESCRIPTION: 'Microbiome’s place or geocoordinates'},
    'Site': {TITLE: 'Site', DESCRIPTION: 'Microbiome’s site within place'},
    'State': {TITLE: 'State', DESCRIPTION: 'Host/Environment state'},
    'Treatment': {TITLE: 'Treatment', DESCRIPTION: 'Host/Environment treatments'},
    'Kit': {TITLE: 'Kit', DESCRIPTION: 'Nucleic acid extraction-kit'},
    'Gene': {TITLE: 'Gene', DESCRIPTION: 'Target gene(s) (e.g. hypervariable regions of 16s/18s rRNA gene)'},
    'Primer': {TITLE: 'Primer', DESCRIPTION: 'PCR primers'},
    'LS': {TITLE: 'Library strategy', DESCRIPTION: 'e.g. aplicon, whole metagenome'},
    'LCM': {TITLE: 'Library construction method', DESCRIPTION: 'e.g. paired-end, single-end'},
    'Sequencing': {TITLE: 'Sequencing platform', DESCRIPTION: ''},
}

# sample processing annotations tend to be more accurate than others.
sample_processing_annotation_types = ['Sequencing', 'LS', 'LCM', 'Kit', 'Primer']


def get_publication_annotations(pubmed_id):
    """
    Fetch EMERALD-provided Europe PMC metagenomics annotations for a paper, and group them by type.
    :param pubmed_id: the publication identified in pubmed
    :return: grouped and sorted annotations, dict of lists of dicts
    """
    epmc = requests.get(settings.EUROPE_PMC['annotations_endpoint'], params={
        'articleIds': f'MED:{pubmed_id}',
        'provider': settings.EUROPE_PMC['annotations_provider']
    })
    try:
        assert epmc.status_code == 200
        annotations = epmc.json()[0][ANNOTATIONS]
    except (AssertionError, KeyError, IndexError):
        raise Http404

    # Group by annotation type, sort within group by icase annotation text
    grouped_annotations = {
        anno_type: sorted([anno for anno in annots], key=lambda anno: anno.get('exact', '').lower())
        for anno_type, annots
        in itertools.groupby(annotations, key=lambda annotation: annotation.get('type', 'Other'))
    }

    # Split off special sample processing annotation groups
    sample_processing_annotations = []
    other_annotations = []

    for anno_type, annots in grouped_annotations.items():
        humanized_annotation_group = {
            **annotation_type_humanize_map.get(anno_type, {TITLE: anno_type, DESCRIPTION: ''}),
            ANNOTATIONS: annots
        }
        if anno_type in sample_processing_annotation_types:
            sample_processing_annotations.append(humanized_annotation_group)
        else:
            other_annotations.append(humanized_annotation_group)

    # Sort each group by highest number of annotations of that type
    sample_processing_annotations.sort(key=lambda group: len(group.get(ANNOTATIONS, [])), reverse=True)
    other_annotations.sort(key=lambda group: len(group.get(ANNOTATIONS, [])), reverse=True)

    return {'sample_processing': sample_processing_annotations, 'other': other_annotations}

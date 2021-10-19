import itertools
from functools import reduce

import requests
from django.conf import settings
from django.http import Http404

TITLE = 'title'
DESCRIPTION = 'description'
ANNOTATIONS = 'annotations'
MENTIONS = 'mentions'
ANNOTATION_TYPE = 'annotation_type'
ANNOTATION_TEXT = 'annotation_text'

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
    'Primer': {TITLE: 'Primer', DESCRIPTION: 'PCR primers used'},
    'LS': {TITLE: 'Library strategy', DESCRIPTION: 'e.g. amplicon, whole metagenome'},
    'LCM': {TITLE: 'Library construction method', DESCRIPTION: 'e.g. paired-end, single-end'},
    'Sequencing': {TITLE: 'Sequencing platform', DESCRIPTION: 'e.g. Illumina'},
}

# sample processing annotations tend to be more accurate than others.
sample_processing_annotation_types = ['Sequencing', 'LS', 'LCM', 'Kit', 'Primer']


def icase_annotation_text(annotation):
    return annotation.get('exact', '').lower()


def get_publication_annotations(pubmed_id):
    """
    Fetch EMERALD-provided Europe PMC metagenomics annotations for a paper, and group them by type and text.
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

    # Group by annotation type, and within type by icase annotation text
    # Sort within each level by number of annotations inside.
    annotations.sort(key=lambda annotation: annotation.get('type'))
    grouped_annotations = sorted(
        [
            {
                ANNOTATION_TYPE: anno_type,
                ANNOTATIONS: sorted(
                    [
                        {
                            ANNOTATION_TEXT: annot_text_icase,
                            MENTIONS: list(identical_annots)
                        }
                        for annot_text_icase, identical_annots
                        in itertools.groupby(sorted(annots_of_type, key=icase_annotation_text),
                                             key=icase_annotation_text)
                    ],
                    key=lambda annotation: len(annotation[MENTIONS]), reverse=True
                ),
                **annotation_type_humanize_map.get(anno_type, {TITLE: anno_type, DESCRIPTION: ''})
            }
            for anno_type, annots_of_type
            in itertools.groupby(annotations, key=lambda annotation: annotation.get('type', 'Other'))
        ],
        key=lambda group: reduce(
            lambda annot_count_of_type, group: annot_count_of_type + len(group[MENTIONS]),
            group[ANNOTATIONS],
            0
        ), reverse=True
    )

    # Split off special sample processing annotation groups
    sample_processing_annotations = []
    other_annotations = []

    for group in grouped_annotations:
        if group[ANNOTATION_TYPE] in sample_processing_annotation_types:
            sample_processing_annotations.append(group)
        else:
            other_annotations.append(group)

    return {'sample_processing': sample_processing_annotations, 'other': other_annotations}

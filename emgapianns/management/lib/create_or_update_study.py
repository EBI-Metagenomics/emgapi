import logging

from ena_portal_api import ena_handler

from emgapianns.management.lib.uploader_exceptions import StudyNotBeRetrievedFromENA

ena = ena_handler.EnaApiHandler()


def run_create_or_update_study(study_accession):
    """
        Both primary and secondary study accessions are support.

        Steps;
            - Check if study already exists
            - Pull latest study metadata from ENA
            - Save or update entry in EMG
    :param study_accession:
    :return:
    """
    try:
        study = ena.get_study(primary_accession=study_accession)
    except ValueError:
        try:
            study = ena.get_study(secondary_accession=study_accession)
        except ValueError:
            raise StudyNotBeRetrievedFromENA

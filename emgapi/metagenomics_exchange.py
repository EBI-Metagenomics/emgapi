#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018-2024 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import requests
from django.conf import settings
from requests.exceptions import HTTPError


class MetagenomicsExchangeAPI:
    """Metagenomics Exchange API Client"""

    def __init__(self, base_url=None):
        self.base_url = base_url or settings.METAGENOMICS_EXCHANGE_API
        self.__token = f"mgx {settings.METAGENOMICS_EXCHANGE_API_TOKEN}"
        self.broker = settings.METAGENOMICS_EXCHANGE_MGNIFY_BROKER

    def get_request(self, endpoint: str, params: dict):
        """Make a GET request, returns the response"""
        headers = {"Accept": "application/json", "Authorization": self.__token}
        response = requests.get(
            f"{self.base_url}/{endpoint}", headers=headers, params=params
        )
        response.raise_for_status()
        return response

    def post_request(self, endpoint: str, data: dict):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.__token,
        }
        response = requests.post(
            f"{self.base_url}/{endpoint}", json=data, headers=headers
        )
        response.raise_for_status()
        return response

    def delete_request(self, endpoint: str):
        headers = {
            "Accept": "application/json",
            "Authorization": self.__token,
        }
        response = requests.delete(f"{self.base_url}/{endpoint}", headers=headers)
        return response

    def patch_request(self, endpoint: str, data: dict):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.__token,
        }
        response = requests.patch(
            f"{self.base_url}/{endpoint}", json=data, headers=headers
        )
        return response

    def generate_metadata(self, mgya, sequence_accession):
        """Generate the metadata object for the Metagenomics Exchange API.

        Parameters:
        mgya : str
            The MGnify Analysis accession.
        sequence_accession : str
            Either the Run accession or the Assembly accession related to the MGYA.

        Returns:
        dict
            A dictionary containing metadata for the Metagenomics Exchange API.
        """
        return {
            "confidence": "full",
            "endPoint": f"https://www.ebi.ac.uk/metagenomics/analyses/{mgya}",
            "method": ["other_metadata"],
            "sourceID": mgya,
            "sequenceID": sequence_accession,
            "status": "public",
            "brokerID": self.broker,
        }

    def add_analysis(self, mgya: str, sequence_accession: str):
        """Add an analysis to the M. Exchange

        Parameters:
        mgya : str
            The MGnify Analysis accession.
        sequence_accession : str
            Either the Run accession or the Assembly accession related to the MGYA.

        Returns:
        requests.models.Response
            The response object from the API request.
        """
        data = self.generate_metadata(mgya, sequence_accession)
        try:
            response = self.post_request(endpoint="datasets", data=data)
            response.raise_for_status()  # Ensure we raise for HTTP errors
            return response
        except HTTPError as http_error:
            try:
                response_json = http_error.response.json()
                logging.error(f"API response content: {response_json}")
            except ValueError:  # Catch JSON decoding errors
                logging.error(f"Failed to decode JSON from response: {http_error.response.text}")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")

            # Log the HTTP status code and the error message
            logging.error(f"HTTPError occurred: {http_error}")
            return None

    def check_analysis(self, mgya: str, sequence_accession: str, metadata=None):
        """Check if a sequence exists in the M. Exchange

        Parameters:
        mgya : str
            The MGnify Analysis accession.
        sequence_accession : str
            Either the Run accession or the Assembly accession related to the MGYA.

        Returns:
        tuple
            A tuple containing two elements:
                - analysis_registry_id : str
                    The analysis registry ID.
                - metadata_match : boolean
                    True, if the metadata matchs.
        """
        if not mgya:
            raise ValueError(f"mgya is mandatory.")
        if not sequence_accession:
            raise ValueError(f"sequence_accession is mandatory.")

        logging.info(f"Checking {mgya} - {sequence_accession}")

        params = {
            "broker": self.broker,
        }

        endpoint = f"sequences/{sequence_accession}/datasets"
        analysis_registry_id = None
        metadata_match = False

        try:
            response = self.get_request(endpoint=endpoint, params=params)
        except HTTPError as http_error:
            logging.error(f"Get API request failed. HTTP Error: {http_error}")
            try:
                response_json = http_error.response.json()
                logging.error(f"API response content: {response_json}")
            except:
                pass
            return analysis_registry_id, metadata_match

        data = response.json()
        datasets = data.get("datasets", [])

        # The API will return an emtpy datasets array if it can find the accession
        if not len(datasets):
            logging.info(f"{mgya} does not exist in ME")
            return analysis_registry_id, metadata_match

        # TODO: this code needs some refactoring to improve it:
        """
        try:
            found_record = next(item for item in datasets if item.get("sourceID") == mgya)
        except StopIteration
            ...
        """
        sourceIDs = [item.get("sourceID") for item in datasets]
        if mgya in sourceIDs:
            found_record = [item for item in datasets if item.get("sourceID") == mgya][
                0
            ]
            logging.info(f"{mgya} exists in ME")
            analysis_registry_id = found_record.get("registryID")
            if not analysis_registry_id:
                raise ValueError(f"The Metagenomics Exchange 'registryID' for {mgya} is null.")

            if metadata:
                for metadata_record in metadata:
                    if not (metadata_record in found_record):
                        return analysis_registry_id, False
                    else:
                        if metadata[metadata_record] != found_record[metadata_record]:
                            metadata_match = False
                            logging.info(
                                f"The metadata doesn't match, for field {metadata[metadata_record]} != {found_record[metadata_record]})"
                            )
                        else:
                            metadata_match = True
                        return analysis_registry_id, metadata_match
            return analysis_registry_id, metadata_match

        return analysis_registry_id, metadata_match

    def delete_analysis(self, registry_id: str):
        """Delete an entry from the registry"""
        response = self.delete_request(endpoint=f"datasets/{registry_id}")
        if response.ok:
            logging.info(f"{registry_id} was deleted with {response.status_code}")
            return True
        else:
            if response.status_code == 400:
                logging.error(f"Bad request for {registry_id}")
            elif response.status_code == 404:
                logging.error(f"{registry_id} not found")
            elif response.status_code == 401:
                logging.error(f"Failed to authenticate for {registry_id}")
            else:
                logging.error(
                    f"Deleted failed for {registry_id}, response message: {response.message}"
                )
            return False

    def patch_analysis(self, registry_id: str, data: dict):
        """Patch an entry on the registry"""
        response = self.patch_request(endpoint=f"datasets/{registry_id}", data=data)
        if response.ok:
            logging.info(f"{registry_id} was patched")
            return True
        else:
            if response.status_code == 400:
                logging.error(f"Bad request for {registry_id}")
            elif response.status_code == 401:
                logging.error(f"Fail to authenticate for {registry_id}")
            elif response.status_code == 409:
                logging.error(f"Conflicts with existing data for {registry_id}")
            else:
                logging.error(
                    f"Patch failed for {registry_id}, response message: {response.message}"
                )
            return False

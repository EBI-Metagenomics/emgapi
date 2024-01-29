#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018-2023 EMBL - European Bioinformatics Institute
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


class MetagenomicsExchangeAPI:

    """Metagenomics Exchange API Client"""

    def __init__(self, base_url=None):
        self.base_url = base_url if base_url else settings.ME_API
        self.__token = settings.ME_API_TOKEN
        self.broker = settings.MGNIFY_BROKER

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
        response = requests.delete(
            f"{self.base_url}/{endpoint}", headers=headers
        )
        response.raise_for_status()
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
        response.raise_for_status()
        return response

    def add_analysis(self, mgya: str, run_accession: str, public: bool):
        data = {
            "confidence": "full",
            "endPoint": f"https://www.ebi.ac.uk/metagenomics/analyses/{mgya}",
            "method": ["other_metadata"],
            "sourceID": mgya,
            "sequenceID": run_accession,
            "status": "public" if public else "private",
            "brokerID": self.broker,
        }
        response = self.post_request(endpoint="datasets", data=data)
        return response


    def check_analysis(self, source_id: str, public=None, metadata=None) -> [str, bool]:
        logging.info(f"Check {source_id}")
        params = {}
        if public:
            params = {
                "status": "public" if public else "private",
            }
        endpoint = f"brokers/{self.broker}/datasets"
        response = self.get_request(endpoint=endpoint, params=params)
        analysis_registryID = ""
        metadata_match = True
        if response.ok:
            data = response.json()
            datasets = data.get("datasets")
            for item in datasets:
                if item.get("sourceID") == source_id:
                    logging.info(f"{source_id} exists in ME")
                    analysis_registryID = item.get("registryID")
                    if metadata:
                        for metadata_record in metadata:
                            if not(metadata_record in item):
                                metadata_match = False
                                return analysis_registryID, metadata_match
                            else:
                                if metadata[metadata_record] != item[metadata_record]:
                                    metadata_match = False
                                    logging.info(f"Incorrect field {metadata[metadata_record]} in ME ({item[metadata_record]})")
                                    return analysis_registryID, metadata_match
                    return analysis_registryID, metadata_match
                else:
                    logging.info(f"{source_id} does not exist in ME")
        return analysis_registryID, metadata_match

    def delete_analysis(self, registry_id: str):
        response = self.delete_request(endpoint=f"datasets/{registry_id}")
        if response.ok:
            logging.info(f"{registry_id} was deleted with {response.status_code}")
            return True
        else:
            if response.status_code == 400:
                logging.error(f"Bad request for {registry_id}")
            elif response.status_code == 401:
                logging.error(f"Failed to authenticate for {registry_id}")
            else:
                logging.error(f"{response.message} for {registry_id}")
            return False

    def patch_analysis(self, registry_id: str, data: dict):
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
            return False

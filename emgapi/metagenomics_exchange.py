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

    def __init__(self, broker="EMG"):
        self.base_url = settings.ME_API
        self.__token = settings.ME_API_TOKEN
        self.broker = broker

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

    def add_record(self, mgya: str, run_accession: str, public: bool):
        data = {
            "confidence": "full",
            "endPoint": f"https://www.ebi.ac.uk/metagenomics/analyses/mgya",
            "method": ["other_metadata"],
            "sourceID": mgya,
            "sequenceID": run_accession,
            "status": "public" if public else "private",
            "brokerID": self.broker,
        }
        response = self.post_request(endpoint="datasets", data=data)
        return response.json()

    def check_analysis(self, source_id: str, public: bool) -> bool:
        logging.info(f"Check {source_id}")
        params = {
            "status": "public" if public else "private",
        }
        endpoint = f"brokers/{self.broker}/datasets"
        response = self.get_request(endpoint=endpoint, params=params)
        if response.ok:
            data = response.json()
            datasets = data.get("datasets")
            for item in datasets:
                if item.get("sourceID") == source_id:
                    return True
            logging.info(f"{source_id} exists")

        return False

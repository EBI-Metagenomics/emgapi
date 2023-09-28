#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018-2021 EMBL - European Bioinformatics Institute
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

import sys
import logging
import requests

class MetagenomicsExchangeAPI:
    """Metagenomics Exchange API Client"""
    def get_request(self, session, url, params):
        response = session.get(url, params=params)
        data = None
        if not response.ok:
            logging.error(
                "Error retrieving dataset {}, response code: {}".format(
                    url, response.status_code
                )
            )
        else:
            data = response.json()
        return data

    def post_request(self, session, url, data):
        default = {
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        }

        response = session.post(
            url, json=data, **default
        )

        if response.ok:
            print('Added')
            logging.info("Data added to ME")
            logging.debug(response.text)
        else:
            print(response.text)
        return response
    def add_record(
        self, url, mgya, run_accession, public, broker, token
    ):
        data = {
            'confidence': 'full',
            'endPoint': f'https://www.ebi.ac.uk/metagenomics/analyses/mgya',
            'method': ['other_metadata'],
            'sourceID': mgya,
            'sequenceID': run_accession,
            'status': 'public' if public else 'private',
            'brokerID': broker,
        }

        with requests.Session() as session:
            url = url + 'datasets'
            session = self._authenticate_session(session, url, token)
            print(session)
            response = self.post_request(session=session, url=url, data=data)
            data = response.json()
            return data

    def check_analysis(self, url, sourceID, public, token):
        logging.info(f'Check {sourceID}')
        params = {
            'status': 'public' if public else 'private',
        }
        with requests.Session() as session:
            session = self._authenticate_session(session, url, token)
            response = self.get_request(session=session, url=url, params=params)
            if response:
                data = response['datasets']
                exists = False
                for item in data:
                    if item['sourceID'] == sourceID:
                        exists = True
                logging.info(f"{sourceID} exists: {exists}")
        return exists

    def _authenticate_session(self, session, url, token):
        """Authenticate the MGnify API request"""

        logging.debug(f"Authenticating ME account")

        headers = {"Authorization": token}

        response = session.get(url, headers=headers)

        if response.ok:
            logging.debug("ME account successfully authenticated.")
            print(f'Auth {url} {response}')
        else:
            print(response)
            # Log textual reason of responded HTTP Status
            logging.error(f"Authentication services responded: {response.reason}). Program will exit now.")
            sys.exit(1)

        return session

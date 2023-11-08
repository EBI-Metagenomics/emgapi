#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019-2023 EMBL - European Bioinformatics Institute
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
import os
from time import sleep

import requests
import logging


EUROPE_PMC_API_URL = os.environ.get(
    "EUROPE_PMC_API_URL", "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
)


def get_default_connection_headers():
    return {
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
        }
    }


class Publication:
    def __init__(
        self,
        pub_year,
        author_string,
        journal_issn,
        pub_type,
        journal_volume,
        title,
        cited_by_count,
        source,
        pmid,
        page_info,
        doi,
        journal_title,
    ):
        self.pub_year = int(pub_year)
        self.author_string = author_string
        self.journal_issn = journal_issn
        self.pub_type = pub_type
        self.journal_volume = journal_volume
        self.title = title
        self.cited_by_count = cited_by_count
        self.source = source
        self.pmid = int(pmid)
        self.page_info = page_info
        self.doi = doi
        self.journal_title = journal_title


class EuropePMCApiHandler:
    def __init__(self):
        self._url = EUROPE_PMC_API_URL
        self._result_type = "lite"
        self._format = "json"

    def _send_get_request(self, params):
        return requests.get(
            self._url, params=params, **get_default_connection_headers()
        )

    @staticmethod
    def _parse_result_list(result_list):
        publications = []

        for item in result_list["result"]:
            publications.append(
                Publication(
                    item.get("pubYear", 0),
                    item.get("authorString", "n/a"),
                    item.get("journalIssn", "n/a"),
                    item.get("pubType", "n/a"),
                    item.get("journalVolume", "n/a"),
                    item.get("title", "n/a"),
                    item.get("citedByCount", 0),
                    item.get("source", "n/a"),
                    item.get("pmid", 0),
                    item.get("pageInfo", "n/a"),
                    item.get("doi", "n/a"),
                    item.get("journalTitle", "n/a"),
                )
            )

        return publications

    def _convert_response(self, response, pubmed_id):
        """Converts the response object into a dict."""
        result_key = "resultList"
        json_data = response.json()

        logging.debug("The response contains {0} properties".format(len(json_data)))
        if result_key in json_data:
            if len(json_data[result_key]["result"]) > 0:
                return self._parse_result_list(json_data[result_key])
            else:
                raise ValueError(
                    "Could not find publication for PubMED {} in Europe PMC.".format(
                        pubmed_id
                    )
                )
        else:
            logging.error(
                "Expected result key - {} - not found in JSON response.".format(
                    result_key
                )
            )

        return None

    def get_publication_by_pubmed_id(self, pubmed_id, attempt=1):
        if not isinstance(pubmed_id, int):
            raise TypeError(
                "The specified pubmed id: {} is not a number!".format(pubmed_id)
            )
        query = "ext_id:{0}".format(pubmed_id)
        search_params = {
            "query": query,
            "resultType": self._result_type,
            "format": self._format,
        }
        response = self._send_get_request(search_params)

        if str(response.status_code)[0] != "2":
            logging.info("{} attempt".format(attempt))
            logging.info(search_params)
            logging.info("Response: {}".format(response.text))
            error_message = (
                "Error retrieving publication {}, response code: {}.".format(
                    pubmed_id, response.status_code
                )
            )
            logging.warning(error_message)
            attempt += 1
            if attempt > 3:
                logging.info("Program will exit now!")
                response.raise_for_status()
            else:
                sleep(1)
                return self.get_publication_by_pubmed_id(
                    pubmed_id=pubmed_id, attempt=attempt
                )

        elif response.status_code == 204:
            raise ValueError(
                "Could not find publication for PubMED {} in Europe PMC.".format(
                    pubmed_id
                )
            )
        else:
            return self._convert_response(response, pubmed_id)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import logging

from django.conf import settings

from emgapi.metagenomics_exchange import MetagenomicsExchangeAPI

import requests
import responses
from unittest import mock


class TestME:

    def test_check_existing_analysis_me(self):
        me_api = MetagenomicsExchangeAPI()
        source_id = "MGYA00293719"
        seq_id = "ERR3063408"
        return_values = me_api.check_analysis(source_id, seq_id, True)
        assert return_values[0]

    def test_check_not_existing_analysis_me(self):
        me_api = MetagenomicsExchangeAPI()
        source_id = "MGYA10293719"
        seq_id = "ERR3063408"
        return_values = me_api.check_analysis(source_id, seq_id, True)
        assert not return_values[0]

    @pytest.mark.skip(reason="Error on ME API side")
    def test_post_existing_analysis_me(self):
        me_api = MetagenomicsExchangeAPI()
        source_id = "MGYA00293719"
        # Should return -> https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/409
        with pytest.raises(requests.HTTPError, match="401 Client Error"):
            me_api.add_analysis(
                mgya=source_id, run_accession="ERR3063408", public=True
            ).json()

    @responses.activate
    def test_mock_post_new_analysis(self):
        me_api = MetagenomicsExchangeAPI()
        endpoint = "datasets"
        url = settings.METAGENOMICS_EXCHANGE_API + f"/{endpoint}"

        responses.add(responses.POST, url, json={"success": True}, status=201)

        response = me_api.add_analysis(
            mgya="MGYA00593709", run_accession="SRR3960575", public=True
        )

        assert response.status_code == 201
        assert response.json() == {"success": True}

    @responses.activate
    def test_mock_delete_analysis_from_me(self):
        me_api = MetagenomicsExchangeAPI()
        registry_id = "MGX0000780"
        endpoint = f"datasets/{registry_id}"
        url = settings.METAGENOMICS_EXCHANGE_API + f"/{endpoint}"

        responses.add(responses.DELETE, url, json={"success": True}, status=201)
        response = me_api.delete_request(endpoint)

        assert response.status_code == 201
        assert response.json() == {"success": True}

    def test_wrong_delete_request_me(self):
        me_api = MetagenomicsExchangeAPI()
        registry_id = "MGX0000780"
        endpoint = f"dataset/{registry_id}"
        assert not me_api.delete_request(endpoint)

    @mock.patch("emgapi.metagenomics_exchange.MetagenomicsExchangeAPI.patch_request")
    def test_patch_analysis_me(self, mock_patch_request):
        me_api = MetagenomicsExchangeAPI()

        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.ok = True

            def json(self):
                return self.json_data

        mock_patch_request.return_value = MockResponse({}, 200)
        registry_id = "MGX0000788"
        mgya = "MGYA00593709"
        run_accession = "SRR3960575"
        public = False

        data = {
            "confidence": "full",
            "endPoint": f"https://www.ebi.ac.uk/metagenomics/analyses/{mgya}",
            "method": ["other_metadata"],
            "sourceID": mgya,
            "sequenceID": run_accession,
            "status": "public" if public else "private",
            "brokerID": "EMG",
        }
        assert me_api.patch_analysis(registry_id, data)

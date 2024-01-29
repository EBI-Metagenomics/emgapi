#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from django.conf import settings

from emgapi.metagenomics_exchange import MetagenomicsExchangeAPI

import requests
import responses

class TestME:
    def test_check_existing_analysis(self):
        me_api = MetagenomicsExchangeAPI()
        source_id = "MGYA00293719"
        assert me_api.check_analysis(source_id, True)

    def test_check_not_existing_analysis(self):
        me_api = MetagenomicsExchangeAPI(broker="MAR")
        source_id = "MGYA00293719"
        assert not me_api.check_analysis(source_id, True)

    def test_post_existing_analysis(self):
        me_api = MetagenomicsExchangeAPI()
        source_id = "MGYA00293719"
        # Should return -> https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/409
        with pytest.raises(requests.HTTPError, match="409 Client Error"):
            me_api.add_analysis(mgya=source_id, run_accession="ERR3063408", public=True).json()

    @responses.activate
    def test_mock_post_new_analysis(self):
        me_api = MetagenomicsExchangeAPI()
        endpoint = "datasets"
        url = settings.ME_API + f"/{endpoint}"

        responses.add(responses.POST, url, json={'success': True}, status=201)

        response = me_api.add_analysis(mgya="MGYA00593709", run_accession="SRR3960575", public=True)

        assert response.status_code == 201
        assert response.json() == {'success': True}
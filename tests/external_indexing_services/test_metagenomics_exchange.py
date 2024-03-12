#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import requests
import responses
from django.conf import settings

from emgapi.metagenomics_exchange import MetagenomicsExchangeAPI


class TestME:

    @responses.activate
    def test_check_existing_analysis_me(self, settings):
        # FIXME: this test doesn't check if the metadata matches or not.
        mgya = "MGYA00293719"
        sequence_accession = "ERR3063408"
        responses.add(
            responses.GET,
            f"{settings.METAGENOMICS_EXCHANGE_API}/sequences/{sequence_accession}/datasets",
            json={"datasets": [{"sourceID": mgya, "registryID": "MGX_FAKE"}]},
            status=200,
        )
        me_api = MetagenomicsExchangeAPI()

        registry_id, _ = me_api.check_analysis(mgya, sequence_accession)
        assert registry_id == "MGX_FAKE"

    @responses.activate
    def test_check_not_existing_analysis_me(self):
        mgya = "MGYA10293719"
        sequence_accession = "ERR3063408"
        responses.add(
            responses.GET,
            f"{settings.METAGENOMICS_EXCHANGE_API}/sequences/{sequence_accession}/datasets",
            json={"datasets": []},
            status=200,
        )
        me_api = MetagenomicsExchangeAPI()
        return_values = me_api.check_analysis(mgya, sequence_accession)
        assert not return_values[0]

    @pytest.mark.skip(reason="Error on ME API side")
    def test_post_existing_analysis_me(self):
        me_api = MetagenomicsExchangeAPI()
        source_id = "MGYA00293719"
        # Should return -> https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/409
        with pytest.raises(requests.HTTPError, match="401 Client Error"):
            me_api.add_analysis(mgya=source_id, sequence_accession="ERR3063408").json()

    @responses.activate
    def test_mock_post_new_analysis(self):
        me_api = MetagenomicsExchangeAPI()
        endpoint = "datasets"
        url = settings.METAGENOMICS_EXCHANGE_API + f"/{endpoint}"

        responses.add(responses.POST, url, json={"success": True}, status=201)

        response = me_api.add_analysis(
            mgya="MGYA00593709", sequence_accession="SRR3960575"
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

    @responses.activate
    def test_incorrect_delete_request_me(self):
        # TODO: this test doesn't make much sense
        me_api = MetagenomicsExchangeAPI()
        responses.add(
            responses.DELETE,
            f"{settings.METAGENOMICS_EXCHANGE_API}/dataset/MGX0000780",
            status=401,
        )
        registry_id = "MGX0000780"
        endpoint = f"dataset/{registry_id}"
        response = me_api.delete_request(endpoint)
        assert response.status_code == 401

    @responses.activate
    def test_patch_analysis_me(self):
        me_api = MetagenomicsExchangeAPI()

        registry_id = "MGX0000788"
        mgya = "MGYA00593709"
        run_accession = "SRR3960575"
        data = {
            "confidence": "full",
            "endPoint": f"https://www.ebi.ac.uk/metagenomics/analyses/{mgya}",
            "method": ["other_metadata"],
            "sourceID": mgya,
            "sequenceID": run_accession,
            "status": "public",
            "brokerID": "EMG",
        }

        responses.add(
            responses.PATCH,
            f"{settings.METAGENOMICS_EXCHANGE_API}/datasets/{registry_id}",
            status=200,
        )

        assert me_api.patch_analysis(registry_id, data)

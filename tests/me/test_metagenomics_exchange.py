#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from unittest import mock

from emgapi.metagenomics_exchange import MetagenomicsExchangeAPI

from requests import HTTPError


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
        with pytest.raises(HTTPError, match="409 Client Error"):
            me_api.add_record(mgya=source_id, run_accession="ERR3063408", public=True)

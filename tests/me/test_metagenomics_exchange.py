#!/usr/bin/env python
# -*- coding: utf-8 -*-

from emgapi import metagenomics_exchange as ME
from django.conf import settings

class TestME:

    test_ME = ME.MetagenomicsExchangeAPI()
    def test_check_existing_analysis(self):
        sourceID = "MGYA00293719"
        broker = 'EMG'
        url = settings.ME_API['dev'] + f'brokers/{broker}/datasets'
        token = settings.ME_TOKEN
        assert self.test_ME.check_analysis(url, sourceID, True, token)

    def test_check_not_existing_analysis(self):
        sourceID = "MGYA00293719"
        broker = 'MAR'
        url = settings.ME_API['dev'] + f'brokers/{broker}/datasets'
        token = settings.ME_TOKEN
        assert not self.test_ME.check_analysis(url, sourceID, True, token)

    def test_post_existing_analysis(self):
        sourceID = "MGYA00293719"
        broker = 'EMG'
        url = settings.ME_API['dev']
        token = settings.ME_TOKEN
        assert not self.test_ME.add_record(url=url, mgya=sourceID, run_accession="ERR3063408", public=True,
                                           broker=broker, token=token)

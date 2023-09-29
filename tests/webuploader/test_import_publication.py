#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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

import pytest

from emgapi.models import Publication
from model_bakery import baker


from emgapianns.management.commands.import_publication import (
    lookup_publication_by_pubmed_id,
)


@pytest.mark.parametrize(
    "pubmed_id, expected_pub_title, expected_year_of_pub, expected_authors, expected_doi",
    [
        (
            4838818,
            "Proceedings: The morphological variation of nervous structures in the atrial endocardium of the dog.",
            1974,
            "Floyd K, Linden RJ, Saunders DA.",
            "n/a",
        ),
        (
            31138692,
            "Mechanisms by which sialylated milk oligosaccharides impact bone biology in a gnotobiotic mouse "
            "model of infant undernutrition.",
            2019,
            "Cowardin CA, Ahern PP, Kung VL, Hibberd MC, Cheng J, Guruge JL, Sundaresan V, Head RD, Barile D,"
            " Mills DA, Barratt MJ, Huq S, Ahmed T, Gordon JI.",
            "10.1073/pnas.1821770116",
        ),
    ],
)
def test_lookup_publication_by_pubmed_id_should_return(
    pubmed_id, expected_pub_title, expected_year_of_pub, expected_authors, expected_doi
):
    publications = lookup_publication_by_pubmed_id(pubmed_id)
    assert len(publications) == 1

    publication = publications[0]
    assert publication.title == expected_pub_title
    assert int(publication.pmid) == pubmed_id
    assert publication.pub_year == expected_year_of_pub
    assert publication.author_string == expected_authors
    assert publication.doi == expected_doi


@pytest.mark.parametrize("pubmed_id", [(0), (000)])
def test_lookup_publication_by_pubmed_id_(pubmed_id):
    with pytest.raises(ValueError):
        lookup_publication_by_pubmed_id(pubmed_id)


@pytest.mark.parametrize("pubmed_id", [("test")])
def test_lookup_publication_by_pubmed_id_raises_exception_on_string(pubmed_id):
    with pytest.raises(TypeError):
        lookup_publication_by_pubmed_id(pubmed_id)


@pytest.mark.django_db
def test_text_fields_longer_than_expected(faker):
    PUB_TITLE_MAX = 740
    PUB_TYPE_MAX = 300
    VOLUME_MAX = 55

    # I've picked 3 fields as representatives
    publications = baker.prepare(
        Publication,
        pub_title=faker.text(max_nb_chars=PUB_TITLE_MAX + 1000),
        pub_type=faker.text(max_nb_chars=PUB_TYPE_MAX + 1000),
        volume=faker.text(max_nb_chars=VOLUME_MAX + 1000),
        _quantity=5,
    )

    for publication in publications:
        assert len(publication.pub_title) > PUB_TITLE_MAX
        assert len(publication.pub_type) > PUB_TYPE_MAX
        assert len(publication.volume) > VOLUME_MAX
        publication.save()
        assert len(publication.pub_title) <= PUB_TITLE_MAX
        assert len(publication.pub_type) <= PUB_TYPE_MAX
        assert len(publication.volume) <= VOLUME_MAX

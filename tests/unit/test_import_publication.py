import pytest
from django.db.transaction import TransactionManagementError
from django.test import TransactionTestCase

from emgapianns.management.commands.import_publication import lookup_publication_by_pubmed_id, \
    update_or_create_publication
from emgapianns.management.lib.europe_pmc_api.europe_pmc_api_handler import Publication


@pytest.mark.parametrize("pubmed_id, expected_pub_title, expected_year_of_pub, expected_authors, expected_doi", [
    (4838818,
     "Proceedings: The morphological variation of nervous structures in the atrial endocardium of the dog.",
     1974,
     "Floyd K, Linden RJ, Saunders DA.",
     "n/a"),
    (31138692,
     "Mechanisms by which sialylated milk oligosaccharides impact bone biology in a gnotobiotic mouse model of infant undernutrition.",
     2019,
     "Cowardin CA, Ahern PP, Kung VL, Hibberd MC, Cheng J, Guruge JL, Sundaresan V, Head RD, Barile D, Mills DA, Barratt MJ, Huq S, Ahmed T, Gordon JI.",
     "10.1073/pnas.1821770116")
])
def test_lookup_publication_by_pubmed_id_should_return(pubmed_id,
                                                       expected_pub_title,
                                                       expected_year_of_pub,
                                                       expected_authors,
                                                       expected_doi):
    publications = lookup_publication_by_pubmed_id(pubmed_id)
    assert len(publications) == 1

    publication = publications[0]
    assert publication.title == expected_pub_title
    assert int(publication.pmid) == pubmed_id
    assert publication.pub_year == expected_year_of_pub
    assert publication.author_string == expected_authors
    assert publication.doi == expected_doi


@pytest.mark.parametrize("pubmed_id", [
    (0),
    (000)
])
def test_lookup_publication_by_pubmed_id_(pubmed_id):
    with pytest.raises(ValueError):
        lookup_publication_by_pubmed_id(pubmed_id)


@pytest.mark.parametrize("pubmed_id", [
    ("test")
])
def test_lookup_publication_by_pubmed_id_raises_exception_on_string(pubmed_id):
    with pytest.raises(TypeError):
        lookup_publication_by_pubmed_id(pubmed_id)


# TODO: Check with Miguel how to run it safely
# class PublicationTestCase(TransactionTestCase):
#     def setUp(self):
#         self.publication = Publication(1974, "Floyd K, Linden RJ, Saunders DA.", '0022-3751; 1469-7793; ',
#                                        'journal article', '238',
#                                        'Proceedings: The morphological variation of nervous structures in the atrial endocardium of the dog.',
#                                        None, None, 4838818, '19P', 'n/a', 'J Physiol')
#
#     def test_select_for_update_raises_an_error_without_transaction(self):
#         with self.assertRaises(TransactionManagementError):
#             publication = update_or_create_publication(self.publication)
#             print(publication)  # needed to actually execute the query because they are lazy

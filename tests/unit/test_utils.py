from bmt.toolkit import Toolkit
import pytest

from bmt.utils import parse_name, format_element, sentencecase_to_camelcase


@pytest.fixture(scope="module")
def toolkit():
    return Toolkit()


@pytest.mark.parametrize(
    "query",
    [
        ("biolink:Gene", "gene"),
        ("biolink:NamedThing", "named thing"),
        ("biolink:related_to", "related to"),
        ("PhenotypicFeature", "phenotypic feature"),
        ("related_to", "related to"),
        ("related to", "related to"),
        ("causes", "causes"),
        ("treats", "treats"),
        ("gene", "gene"),
        ("has_gene", "has gene"),
        ("biolink:GeneToGeneAssociation", "gene to gene association"),
        ("RNA product", "RNA product"),
        ("RNA Product", "RNA Product"),
        ("Rna Product", "Rna Product"),
        ("biolink:RNAProduct", "RNA product"),
    ],
)
def test_parse_name(query):
    n = parse_name(query[0])
    assert n == query[1]


@pytest.mark.parametrize(
    "query",
    [
        ("phenotypic feature", "PhenotypicFeature"),
        ("noncoding RNA product", "NoncodingRNAProduct"),
    ],
)
def test_sentencecase_to_camelcase(query):
    n = sentencecase_to_camelcase(query[0])
    assert n == query[1]


@pytest.mark.parametrize(
    "query",
    [
        ("related to", "biolink:related_to"),
        ("caused_by", "biolink:caused_by"),
        ("PhenotypicFeature", "biolink:PhenotypicFeature"),
        ("noncoding RNA product", "biolink:NoncodingRNAProduct"),
    ],
)
def test_format_element(query, toolkit):
    n = format_element(toolkit.get_element(query[0]))
    assert n == query[1]

if __name__ == '__main__':
    pytest.main(["."])
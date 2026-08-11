from bmt.toolkit import Toolkit
import pytest

from bmt.utils import (
    parse_name,
    format_element,
    sentencecase_to_camelcase,
    sentencecase_to_snakecase,
    snakecase_to_sentencecase,
)


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
        ("related_to", "related to"),
        ("has_gene_product", "has gene product"),
        ("gene_product_of", "gene product of"),
        ("physically_interacts_with", "physically interacts with"),
        ("in_taxon", "in taxon"),
        ("subclass_of", "subclass of"),
        ("has_qualitative_form_or_quantity", "has qualitative form or quantity"),
        ("colocalizes_with", "colocalizes with"),
        ("max_research_phase", "max research phase"),
        # Already sentence case, or a single word: unchanged apart from folding.
        ("affects", "affects"),
        ("", ""),
    ],
)
def test_snakecase_to_sentencecase(query):
    n = snakecase_to_sentencecase(query[0])
    assert n == query[1]


@pytest.mark.parametrize(
    "query",
    [
        ("related to", "related_to"),
        ("has gene product", "has_gene_product"),
        ("gene product of", "gene_product_of"),
        ("physically interacts with", "physically_interacts_with"),
        ("in taxon", "in_taxon"),
        ("subclass of", "subclass_of"),
        ("gene or gene product", "gene_or_gene_product"),
        ("named thing", "named_thing"),
        ("log odds ratio 95 ci", "log_odds_ratio_95_ci"),
        ("affects", "affects"),
        ("", ""),
    ],
)
def test_sentencecase_to_snakecase(query):
    n = sentencecase_to_snakecase(query[0])
    assert n == query[1]


@pytest.mark.parametrize(
    "query",
    [
        # An embedded acronym is split into one segment per letter, and the
        # boundary before it is *not* doubled the way stringcase doubled it
        # ("highest__f_d_a_approval_status", "noncoding__r_n_a_product").
        ("highest FDA approval status", "highest_f_d_a_approval_status"),
        ("noncoding RNA product", "noncoding_r_n_a_product"),
    ],
)
def test_sentencecase_to_snakecase_acronyms(query):
    """
    Pin how acronyms fall out of ``sentencecase_to_snakecase``.

    Neither the current output nor stringcase's reproduces the model's own
    ``biolink:highest_FDA_approval_status``, so this is not a correctness
    assertion -- it records the shape callers actually get, so that any future
    change to it is a deliberate one.
    """
    n = sentencecase_to_snakecase(query[0])
    assert n == query[1]


@pytest.mark.parametrize(
    "query",
    [
        # Digit runs are split per digit, so this does not round-trip back to
        # the model's "log odds ratio 95 ci"; get_element only still resolves
        # it because of the separator-insensitive fallback in Toolkit.
        ("log_odds_ratio_95_ci", "log odds ratio 9 5 ci"),
        ("1_to_1", "1 to 1"),
    ],
)
def test_snakecase_to_sentencecase_digits(query):
    n = snakecase_to_sentencecase(query[0])
    assert n == query[1]


def test_format_element_round_trips_for_every_element(toolkit):
    """
    Every class and slot in the model must survive name -> CURIE -> name.

    This is the property the case-conversion helpers exist to serve, so it is
    the guard that matters if they are ever swapped out again. ``metatype:``
    CURIEs from the linkml types schema are excluded: ``parse_name`` only
    understands the ``biolink:`` prefix, so they have never round-tripped.
    """
    failures = []
    for name in sorted(set(toolkit.get_all_elements())):
        element = toolkit.get_element(name)
        assert element is not None, f"{name} is listed but does not resolve"
        curie = format_element(element)
        if curie.startswith("metatype:"):
            continue
        resolved = toolkit.get_element(curie)
        if resolved is None or resolved.name != element.name:
            failures.append((name, curie, resolved.name if resolved else None))
    assert not failures


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

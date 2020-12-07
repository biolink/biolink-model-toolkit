import pytest

from bmt.utils import parse_name


@pytest.mark.parametrize('query', [
    ('biolink:Gene', 'gene'),
    ('biolink:NamedThing', 'named thing'),
    ('biolink:related_to', 'related to'),
    ('PhenotypicFeature', 'phenotypic feature'),
    ('related_to', 'related to'),
    ('related to', 'related to'),
    ('causes', 'causes'),
    ('treats', 'treats'),
    ('gene', 'gene'),
    ('has_gene', 'has gene'),
    ('biolink:GeneToGeneAssociation', 'gene to gene association'),
    ('RNA product', 'RNA product'),
    ('RNA Product', 'RNA Product'),
    ('Rna Product', 'Rna Product'),
])
def test_parse_name(query):
    n = parse_name(query[0])
    assert n == query[1]


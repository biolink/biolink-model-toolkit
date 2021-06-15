import pytest
from bmt import Toolkit


@pytest.fixture(scope="module")
def toolkit():
    return Toolkit()


GENE_OR_GENE_PRODUCT = "gene or gene product"
NUCLEIC_ACID_ENTITY = "nucleic acid entity"
MOLECULAR_ACTIVITY = "molecular activity"
GENOMIC_ENTITY = "genomic entity"
BIOLOGICAL_ENTITY = "biological entity"
RELATED_TO = "related to"
INTERACTS_WITH = "interacts with"
NAMED_THING = "named thing"
SUBJECT = "subject"
ENABLED_BY = "enabled by"


def test_get_model_version(toolkit):
    version = toolkit.get_model_version()
    assert version == '2.0.1'


def test_get_all_elements(toolkit):
    elements = toolkit.get_all_elements()
    assert NAMED_THING in elements
    assert 'association' in elements
    assert RELATED_TO in elements
    assert 'uriorcurie' in elements

    elements = toolkit.get_all_elements(formatted=True)
    assert 'biolink:NamedThing' in elements
    assert 'biolink:GeneToGeneAssociation' in elements
    assert 'biolink:related_to' in elements
    assert 'metatype:Uriorcurie' in elements
    assert 'biolink:FrequencyValue' in elements


def test_get_all_entities(toolkit):
    entities = toolkit.get_all_entities()
    assert NAMED_THING in entities
    assert 'gene' in entities
    assert 'disease' in entities
    assert 'association' not in entities
    assert RELATED_TO not in entities

    entities = toolkit.get_all_entities(formatted=True)
    assert 'biolink:NamedThing' in entities
    assert 'biolink:Gene' in entities
    assert 'biolink:Disease' in entities


def test_get_all_associations(toolkit):
    associations = toolkit.get_all_associations()
    assert 'association' in associations
    assert 'gene to gene association' in associations
    assert NAMED_THING not in associations

    associations = toolkit.get_all_associations(formatted=True)
    assert 'biolink:Association' in associations
    assert 'biolink:GeneToGeneAssociation' in associations


def test_get_all_node_properties(toolkit):
    properties = toolkit.get_all_node_properties()
    assert 'name' in properties
    assert 'category' in properties
    assert 'has gene' in properties

    properties = toolkit.get_all_node_properties(formatted=True)
    assert 'biolink:name' in properties
    assert 'biolink:category' in properties
    assert 'biolink:has_gene' in properties


def test_get_all_edge_properties(toolkit):
    properties = toolkit.get_all_edge_properties()
    assert SUBJECT in properties
    assert 'object' in properties
    assert 'frequency qualifier' in properties

    properties = toolkit.get_all_edge_properties(formatted=True)
    assert 'biolink:subject' in properties
    assert 'biolink:object' in properties
    assert 'biolink:frequency_qualifier' in properties


def test_get_element(toolkit):
    gene = toolkit.get_element('gene')
    locus = toolkit.get_element('locus')
    assert gene == locus

    o = toolkit.get_element('drug intake')
    assert o and o.name == 'drug exposure'

    o = toolkit.get_element('molecular function')
    assert o and o.name == MOLECULAR_ACTIVITY

    o = toolkit.get_element('RNA Product')
    assert o and o.name == 'RNA product'

    o = toolkit.get_element('rna product')
    assert o and o.name == 'RNA product'


def test_predicate(toolkit):
    assert not toolkit.is_predicate(NAMED_THING)
    assert not toolkit.is_predicate('gene')
    assert toolkit.is_predicate('causes')


def test_mixin(toolkit):
    assert not toolkit.is_mixin(NAMED_THING)
    assert toolkit.is_mixin('ontology class')
    assert not toolkit.is_mixin('this_does_not_exist')


def test_is_translator_canonical_predicate(toolkit):
    assert toolkit.is_translator_canonical_predicate('treats')
    assert not toolkit.is_translator_canonical_predicate('treated by')
    assert not toolkit.is_translator_canonical_predicate('this_does_not_exist')


def test_has_inverse(toolkit):
    assert not toolkit.has_inverse('contributor')
    assert toolkit.has_inverse('superclass of')
    assert not toolkit.has_inverse('this_does_not_exist')


def test_category(toolkit):
    assert toolkit.is_category(NAMED_THING)
    assert toolkit.is_category('gene')
    assert not toolkit.is_category('causes')
    assert not toolkit.is_category('affects')


def test_ancestors(toolkit):
    assert RELATED_TO in toolkit.get_ancestors('causes')
    assert 'biolink:GenomicEntity' in toolkit.get_ancestors('gene', formatted=True)
    assert 'biolink:related_to' in toolkit.get_ancestors('causes', formatted=True)
    assert 'biolink:GeneOrGeneProduct' in toolkit.get_ancestors('gene', formatted=True)
    assert NAMED_THING in toolkit.get_ancestors('gene')
    assert GENE_OR_GENE_PRODUCT in toolkit.get_ancestors('gene')
    assert 'biolink:NamedThing' in toolkit.get_ancestors('gene', formatted=True)
    assert 'chemical entity' in toolkit.get_ancestors('gene')
    assert 'transcript' not in toolkit.get_ancestors('gene')
    assert 'causes' in toolkit.get_ancestors('causes')
    assert 'causes' in toolkit.get_ancestors('causes', reflexive=True)
    assert 'causes' not in toolkit.get_ancestors('causes', reflexive=False)
    assert 'biolink:causes' in toolkit.get_ancestors('causes', reflexive=True, formatted=True)
    assert GENOMIC_ENTITY in toolkit.get_ancestors('gene')
    assert GENOMIC_ENTITY not in toolkit.get_ancestors(BIOLOGICAL_ENTITY)
    assert GENOMIC_ENTITY in toolkit.get_ancestors(GENOMIC_ENTITY, reflexive=True)
    assert GENOMIC_ENTITY not in toolkit.get_ancestors(GENOMIC_ENTITY, reflexive=False)


def test_descendants(toolkit):
    assert 'gene' in toolkit.get_descendants(GENE_OR_GENE_PRODUCT)
    assert MOLECULAR_ACTIVITY in toolkit.get_descendants('occurrent')
    assert 'gene' not in toolkit.get_descendants('outcome')
    assert 'gene' in toolkit.get_descendants(NAMED_THING)
    assert 'causes' in toolkit.get_descendants(RELATED_TO)
    assert INTERACTS_WITH in toolkit.get_descendants(RELATED_TO)
    assert 'phenotypic feature' in toolkit.get_descendants(NAMED_THING)
    assert RELATED_TO not in toolkit.get_descendants(NAMED_THING)
    assert 'biolink:PhenotypicFeature' in toolkit.get_descendants(NAMED_THING, formatted=True)
    assert 'molecular activity_has output' not in toolkit.get_descendants(MOLECULAR_ACTIVITY, reflexive=True)
    assert 'molecular activity_has output' not in toolkit.get_descendants('has output', reflexive=True)
    assert 'gene' in toolkit.get_descendants('gene', reflexive=True)


def test_children(toolkit):
    assert 'causes' in toolkit.get_children('contributes to')
    assert 'physically interacts with' in toolkit.get_children(INTERACTS_WITH)
    assert 'gene' in toolkit.get_children(NUCLEIC_ACID_ENTITY)
    assert 'biolink:Gene' in toolkit.get_children(NUCLEIC_ACID_ENTITY, formatted=True)


def test_parent(toolkit):
    assert 'contributes to' in toolkit.get_parent('causes')
    assert INTERACTS_WITH in toolkit.get_parent('physically interacts with')
    assert NUCLEIC_ACID_ENTITY in toolkit.get_parent('gene')
    assert 'biolink:NucleicAcidEntity' in toolkit.get_parent('gene', formatted=True)


def test_mapping(toolkit):
    assert len(toolkit.get_all_elements_by_mapping('SO:0000704')) == 1
    assert 'gene' in toolkit.get_all_elements_by_mapping('SO:0000704')

    assert len(toolkit.get_all_elements_by_mapping('MONDO:0000001')) == 1
    assert 'disease' in toolkit.get_all_elements_by_mapping('MONDO:0000001')

    assert len(toolkit.get_all_elements_by_mapping('UPHENO:0000001')) == 1
    assert 'affects' in toolkit.get_all_elements_by_mapping('UPHENO:0000001')

    assert len(toolkit.get_all_elements_by_mapping('RO:0004033')) == 2
    assert 'negatively regulates' in toolkit.get_all_elements_by_mapping('RO:0004033')
    assert 'biolink:negatively_regulates' in toolkit.get_all_elements_by_mapping('RO:0004033', formatted=True)


def test_get_slot_domain(toolkit):
    assert BIOLOGICAL_ENTITY in toolkit.get_slot_domain('ameliorates')
    assert 'biological process or activity' in toolkit.get_slot_domain(ENABLED_BY)
    assert BIOLOGICAL_ENTITY in toolkit.get_slot_domain(ENABLED_BY, include_ancestors=True)
    assert 'biolink:BiologicalEntity' in toolkit.get_slot_domain(ENABLED_BY, include_ancestors=True, formatted=True)

    assert 'entity' in toolkit.get_slot_domain('name')
    assert 'entity' in toolkit.get_slot_domain('category')
    assert 'association' in toolkit.get_slot_domain('relation')


def test_get_slot_range(toolkit):
    assert 'disease or phenotypic feature' in toolkit.get_slot_range('treats')
    assert BIOLOGICAL_ENTITY in toolkit.get_slot_range('treats', include_ancestors=True)
    assert 'biolink:BiologicalEntity' in toolkit.get_slot_range('treats', include_ancestors=True, formatted=True)

    assert 'label type' in toolkit.get_slot_range('name')
    assert 'uriorcurie' in toolkit.get_slot_range('relation')
    assert 'metatype:Uriorcurie' in toolkit.get_slot_range('relation', formatted=True)


def test_get_all_slots_with_class_domain(toolkit):
    assert 'has drug' in toolkit.get_all_slots_with_class_domain('treatment')
    assert 'biolink:has_drug' in toolkit.get_all_slots_with_class_domain('treatment', formatted=True)


def test_get_all_slots_with_class_range(toolkit):
    assert 'in taxon' in toolkit.get_all_slots_with_class_range('organism taxon')
    assert 'biolink:in_taxon' in toolkit.get_all_slots_with_class_range('organism taxon', formatted=True)


def test_get_all_predicates_with_class_domain(toolkit):
    assert 'genetically interacts with' in toolkit.get_all_slots_with_class_domain('gene')
    assert INTERACTS_WITH in toolkit.get_all_slots_with_class_domain('gene', check_ancestors=True)
    assert 'biolink:interacts_with' in toolkit.get_all_slots_with_class_domain('gene', check_ancestors=True, formatted=True)

    assert 'in complex with' in toolkit.get_all_slots_with_class_domain(GENE_OR_GENE_PRODUCT)
    assert 'expressed in' in toolkit.get_all_slots_with_class_domain(GENE_OR_GENE_PRODUCT)


def test_get_all_predicates_with_class_range(toolkit):
    assert 'manifestation of' in toolkit.get_all_predicates_with_class_range('disease')
    assert 'disease has basis in' in toolkit.get_all_predicates_with_class_range('disease', check_ancestors=True)
    assert 'biolink:disease_has_basis_in' in toolkit.get_all_predicates_with_class_range('disease', check_ancestors=True, formatted=True)


def test_get_all_properties_with_class_domain(toolkit):
    assert 'category' in toolkit.get_all_properties_with_class_domain('entity')
    assert 'category' in toolkit.get_all_properties_with_class_domain('gene', check_ancestors=True)
    assert 'biolink:category' in toolkit.get_all_properties_with_class_domain('gene', check_ancestors=True, formatted=True)

    assert SUBJECT in toolkit.get_all_properties_with_class_domain('association')
    assert SUBJECT in toolkit.get_all_properties_with_class_domain('association', check_ancestors=True)
    assert 'biolink:subject' in toolkit.get_all_properties_with_class_domain('association', check_ancestors=True, formatted=True)


def test_get_all_properties_with_class_range(toolkit):
    assert 'has gene' in toolkit.get_all_properties_with_class_range('gene')
    assert SUBJECT in toolkit.get_all_properties_with_class_range('gene', check_ancestors=True)
    assert 'biolink:subject' in toolkit.get_all_properties_with_class_range('gene', check_ancestors=True, formatted=True)


def test_get_value_type_for_slot(toolkit):
    assert 'uriorcurie' in toolkit.get_value_type_for_slot(SUBJECT)
    assert 'uriorcurie' in toolkit.get_value_type_for_slot('object')
    assert 'string' in toolkit.get_value_type_for_slot('symbol')
    assert 'biolink:CategoryType' in toolkit.get_value_type_for_slot('category', formatted=True)




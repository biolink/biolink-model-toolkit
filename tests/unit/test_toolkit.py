from bmt import Toolkit


def test_get_all_elements():
    toolkit = Toolkit()
    elements = toolkit.get_all_elements()
    assert 'named thing' in elements
    assert 'association' in elements
    assert 'related to' in elements
    assert 'uriorcurie' in elements

    elements = toolkit.get_all_elements(formatted=True)
    assert 'biolink:NamedThing' in elements
    assert 'biolink:GeneToGeneAssociation' in elements
    assert 'biolink:related_to' in elements
    assert 'metatype:Uriorcurie' in elements
    assert 'biolink:FrequencyValue' in elements


def test_get_all_entities():
    toolkit = Toolkit()
    entities = toolkit.get_all_entities()
    assert 'named thing' in entities
    assert 'gene' in entities
    assert 'disease' in entities
    assert 'association' not in entities
    assert 'related to' not in entities

    entities = toolkit.get_all_entities(formatted=True)
    assert 'biolink:NamedThing' in entities
    assert 'biolink:Gene' in entities
    assert 'biolink:Disease' in entities


def test_get_all_associations():
    toolkit = Toolkit()
    associations = toolkit.get_all_associations()
    assert 'association' in associations
    assert 'gene to gene association' in associations
    assert 'named thing' not in associations

    associations = toolkit.get_all_associations(formatted=True)
    assert 'biolink:Association' in associations
    assert 'biolink:GeneToGeneAssociation' in associations


def test_get_all_node_properties():
    toolkit = Toolkit()
    properties = toolkit.get_all_node_properties()
    assert 'name' in properties
    assert 'category' in properties
    assert 'has gene' in properties

    properties = toolkit.get_all_node_properties(formatted=True)
    assert 'biolink:name' in properties
    assert 'biolink:category' in properties
    assert 'biolink:has_gene' in properties


def test_get_all_edge_properties():
    toolkit = Toolkit()
    properties = toolkit.get_all_edge_properties()
    assert 'subject' in properties
    assert 'object' in properties
    assert 'frequency qualifier' in properties

    properties = toolkit.get_all_edge_properties(formatted=True)
    assert 'biolink:subject' in properties
    assert 'biolink:object' in properties
    assert 'biolink:frequency_qualifier' in properties


def test_get_element():
    toolkit = Toolkit()
    gene = toolkit.get_element('gene')
    locus = toolkit.get_element('locus')
    assert gene == locus

    o = toolkit.get_element('drug intake')
    assert o and o.name == 'drug exposure'

    o = toolkit.get_element('molecular function')
    assert o and o.name == 'molecular activity'

    o = toolkit.get_element('RNA Product')
    assert o and o.name == 'RNA product'

    o = toolkit.get_element('rna product')
    assert o and o.name == 'RNA product'


def test_predicate():
    toolkit = Toolkit()
    assert not toolkit.is_predicate('named thing')
    assert not toolkit.is_predicate('gene')
    assert toolkit.is_predicate('causes')


def test_mixin():
    toolkit = Toolkit()
    assert not toolkit.is_mixin('named thing')
    assert toolkit.is_mixin('ontology class')
    assert not toolkit.is_mixin('this_does_not_exist')


def test_has_inverse():
    toolkit = Toolkit()
    assert not toolkit.has_inverse('contributor')
    assert toolkit.has_inverse('superclass of')
    assert not toolkit.has_inverse('this_does_not_exist')


def test_category():
    toolkit = Toolkit()
    assert toolkit.is_category('named thing')
    assert toolkit.is_category('gene')
    assert not toolkit.is_category('causes')
    assert not toolkit.is_category('affects')


def test_ancestors():
    toolkit = Toolkit()
    assert 'related to' in toolkit.get_ancestors('causes')
    assert 'biolink:related_to' in toolkit.get_ancestors('causes', formatted=True)

    assert 'named thing' in toolkit.get_ancestors('gene')
    assert 'biolink:NamedThing' in toolkit.get_ancestors('gene', formatted=True)

    assert 'causes' in toolkit.get_ancestors('causes')
    assert 'causes' in toolkit.get_ancestors('causes', reflexive=True)
    assert 'causes' not in toolkit.get_ancestors('causes', reflexive=False)
    assert 'biolink:causes' in toolkit.get_ancestors('causes', reflexive=True, formatted=True)

    assert 'drug exposure' in toolkit.get_ancestors('drug intake', reflexive=True)


def test_descendants():
    toolkit = Toolkit()
    assert 'causes' in toolkit.get_descendants('related to')
    assert 'interacts with' in toolkit.get_descendants('related to')
    assert 'gene' in toolkit.get_descendants('named thing')
    assert 'phenotypic feature' in toolkit.get_descendants('named thing')
    assert 'biolink:PhenotypicFeature' in toolkit.get_descendants('named thing', formatted=True)

    assert 'genomic entity' in toolkit.get_ancestors('genomic entity')
    assert 'genomic entity' in toolkit.get_ancestors('genomic entity', reflexive=True)
    assert 'genomic entity' not in toolkit.get_ancestors('genomic entity', reflexive=False)
    assert 'biolink:GenomicEntity' in toolkit.get_ancestors('gene', formatted=True)

    assert 'gross anatomical structure' in toolkit.get_ancestors('tissue', reflexive=True)
    assert 'molecular activity_has output' not in toolkit.get_descendants('molecular activity', reflexive=True)
    assert 'molecular activity_has output' not in toolkit.get_descendants('has output', reflexive=True)

    assert 'gene' in toolkit.get_descendants('gene', reflexive=True)


def test_children():
    toolkit = Toolkit()
    assert 'causes' in toolkit.get_children('contributes to')
    assert 'physically interacts with' in toolkit.get_children('interacts with')
    assert 'gene' in toolkit.get_children('genomic entity')
    assert 'biolink:Gene' in toolkit.get_children('genomic entity', formatted=True)


def test_parent():
    toolkit = Toolkit()
    assert 'contributes to' in toolkit.get_parent('causes')
    assert 'interacts with' in toolkit.get_parent('physically interacts with')
    assert 'genomic entity' in toolkit.get_parent('gene')
    assert 'biolink:GenomicEntity' in toolkit.get_parent('gene', formatted=True)


def test_mapping():
    toolkit = Toolkit()
    assert len(toolkit.get_all_elements_by_mapping('SO:0000704')) == 1
    assert 'gene' in toolkit.get_all_elements_by_mapping('SO:0000704')

    assert len(toolkit.get_all_elements_by_mapping('MONDO:0000001')) == 1
    assert 'disease' in toolkit.get_all_elements_by_mapping('MONDO:0000001')

    assert len(toolkit.get_all_elements_by_mapping('UPHENO:0000001')) == 1
    assert 'affects' in toolkit.get_all_elements_by_mapping('UPHENO:0000001')

    assert len(toolkit.get_all_elements_by_mapping('RO:0004033')) == 1
    assert 'negatively regulates' in toolkit.get_all_elements_by_mapping('RO:0004033')
    assert 'biolink:negatively_regulates' in toolkit.get_all_elements_by_mapping('RO:0004033', formatted=True)


def test_get_slot_domain():
    toolkit = Toolkit()
    assert 'biological entity' in toolkit.get_slot_domain('ameliorates')
    assert 'biological process or activity' in toolkit.get_slot_domain('enabled by')
    assert 'biological entity' in toolkit.get_slot_domain('enabled by', include_ancestors=True)
    assert 'biolink:BiologicalEntity' in toolkit.get_slot_domain('enabled by', include_ancestors=True, formatted=True)

    assert 'entity' in toolkit.get_slot_domain('name')
    assert 'entity' in toolkit.get_slot_domain('category')
    assert 'association' in toolkit.get_slot_domain('relation')


def test_get_slot_range():
    toolkit = Toolkit()
    assert 'disease or phenotypic feature' in toolkit.get_slot_range('treats')
    assert 'biological entity' in toolkit.get_slot_range('treats', include_ancestors=True)
    assert 'biolink:BiologicalEntity' in toolkit.get_slot_range('treats', include_ancestors=True, formatted=True)

    assert 'label type' in toolkit.get_slot_range('name')
    assert 'uriorcurie' in toolkit.get_slot_range('relation')
    assert 'metatype:Uriorcurie' in toolkit.get_slot_range('relation', formatted=True)


def test_get_all_slots_with_class_domain():
    toolkit = Toolkit()
    assert 'has drug' in toolkit.get_all_slots_with_class_domain('treatment')
    assert 'biolink:has_drug' in toolkit.get_all_slots_with_class_domain('treatment', formatted=True)


def test_get_all_slots_with_class_range():
    toolkit = Toolkit()
    assert 'treated by' in toolkit.get_all_slots_with_class_range('treatment')
    assert 'biolink:treated_by' in toolkit.get_all_slots_with_class_range('treatment', formatted=True)


def test_get_all_predicates_with_class_domain():
    toolkit = Toolkit()
    assert 'genetically interacts with' in toolkit.get_all_slots_with_class_domain('gene')
    assert 'interacts with' in toolkit.get_all_slots_with_class_domain('gene', check_ancestors=True)
    assert 'biolink:interacts_with' in toolkit.get_all_slots_with_class_domain('gene', check_ancestors=True, formatted=True)

    assert 'in complex with' in toolkit.get_all_slots_with_class_domain('gene or gene product')
    assert 'expressed in' in toolkit.get_all_slots_with_class_domain('gene or gene product')


def test_get_all_predicates_with_class_range():
    toolkit = Toolkit()
    assert 'manifestation of' in toolkit.get_all_predicates_with_class_range('disease')
    assert 'disease has basis in' in toolkit.get_all_predicates_with_class_range('disease', check_ancestors=True)
    assert 'biolink:disease_has_basis_in' in toolkit.get_all_predicates_with_class_range('disease', check_ancestors=True, formatted=True)


def test_get_all_properties_with_class_domain():
    toolkit = Toolkit()
    assert 'category' in toolkit.get_all_properties_with_class_domain('entity')
    assert 'category' in toolkit.get_all_properties_with_class_domain('gene', check_ancestors=True)
    assert 'biolink:category' in toolkit.get_all_properties_with_class_domain('gene', check_ancestors=True, formatted=True)

    assert 'subject' in toolkit.get_all_properties_with_class_domain('association')
    assert 'subject' in toolkit.get_all_properties_with_class_domain('association', check_ancestors=True)
    assert 'biolink:subject' in toolkit.get_all_properties_with_class_domain('association', check_ancestors=True, formatted=True)


def test_get_all_properties_with_class_range():
    toolkit = Toolkit()
    assert 'has gene' in toolkit.get_all_properties_with_class_range('gene')
    assert 'subject' in toolkit.get_all_properties_with_class_range('gene', check_ancestors=True)
    assert 'biolink:subject' in toolkit.get_all_properties_with_class_range('gene', check_ancestors=True, formatted=True)


def test_get_value_type_for_slot():
    toolkit = Toolkit()
    assert 'uriorcurie' in toolkit.get_value_type_for_slot('subject')
    assert 'uriorcurie' in toolkit.get_value_type_for_slot('object')
    assert 'string' in toolkit.get_value_type_for_slot('symbol')
    assert 'biolink:CategoryType' in toolkit.get_value_type_for_slot('category', formatted=True)




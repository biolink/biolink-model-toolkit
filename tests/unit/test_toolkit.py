import sys
from typing import Optional, List, Dict

import pytest
from linkml_runtime.linkml_model import Element

from bmt import Toolkit
from bmt.toolkit import LATEST_BIOLINK_RELEASE


@pytest.fixture(scope="module")
def toolkit():
    return Toolkit()


ASSOCIATION = "association"
BIOLOGICAL_ENTITY = "biological entity"
BIOLOGICAL_ENTITY_CURIE = "biolink:BiologicalEntity"
SUBJECT_CURIE = "biolink:subject"
RELATED_TO_CURIE = "biolink:related_to"
NODE_PROPERTY = 'node property'
SYNONYM = "synonym"
ASSOCIATION_SLOT = "association slot"
HAS_POPULATION_CONTEXT = "population context qualifier"
CAUSES = "causes"
AFFECTS = "affects"
AFFECTS_CURIE = "biolink:affects"
ENABLED_BY = "enabled by"
REGULATES = "regulates"
REGULATES_CURIE = "biolink:regulates"
REGULATED_BY = "regulated by"
REGULATED_BY_CURIE = "biolink:regulated_by"
TREATS = "treats"
TREATS_CURIE = "biolink:treats"
TREATED_BY = "treated by"
TREATED_BY_CURIE = "biolink:treated_by"

ENTITY = "entity"
ENTITY_CURIE = "biolink:Entity"
CHEMICAL_ENTITY = "chemical entity"
CHEMICAL_ENTITY_CURIE = "biolink:ChemicalEntity"
GENE = "gene"
GENE_CURIE = "biolink:Gene"
GENE_OR_GENE_PRODUCT = "gene or gene product"
GENE_OR_GENE_PRODUCT_CURIE = "biolink:GeneOrGeneProduct"
GENOMIC_ENTITY = "genomic entity"
GENOMIC_ENTITY_CURIE = "biolink:GenomicEntity"
INTERACTS_WITH = "interacts with"
MOLECULAR_ACTIVITY = "molecular activity"
NUCLEIC_ACID_ENTITY = "nucleic acid entity"
NAMED_THING = "named thing"
NAMED_THING_CURIE = "biolink:NamedThing"
ORGANISM_TAXON = "organism taxon"
PHENOTYPIC_FEATURE = "phenotypic feature"
RELATED_TO = "related to"
SUBJECT = "subject"
THING_WITH_TAXON = "thing with taxon"
TREATMENT = "treatment"
ACTIVE_IN = "active in"
HAS_ACTIVE_COMPONENT = "has active component"

# aspect qualifier is abstract so not really a valid qualifier
ASPECT_QUALIFIER_NAME = "aspect qualifier"

ANATOMICAL_CONTEXT_QUALIFIER_NAME = "anatomical context qualifier"
ANATOMICAL_CONTEXT_QUALIFIER_CURIE = "biolink:anatomical_context_qualifier"
ANATOMICAL_CONTEXT_QUALIFIER_ENUM_NAME = "AnatomicalContextQualifierEnum"
ANATOMICAL_CONTEXT_QUALIFIER_ENUM_CURIE = "biolink:AnatomicalContextQualifierEnum"

SUBJECT_DIRECTION_QUALIFIER_NAME = "subject direction qualifier"
SUBJECT_DIRECTION_QUALIFIER_CURIE = "biolink:subject_direction_qualifier"
DIRECTION_QUALIFIER_ENUM_NAME = "DirectionQualifierEnum"
DIRECTION_QUALIFIER_ENUM_CURIE = "biolink:DirectionQualifierEnum"

SPECIES_CONTEXT_QUALIFIER_NAME = "species context qualifier"
SPECIES_CONTEXT_QUALIFIER_CURIE = "biolink:species_context_qualifier"

# 'catalyst qualifier' has a mixin range 'macromolecular machine mixin'
CATALYST_QUALIFIER_NAME = "catalyst qualifier"
CATALYST_QUALIFIER_CURIE = "biolink:catalyst_qualifier"

SUBJECT_ASPECT_QUALIFIER_NAME = "subject aspect qualifier"
SUBJECT_ASPECT_QUALIFIER_CURIE = "biolink:subject_aspect_qualifier"
SUBJECT_ASPECT_QUALIFIER_SAMPLE_VALUE = "synthesis"

# 'qualified predicate' is a qualifier use case in a class of its own
QUALIFIED_PREDICATE_NAME = "qualified predicate"
QUALIFIED_PREDICATE_CURIE = "biolink:qualified_predicate"
QUALIFIED_PREDICATE_SAMPLE_VALUE = "causes"


def test_get_model_version(toolkit):
    version = toolkit.get_model_version()
    assert version == LATEST_BIOLINK_RELEASE


def test_warnings(toolkit):

    # only certain contexts are legitimate
    with pytest.raises(AssertionError):
        toolkit._format_warning_msg(context="invalid-context", identifiers={"1", "2", "3"})

    identifier = "HGNC:1234"
    context = "get_associations_subject_category"
    toolkit.warning(context=context, identifier=identifier)
    warnings: str = toolkit.dump_warnings()
    assert warnings.endswith(
        "get_associations_subject_category | "
        "Could not find subject category elements:\n\t'HGNC:1234'\n"
        "within the current Biolink Model release?\n\n"
    )

    toolkit.clear_warnings()
    warnings = toolkit.dump_warnings()
    assert warnings == ""

    # check the unit test console for a display of the following messages
    context = "get_associations_object_category"
    toolkit.warning(context=context, identifier="biolink:NotACategory")
    toolkit.warning(context=context, identifier="NCBIGene:1010")

    context = "get_element_by_prefix_missing_element"
    toolkit.warning(context=context, identifier="foo:bar")

    context = "get_associations_missing_association"
    toolkit.warning(context=context, identifier="biolink:NotAnAssociation")

    print("\n\n"+toolkit.dump_warnings(), file=sys.stderr)


def test_sv(toolkit):
    v = toolkit.view
    ancs = v.slot_ancestors('broad match')
    print(ancs)
    assert 'related to' in ancs


def test_get_denormalized_association_slots(toolkit):
    annotations = toolkit.get_denormalized_association_slots(formatted=True)
    print(annotations)
    assert "biolink:subject_closure" in annotations
    assert "gene" not in annotations
    annotations = toolkit.get_denormalized_association_slots(formatted=False)
    assert "subject closure" in annotations
    assert "gene" not in annotations


def test_get_id_prefixes(toolkit):
    tclass = toolkit.get_element(GENE_CURIE)
    assert tclass.class_uri == GENE_CURIE


def test_validate_edge(toolkit):
    subject = CHEMICAL_ENTITY_CURIE
    predicate = AFFECTS_CURIE
    p_object = GENE_CURIE
    assert toolkit.validate_edge(subject, predicate, p_object, ancestors=True)


def test_mixin_validate_edge(toolkit):
    subject = GENOMIC_ENTITY_CURIE
    predicate = "biolink:coexists_with"
    p_object = "biolink:SmallMolecule"
    assert toolkit.validate_edge(subject, predicate, p_object, ancestors=True)


def test_not_valid_edge(toolkit):
    subject = NAMED_THING_CURIE
    predicate = "biolink:has_target"
    p_object = GENE_CURIE
    assert not toolkit.validate_edge(subject, predicate, p_object, ancestors=True)


def test_get_element_via_alias(toolkit):
    el = toolkit.get_element('definition')
    pred_alias = toolkit.get_element("biolink:realized_in_response_to")
    print(pred_alias)
    ameliorates_aliase = toolkit.get_element("biolink:ameliorates")
    assert ameliorates_aliase.name == "ameliorates condition"
    assert pred_alias.name == "caused by"
    assert el.name == 'description'


def test_predicate_map(toolkit):
    mp: Dict[str, str] = toolkit.get_predicate_mapping("augments")
    assert mp.get("biolink:object_aspect_qualifier") == 'activity or abundance'


def test_rna(toolkit):
    assert 'molecular entity' in toolkit.get_descendants(ENTITY_CURIE)
    assert 'microRNA' in toolkit.get_descendants(ENTITY_CURIE)
    assert 'biolink:MicroRNA' in toolkit.get_descendants(ENTITY_CURIE, formatted=True)


def test_get_element_by_mapping(toolkit):
    element_name = toolkit.get_element_by_mapping("RO:0003303")
    assert element_name == "causes"


def test_get_element_by_prefix(toolkit):
    elements = toolkit.get_element_by_prefix("UBERON:1234")
    assert "anatomical entity" in elements

    elements = toolkit.get_element_by_prefix("GO:1234")
    assert "molecular activity" in elements

    elements = toolkit.get_element_by_prefix("TEST:1234")
    assert "anatomical entity" not in elements

    elements = toolkit.get_element_by_prefix("EDAM-DATA:123345")
    assert "attribute" in elements

    elements = toolkit.get_element_by_prefix("BSPO:123345")
    assert "original predicate" in elements


def test_get_all_elements(toolkit):
    elements = toolkit.get_all_elements()
    assert NAMED_THING in elements
    assert ASSOCIATION in elements
    assert RELATED_TO in elements
    assert "uriorcurie" in elements
    assert "thing does not exist" not in elements

    elements = toolkit.get_all_elements(formatted=True)
    assert "biolink:ThingDoesNotExist" not in elements
    assert NAMED_THING_CURIE in elements
    assert "biolink:GeneToGeneAssociation" in elements
    assert RELATED_TO_CURIE in elements
    assert "metatype:Uriorcurie" in elements
    assert "biolink:FrequencyValue" in elements


def test_get_all_entities(toolkit):
    entities = toolkit.get_all_entities()
    assert NAMED_THING in entities
    assert GENE in entities
    assert "disease" in entities
    assert ASSOCIATION not in entities
    assert RELATED_TO not in entities

    entities = toolkit.get_all_entities(formatted=True)
    assert NAMED_THING_CURIE in entities
    assert GENE_CURIE in entities
    assert "biolink:Disease" in entities
    assert "biolink:Association" not in entities


def test_get_all_associations(toolkit):
    associations = toolkit.get_all_associations()
    assert ASSOCIATION in associations
    assert "gene to gene association" in associations
    assert NAMED_THING not in associations

    associations = toolkit.get_all_associations(formatted=True)
    assert "biolink:Association" in associations
    assert "biolink:GeneToGeneAssociation" in associations
    assert NAMED_THING_CURIE not in associations


def test_filter_values_on_slot(toolkit):
    # as our test data, we take an extant associations from Biolink release 3.5.4
    as_element: Optional[Element] = toolkit.get_element("chemical affects gene association")
    slot_usage = as_element["slot_usage"]

    subject_definition = slot_usage["subject"]  # "gene or gene product"
    assert toolkit.filter_values_on_slot(
        slot_values=[
            GENE_OR_GENE_PRODUCT_CURIE,
            "biolink:MolecularEntity",
            "biolink:ChemicalMixture",
            "biolink:SmallMolecule"
        ],
        definition=subject_definition,
        field="range"
    )
    assert not toolkit.filter_values_on_slot(
        slot_values=["biolink:ClinicalEntity"],
        definition=subject_definition,
        field="range"
    )
    assert toolkit.filter_values_on_slot(
        slot_values=[
            "gene or gene product",
            "molecular entity",
            "chemical mixture",
            "small molecule"
        ],
        definition=subject_definition,
        field="range",
        formatted=False
    )

    predicate_definition = slot_usage["predicate"]  # "affects"
    assert toolkit.filter_values_on_slot(
        slot_values=[AFFECTS_CURIE, REGULATES_CURIE],
        definition=predicate_definition,
        field="subproperty_of"
    )
    assert not toolkit.filter_values_on_slot(
        slot_values=["biolink:diagnoses"],
        definition=predicate_definition,
        field="subproperty_of"
    )


@pytest.mark.parametrize(
    "assoc_name,subj_cats,predicates,obj_cats,formatted,outcome",
    [
        (  # query 0 - empty constraints - automatic pass
            "association",  # assoc_name
            [],    # subj_cats
            [],    # predicates
            [],    # obj_cats
            True,  # formatted
            True   # outcome == pass
        ),
        (  # query 1 - unformatted inputs, valid matches to given association
            "chemical entity assesses named thing association",
            ["chemical entity"],
            ["assesses"],
            ["named thing"],
            False,  # don't use CURIEs
            True   # outcome == pass
        ),
        (  # query 2 - CURIE formatted inputs, valid matches to given association
            "chemical entity assesses named thing association",
            ["biolink:ChemicalEntity"],
            ["biolink:assesses"],
            ["biolink:NamedThing"],
            True,
            True   # outcome == pass
        ),
        (  # query 3 - constraints matching another specific association
            "chemical entity assesses named thing association",
            ["biolink:ChemicalEntity"],
            ["biolink:assesses"],
            ["biolink:NamedThing"],
            True,
            True   # outcome == pass
        ),
        (   # query 4 - predicate constraint is empty, so it matches...
            "gene to gene association",
            ["biolink:GeneOrGeneProduct"],
            [],
            ["biolink:GeneOrGeneProduct"],
            True,
            True   # outcome == pass
        ),
        (   # query 5 - ...but if I do give it a predicate, since there is no
            #           slot_usage for 'predicate', everything still matches
            "gene to gene association",
            ["biolink:GeneOrGeneProduct"],
            ["biolink:related_to"],
            ["biolink:GeneOrGeneProduct"],
            True,
            True   # outcome == pass
        ),
        (   # query 6 - the association has the specific predicate expectation but needs
            #           to inherit its 'subject' and 'object' from an ancestral class
            "gene to gene coexpression association",
            ["biolink:GeneOrGeneProduct"],
            ["biolink:coexpressed_with"],
            ["biolink:GeneOrGeneProduct"],
            True,
            True   # outcome == fail
        ),
        (   # query 7 - another specific matching association
            "pairwise molecular interaction",
            ["molecular entity"],
            ["interacts with"],
            ["molecular entity"],
            False,
            True   # outcome == pass
        ),
        (   # query 8 - mixin doesn't have a suitable 'object' constraint, so it cannot be selected
            "chemical to entity association mixin",
            ["chemical entity or gene or gene product"],
            ["affects"],
            ["named thing"],
            False,
            False   # outcome == fail
        ),
        (   # query 9 - this ought to work with any predicate 'cuz the slot_usage has a 'predicate'
            #           property, no 'subproperty_of' constraint, and the 'object' no 'range', but
            #           at least, both slots have a 'description' field.
            "organism taxon to environment association",
            ["organism taxon"],
            ["affects"],
            ["environmental context"],
            False,
            True   # outcome == pass
        ),
        (  # query 10 - a missing 'predicate' property in the 'slot_usage' field simply lets all predicates match
            "exon to transcript relationship",
            ["exon"],
            ["part of"],
            ["transcript"],
            False,
            True   # outcome == pass
        ),
        (  # query 11 - subject (and object) categories don't match the specified range (or its descendants)
            "exon to transcript relationship",
            ["molecular activity"],
            ["affects"],
            ["molecular activity"],
            False,
            False   # outcome == fail
        )
    ]
)
def test_match_association(
        toolkit,
        assoc_name: str,
        subj_cats: List[str],
        predicates: List[str],
        obj_cats: List[str],
        formatted: bool,
        outcome: bool
):
    association: Element = toolkit.get_element(assoc_name)
    assert toolkit.match_association(association, subj_cats, predicates, obj_cats, formatted) is outcome


def test_get_associations_without_parameters(toolkit):
    # Empty argument versions of get_associations()
    # are equivalent to get_all_associations()
    associations = toolkit.get_associations()
    assert ASSOCIATION in associations
    assert "gene to gene association" in associations
    assert NAMED_THING not in associations

    associations = toolkit.get_associations(formatted=True)
    assert "biolink:Association" in associations
    assert "biolink:GeneToGeneAssociation" in associations
    assert NAMED_THING_CURIE not in associations


@pytest.mark.parametrize(
    "subject_categories,predicates,object_categories,match_inverses,contains,does_not_contain",
    [
        (   # Q0 - all parameters None => same (formatted) result as get_all_associations()
            None,   # subject_categories: Optional[List[str]],
            None,   # predicates: Optional[List[str]],
            None,   # object_categories: Optional[List[str]],
            True,   # match_inverses
            [
                # diverse set of all the matching associations
                "biolink:Association",
                "biolink:ContributorAssociation",
                "biolink:GenotypeToGeneAssociation",
                "biolink:GeneToDiseaseAssociation",
                "biolink:ExposureEventToOutcomeAssociation",
                "biolink:DiseaseOrPhenotypicFeatureToLocationAssociation"
            ],      # contains: List[str]
            []      # does_not_contain: List[str] - should be empty set in the unit test case
        ),
        (   # Q1 - subject_categories set to a value and all other parameters == None
            [GENE_CURIE],
            None,
            None,
            True,   # match_inverses
            [
                "biolink:GeneToGeneAssociation",
                "biolink:GeneToDiseaseAssociation"
            ],
            [
                "biolink:Association",
                "biolink:ContributorAssociation",
                "biolink:ExposureEventToOutcomeAssociation"
            ]
        ),
        (   # Q2 - subject_categories, object_categories given non-None values and predicates == None
            #   gene to disease association:
            #     is_a: gene to disease or phenotypic feature association
            #     ...
            #     mixins:
            #       - entity to disease association mixin
            #       - gene to entity association mixin
            #     slot_usage:
            #       subject:
            #         range: gene or gene product
            #         description: >-
            #           gene in which variation is correlated with the disease,
            #           may be protective or causative or associative, or as a model
            #       object:
            #         range: disease
            [GENE_CURIE],
            None,
            ["biolink:Disease"],
            True,   # match_inverses
            ["biolink:GeneToDiseaseAssociation"],
            [
                "biolink:Association",
                "biolink:ContributorAssociation",
                "biolink:GenotypeToGeneAssociation",
                "biolink:ExposureEventToOutcomeAssociation"
            ]
        ),
        (   # Q3 - subject_categories, predicates and object_categories given non-None values
            #   druggable gene to disease association:
            #     is_a: gene to disease association
            #     slot_usage:
            #       subject:
            #         range: gene or gene product
            #         description: >-
            #           gene in which variation is correlated with the disease
            #           in a protective manner, or if the product produced
            #           by the gene can be targeted by a small molecule and
            #           this leads to a protective or improving disease state.
            #       predicate:
            #         subproperty_of: target for
            #       has evidence:
            #         range: DruggableGeneCategoryEnum
            #     defining_slots:
            #       - subject
            #       - object
            #       - predicate
            #     mixins:
            #       - entity to disease association mixin  # Note: the 'object' slot_usage is defined in this mixin
            #       - gene to entity association mixin
            [GENE_CURIE],
            ["biolink:target_for"],
            ["biolink:Disease"],
            True,   # match_inverses
            ["biolink:DruggableGeneToDiseaseAssociation"],
            [
                "biolink:Association",
                "biolink:ContributorAssociation",
                "biolink:GenotypeToGeneAssociation",
                "biolink:GeneToDiseaseAssociation",
                "biolink:ExposureEventToOutcomeAssociation"
            ]
        ),
        (   # Q4 - Check if "biolink:Gene -- biolink:regulates -> biolink:Gene"
            #      matches expected biolink:Association subclasses
            [GENE_CURIE],
            [REGULATES_CURIE],
            [GENE_CURIE],
            True,   # match_inverses
            [
                'biolink:ChemicalEntityOrGeneOrGeneProductRegulatesGeneAssociation'
            ],
            [
                "biolink:Association",
                "biolink:GeneToDiseaseOrPhenotypicFeatureAssociation",
                "biolink:ChemicalAffectsGeneAssociation",
                "biolink:ChemicalGeneInteractionAssociation"
            ]
        ),
        (   # Q5 - Check if "biolink:Gene -- biolink:affects -> biolink:SmallMolecule" - no match
            [GENE_CURIE],
            [AFFECTS_CURIE],
            ["biolink:SmallMolecule"],
            True,   # match_inverses, but as of Biolink Model release 3.5.4, there is no inverse for this SPO
            [],
            [
                "biolink:Association",

                # inverse of 'affects' is 'affected_by' hence is
                # not a match to the predicate subproperty_of
                # this otherwise appropriate association
                "biolink:ChemicalAffectsGeneAssociation"
            ]
        ),
        (   # Q6 - Check if "biolink:Gene -- biolink:affected_by -> biolink:SmallMolecule" - inverse match
            [GENE_CURIE],
            ["biolink:affected_by"],
            ["biolink:SmallMolecule"],
            True,   # match_inverses
            [
                # inverse of 'affected_by' is 'affects', which DOES match the predicate
                # 'subproperty_of' the inverse ChemicalAffectsGeneAssociation association
                "biolink:ChemicalAffectsGeneAssociation"
            ],
            [
                "biolink:Association"
            ]
        ),
        (   # Q7 - Check if "biolink:Gene -- biolink:affects -> biolink:SmallMolecule" - no direct match
            [GENE_CURIE],
            [AFFECTS_CURIE],
            ["biolink:SmallMolecule"],
            False,   # match_inverses
            [],  # as of Biolink Model release 3.5.4, there is no direct match for this set of SPO parameters
            [
                "biolink:Association",
                "biolink:ChemicalAffectsGeneAssociation"
            ]
        ),
        (   # Q8 - Check if "biolink:Gene -- biolink:affected -> biolink:SmallMolecule" - still no direct match
            [GENE_CURIE],
            ["biolink:affected_by"],
            ["biolink:SmallMolecule"],
            False,   # match_inverses
            [],  # as of Biolink Model release 3.5.4, there is no direct match for this set of SPO parameters
            [
                "biolink:Association",
                "biolink:ChemicalAffectsGeneAssociation"
            ]
        ),
        (   # Q9 - Check if "biolink:Gene -- biolink:affected -> biolink:SmallMolecule" - still no direct match
            [GENE_OR_GENE_PRODUCT],
            ["biolink:affected_by"],
            ["biolink:ChemicalEntity"],
            False,   # match_inverses
            [],  # as of Biolink Model release 3.5.4, there is no direct match for this set of SPO parameters
            [
                "biolink:Association",
                "biolink:ChemicalAffectsGeneAssociation"
            ]
        ),
        (   # Q10 - Check if "biolink:not-a-category -- biolink:affects -> biolink:SmallMolecule" -
            #      has no direct match (and issues a log warning?)
            ["biolink:not-a-category"],
            [AFFECTS_CURIE],
            ["biolink:ChemicalEntity"],
            False,   # match_inverses
            [],  # there is no direct match for a nonsense subject category
            ["biolink:Association"]
        ),
        (   # Q11 - Check if "biolink:Gene -- biolink:not-a-predicate -> biolink:SmallMolecule" -
            #      has no direct match (and issues a log warning?)
            [GENE_CURIE],
            ["biolink:not-a-predicate"],
            ["biolink:ChemicalEntity"],
            False,   # match_inverses
            [],  # there is no direct match for a nonsense predicate
            ["biolink:Association"]
        ),
        (   # Q12 - Check if "biolink:Gene -- biolink:affects -> biolink:not-a-category" -
            #       has no direct match (and issues a log warning?)
            [GENE_CURIE],
            [AFFECTS_CURIE],
            ["biolink:not-a-category"],
            False,   # match_inverses
            [],  # there is no direct match for a nonsense object category
            ["biolink:Association"]
        ),
        (   # Q13 - Check if "biolink:Gene -- biolink:regulated_by -> biolink:ChemicalEntity"
            #       should match the inverse (# )sneaking in unformatted class/slot names (should still work!))
            [GENE_CURIE],
            [REGULATED_BY],
            [CHEMICAL_ENTITY],
            True,   # match_inverses
            # this should be detected without any messaging
            ["biolink:ChemicalEntityOrGeneOrGeneProductRegulatesGeneAssociation"],
            []
        )
    ]
)
def test_get_associations_with_parameters(
        toolkit,
        subject_categories: Optional[List[str]],
        predicates: Optional[List[str]],
        object_categories: Optional[List[str]],
        match_inverses: bool,
        contains: List[str],
        does_not_contain: List[str]
):
    associations = toolkit.get_associations(
        subject_categories=subject_categories,
        predicates=predicates,
        object_categories=object_categories,
        match_inverses=match_inverses,
        # we don't bother testing the 'format' flag simply in confidence
        # that the associated code is already well tested in other contexts
        formatted=True
    )
    assert all([entry in associations for entry in contains])
    assert not any([entry in associations for entry in does_not_contain])


def test_get_associations_gene_to_chemical(toolkit):
    associations = toolkit.get_associations(
        subject_categories=["biolink:ChemicalEntity"],
        predicates=[AFFECTS_CURIE],
        object_categories=["biolink:GeneOrGeneProduct"],
        # we don't bother testing the 'format' flag simply in confidence
        # that the associated code is already well tested in other contexts
        formatted=True
    )
    assert associations

    unformatted_associations = toolkit.get_associations(
        subject_categories=["chemical entity"],
        predicates=["affects"],
        object_categories=["gene or gene product"],
        formatted=True
    )

    assert unformatted_associations


def test_get_all_node_properties(toolkit):
    properties = toolkit.get_all_node_properties()
    assert "provided by" in properties
    assert "category" in properties
    assert "has gene" in properties
    assert RELATED_TO not in properties
    assert SUBJECT not in properties

    properties = toolkit.get_all_node_properties(formatted=True)
    assert "biolink:provided_by" in properties
    assert "biolink:category" in properties
    assert "biolink:has_gene" in properties
    assert SUBJECT_CURIE not in properties
    assert RELATED_TO_CURIE not in properties


def test_get_all_edge_properties(toolkit):
    properties = toolkit.get_all_edge_properties()
    assert SUBJECT in properties
    assert "object" in properties
    assert "frequency qualifier" in properties
    assert "not in the model" not in properties

    properties = toolkit.get_all_edge_properties(formatted=True)
    assert SUBJECT_CURIE in properties
    assert "biolink:object" in properties
    assert "biolink:frequency_qualifier" in properties


def test_get_element(toolkit):

    o = toolkit.get_element("drug intake")
    assert o and o.name == "drug exposure"

    o = toolkit.get_element("molecular function")
    assert o and o.name == MOLECULAR_ACTIVITY

    o = toolkit.get_element("molecular_function")
    assert o and o.name == MOLECULAR_ACTIVITY

    o = toolkit.get_element("cellular_component")
    assert o and o.name == "cellular component"

    o = toolkit.get_element("RNA Product")
    assert o and o.name == "RNA product"

    o = toolkit.get_element("rna product")
    assert o and o.name == "RNA product"


def test_get_enum_via_element(toolkit):
    association_element = toolkit.get_element("biolink:ChemicalAffectsGeneAssociation")
    qualifier_type = association_element["slot_usage"]["object aspect qualifier"]
    value_range = qualifier_type.range
    assert value_range == "GeneOrGeneProductOrChemicalEntityAspectEnum"


def test_is_node_property(toolkit):
    assert toolkit.is_node_property(NODE_PROPERTY)
    assert toolkit.is_node_property(SYNONYM)
    assert not toolkit.is_node_property(HAS_POPULATION_CONTEXT)
    assert not toolkit.is_node_property(CAUSES)
    assert not toolkit.is_node_property(GENE)


def test_is_association_slot(toolkit):
    assert toolkit.is_association_slot(ASSOCIATION_SLOT)
    assert toolkit.is_association_slot(HAS_POPULATION_CONTEXT)
    assert not toolkit.is_association_slot(SYNONYM)
    assert not toolkit.is_association_slot(CAUSES)
    assert not toolkit.is_association_slot(GENE)


def test_is_predicate(toolkit):
    assert toolkit.is_predicate(CAUSES)
    assert not toolkit.is_predicate(NAMED_THING)
    assert not toolkit.is_predicate(GENE)
    assert not toolkit.is_category(SYNONYM)
    assert not toolkit.is_category(HAS_POPULATION_CONTEXT)


def test_is_mixin(toolkit):
    assert not toolkit.is_mixin(NAMED_THING)
    assert toolkit.is_mixin("ontology class")
    assert not toolkit.is_mixin("this_does_not_exist")


def test_is_symmetric(toolkit):
    assert not toolkit.is_symmetric("")
    assert not toolkit.is_symmetric("this_predicate_does_not_exist")
    assert toolkit.is_symmetric(RELATED_TO)
    assert toolkit.is_symmetric(INTERACTS_WITH)
    assert not toolkit.is_symmetric(AFFECTS)


def test_is_translator_canonical_predicate(toolkit):
    assert toolkit.is_translator_canonical_predicate("studied to treat")
    assert not toolkit.is_translator_canonical_predicate("this_predicate_does_not_exist")
    assert not toolkit.is_translator_canonical_predicate("completed by")
    assert toolkit.is_translator_canonical_predicate(REGULATES)


def test_has_inverse(toolkit):
    assert toolkit.has_inverse("completed by")
    assert not toolkit.has_inverse("this_does_not_exist")

    # this next assertion reflects the fact that 'has_inverse' doesn't
    # detect the inverse of a canonical element (e.g. 'treats'),
    # even if the canonical is listed as the inverse of another
    # element ought to be considered its inverse (i.e. 'treated by')
    assert toolkit.has_inverse(TREATED_BY)
    assert not toolkit.has_inverse(TREATS)
    # ...works with Biolink CURIE
    assert toolkit.has_inverse(TREATED_BY_CURIE)
    # symmetric predicates are not also tagged with 'inverse'
    # so the following call also comes back empty-handed
    assert not toolkit.has_inverse(RELATED_TO)


def test_get_inverse(toolkit):
    assert toolkit.get_inverse(ACTIVE_IN) == HAS_ACTIVE_COMPONENT
    assert toolkit.get_inverse(HAS_ACTIVE_COMPONENT) == ACTIVE_IN
    sd = toolkit.get_element(ACTIVE_IN)
    assert toolkit.get_inverse(sd.name) == HAS_ACTIVE_COMPONENT
    # Unlike 'has_inverse' above, 'get_inverse' does discover the
    # conceptual inverse every time. Works fine with 'mixin' predicates.
    assert toolkit.get_inverse(TREATS) == TREATED_BY
    assert toolkit.get_inverse(TREATED_BY) == TREATS
    # But doesn't see symmetrical predicates?
    assert toolkit.get_inverse(RELATED_TO) != RELATED_TO


def test_get_get_inverse_predicate(toolkit):
    assert toolkit.get_inverse_predicate(ACTIVE_IN) == HAS_ACTIVE_COMPONENT
    assert toolkit.get_inverse_predicate(HAS_ACTIVE_COMPONENT) == ACTIVE_IN

    # ... however, this method DOES work with symmetric predicates
    assert toolkit.get_inverse_predicate(RELATED_TO) == RELATED_TO
    assert toolkit.get_inverse_predicate(RELATED_TO, formatted=True) == RELATED_TO_CURIE

    # ... and with mixin predicates too
    assert toolkit.get_inverse_predicate(TREATS) == TREATED_BY
    assert toolkit.get_inverse_predicate(TREATED_BY) == TREATS
    assert toolkit.get_inverse_predicate(TREATS, formatted=True) == TREATED_BY_CURIE
    assert toolkit.get_inverse_predicate(TREATED_BY, formatted=True) == TREATS_CURIE


def test_category(toolkit):
    assert toolkit.is_category(NAMED_THING)
    assert toolkit.is_category(GENE)
    assert not toolkit.is_category(CAUSES)
    assert not toolkit.is_category("affects")
    assert not toolkit.is_category(GENE_OR_GENE_PRODUCT)


def test_is_qualifier(toolkit):
    assert toolkit.is_qualifier(SUBJECT_DIRECTION_QUALIFIER_NAME)
    assert toolkit.is_qualifier(SUBJECT_DIRECTION_QUALIFIER_CURIE)
    assert not toolkit.is_qualifier(DIRECTION_QUALIFIER_ENUM_NAME)
    assert not toolkit.is_qualifier(NAMED_THING)
    assert not toolkit.is_qualifier(CAUSES)
    assert not toolkit.is_qualifier("affects")
    assert not toolkit.is_qualifier(GENE_OR_GENE_PRODUCT)


def test_is_enum(toolkit):
    assert toolkit.is_enum(DIRECTION_QUALIFIER_ENUM_NAME)
    assert not toolkit.is_enum(NAMED_THING)
    assert not toolkit.is_enum(CAUSES)
    assert not toolkit.is_enum("affects")
    assert not toolkit.is_enum(GENE_OR_GENE_PRODUCT)


def test_is_subproperty_of(toolkit):
    assert toolkit.is_subproperty_of("contributes to", "causes")
    assert toolkit.is_subproperty_of("similar to", "orthologous to")


@pytest.mark.parametrize(
    "qualifier_type_id,qualifier_value,associations,result",
    [
        # method called with empty arguments fails gracefully
        ("", "", None, False),                                # Q0
        (SUBJECT_DIRECTION_QUALIFIER_NAME, "", None, False),  # Q1
        ("", "upregulated", None, False),                     # Q2

        # 'aspect qualifier' is 'abstract', hence can't be instantiated (doesn't have a 'range')
        (ASPECT_QUALIFIER_NAME, "upregulated", None, False),  # Q3

        # qualifier with value drawn from enum 'permissible values'
        (SUBJECT_DIRECTION_QUALIFIER_NAME, "upregulated", None, True),    # Q4
        (SUBJECT_DIRECTION_QUALIFIER_CURIE, "upregulated", None, True),   # Q5 - CURIE accepted here too

        # *** Use case currently not supported: RO term is exact_match to 'upregulated' enum
        # (SUBJECT_DIRECTION_QUALIFIER_NAME, "RO:0002213", None, True),   # Qx -

        # qualifier with value drawn from concrete Biolink category identifier spaces
        (SPECIES_CONTEXT_QUALIFIER_NAME, "NCBITaxon:9606", None, True),   # Q6
        (SPECIES_CONTEXT_QUALIFIER_CURIE, "NCBITaxon:9606", None, True),  # Q7 - CURIE accepted here too

        # qualifier with value drawn from concrete Biolink category identifier spaces
        (SPECIES_CONTEXT_QUALIFIER_NAME, "NCBITaxon:9606", None, True),   # Q8
        (SPECIES_CONTEXT_QUALIFIER_CURIE, "NCBITaxon:9606", None, True),  # Q9 - CURIE accepted here too

        # *** Another currently unsupported use case...
        # 'catalyst qualifier' has a mixin range 'macromolecular machine mixin'
        # 'GO:0032991' is exact match to 'macromolecular complex' which has
        #   'macromolecular machine mixin' as a mixin and also has id_prefixes including GO, so...
        # (CATALYST_QUALIFIER_NAME, "GO:0032991", None, True), # Qxx
        # (CATALYST_QUALIFIER_CURIE, "GO:0032991", None, True), # Qxx - CURIE accepted here too

        # mis-matched qualifier values or value types
        (SUBJECT_DIRECTION_QUALIFIER_NAME, "UBERON:0001981", None, False),      # Q10
        (SPECIES_CONTEXT_QUALIFIER_NAME, "upregulated", None, False),           # Q11

        # 'object aspect qualifier' is a qualifier use case in a class of its own
        # Validation required a priori knowledge of the biolink:Association
        # subclass that constrains the semantics of the edge in question
        # e.g. biolink:GeneToDiseaseOrPhenotypicFeatureAssociation in Biolink Model 3.5.2
        (
            SUBJECT_ASPECT_QUALIFIER_NAME,
            SUBJECT_ASPECT_QUALIFIER_SAMPLE_VALUE,
            ["biolink:GeneToDiseaseOrPhenotypicFeatureAssociation"],
            True
        ),  # Q12
        (
            SUBJECT_ASPECT_QUALIFIER_CURIE,
            SUBJECT_ASPECT_QUALIFIER_SAMPLE_VALUE,
            ["biolink:GeneToDiseaseOrPhenotypicFeatureAssociation"],
            True
        ),  # Q13 - CURIE accepted here too

        # 'qualified predicate' is a qualifier use case in a class of its own
        # Validation required a priori knowledge of the biolink:Association
        # subclass that constrains the semantics of the edge in question
        # e.g. biolink:ChemicalAffectsGeneAssociation in Biolink Model 3.5.2
        (
            QUALIFIED_PREDICATE_NAME,
            QUALIFIED_PREDICATE_SAMPLE_VALUE,
            ["biolink:ChemicalAffectsGeneAssociation"],
            True
        ),  # Q14
        (
            QUALIFIED_PREDICATE_CURIE,
            QUALIFIED_PREDICATE_SAMPLE_VALUE,
            ["biolink:ChemicalAffectsGeneAssociation"],
            True
        ),  # Q15 - CURIE accepted here too
        (
            "biolink:object_aspect_qualifier",
            "activity_or_abundance",
            [
                'biolink:ChemicalGeneInteractionAssociation',
                'biolink:ChemicalAffectsGeneAssociation',
                'biolink:ChemicalEntityOrGeneOrGeneProductRegulatesGeneAssociation'
            ],
            # 'Gene--regulates->Gene' matches specified associations and from Biolink Model 3.5.3 onwards,
            # the 'biolink:ChemicalAffectsGeneAssociation' class defines 'slot_usage' for
            # 'biolink:object_aspect_qualifier' as 'GeneOrGeneProductOrChemicalEntityAspectEnum'
            # which contains the enum member value of 'activity_or_abundance', thus True test result
            True
        )
    ]
)
def test_validate_qualifier(
        toolkit,
        qualifier_type_id: str,
        qualifier_value: str,
        associations: Optional[List[str]],
        result: bool
):
    assert toolkit.validate_qualifier(
        qualifier_type_id=qualifier_type_id,
        qualifier_value=qualifier_value,
        associations=associations
    ) is result


def test_is_permissible_value_of_enum(toolkit):
    assert toolkit.is_permissible_value_of_enum(DIRECTION_QUALIFIER_ENUM_NAME, "upregulated")
    assert toolkit.is_permissible_value_of_enum(DIRECTION_QUALIFIER_ENUM_CURIE, "upregulated")


def test_ancestors(toolkit):
    assert RELATED_TO in toolkit.get_ancestors(CAUSES)
    a = toolkit.get_ancestors(GENE)
    ancs = [toolkit.get_element(ai)['class_uri'] for ai in a]
    assert NAMED_THING_CURIE in ancs

    assert "biolink:ChemicalEntityOrGeneOrGeneProduct" in toolkit.get_ancestors(
        GENE, formatted=True
    )
    assert GENOMIC_ENTITY_CURIE in toolkit.get_ancestors(GENE, formatted=True)
    assert RELATED_TO_CURIE in toolkit.get_ancestors(CAUSES, formatted=True)
    assert GENE_OR_GENE_PRODUCT_CURIE in toolkit.get_ancestors(GENE, formatted=True)
    assert GENE_OR_GENE_PRODUCT_CURIE not in toolkit.get_ancestors(
        GENE, formatted=True, mixin=False
    )
    assert NAMED_THING in toolkit.get_ancestors(GENE)
    assert GENE_OR_GENE_PRODUCT in toolkit.get_ancestors(GENE)
    assert GENE_OR_GENE_PRODUCT not in toolkit.get_ancestors(GENE, mixin=False)
    assert NAMED_THING_CURIE in toolkit.get_ancestors(GENE, formatted=True)
    assert "biological entity" in toolkit.get_ancestors(GENE)
    assert "transcript" not in toolkit.get_ancestors(GENE)
    assert CAUSES in toolkit.get_ancestors(CAUSES)
    assert CAUSES in toolkit.get_ancestors(CAUSES, reflexive=True)
    assert CAUSES not in toolkit.get_ancestors(CAUSES, reflexive=False)
    assert "biolink:causes" in toolkit.get_ancestors(
        CAUSES, reflexive=True, formatted=True
    )
    assert GENOMIC_ENTITY in toolkit.get_ancestors(GENE)
    assert GENOMIC_ENTITY not in toolkit.get_ancestors(BIOLOGICAL_ENTITY)
    assert GENOMIC_ENTITY in toolkit.get_ancestors(GENOMIC_ENTITY, reflexive=True)
    assert GENOMIC_ENTITY not in toolkit.get_ancestors(GENOMIC_ENTITY, reflexive=False)
    assert THING_WITH_TAXON not in toolkit.get_ancestors(
        PHENOTYPIC_FEATURE, mixin=False
    )
    assert THING_WITH_TAXON in toolkit.get_ancestors(PHENOTYPIC_FEATURE)

    assert GENE not in toolkit.get_ancestors(CHEMICAL_ENTITY_CURIE, reflexive=False)


def test_permissible_value_ancestors(toolkit):
    assert "increased" in toolkit.get_permissible_value_ancestors("upregulated", "DirectionQualifierEnum")
    assert "modified_form" in toolkit.get_permissible_value_ancestors(
        "snp_form", "ChemicalOrGeneOrGeneProductFormOrVariantEnum"
    )
    assert "increased" in toolkit.get_permissible_value_parent("upregulated", "DirectionQualifierEnum")
    assert "upregulated" in toolkit.get_permissible_value_children("increased", "DirectionQualifierEnum")
    assert "synthesis" in \
           toolkit.get_permissible_value_descendants(
               "activity_or_abundance",
               "GeneOrGeneProductOrChemicalEntityAspectEnum"
           )


def test_ancestors_for_kgx(toolkit):
    ancestors1 = toolkit.get_ancestors(PHENOTYPIC_FEATURE, formatted=True, mixin=False)
    assert ancestors1 is not None
    assert len(ancestors1) == 5
    ancestors2 = toolkit.get_ancestors(PHENOTYPIC_FEATURE, formatted=True)
    assert ancestors2 is not None
    assert len(ancestors2) == 6


def test_descendants(toolkit):
    assert GENE in toolkit.get_descendants(GENE_OR_GENE_PRODUCT)
    assert GENE not in toolkit.get_descendants(GENE_OR_GENE_PRODUCT, mixin=False)
    assert MOLECULAR_ACTIVITY in toolkit.get_descendants("occurrent")
    assert GENE not in toolkit.get_descendants("outcome")
    assert GENE in toolkit.get_descendants(NAMED_THING)
    assert CAUSES in toolkit.get_descendants(RELATED_TO)
    assert INTERACTS_WITH in toolkit.get_descendants(RELATED_TO)
    assert PHENOTYPIC_FEATURE in toolkit.get_descendants(NAMED_THING)
    assert RELATED_TO not in toolkit.get_descendants(NAMED_THING)
    assert "ameliorates condition" in toolkit.get_descendants("biolink:ameliorates")
    assert "biolink:ameliorates_condition" in toolkit.get_descendants("biolink:ameliorates", formatted=True)

    with pytest.raises(ValueError):
        toolkit.get_descendants('biolink:invalid')
    assert "biolink:PhenotypicFeature" in toolkit.get_descendants(
        NAMED_THING, formatted=True
    )
    assert "molecular activity_has output" not in toolkit.get_descendants(
        MOLECULAR_ACTIVITY, reflexive=True
    )
    assert "molecular activity_has output" not in toolkit.get_descendants(
        "has output", reflexive=True
    )
    assert "expressed in" in toolkit.get_descendants("located in")
    assert GENE in toolkit.get_descendants(GENE, reflexive=True)


def test_children(toolkit):
    assert CAUSES in toolkit.get_children("contributes to")
    assert "physically interacts with" in toolkit.get_children(INTERACTS_WITH)
    assert "transcript" in toolkit.get_children(BIOLOGICAL_ENTITY)
    assert GENE in toolkit.get_children(GENE_OR_GENE_PRODUCT)
    assert GENE not in toolkit.get_children(GENE_OR_GENE_PRODUCT, mixin=False)
    assert "biolink:Transcript" in toolkit.get_children(
        BIOLOGICAL_ENTITY, formatted=True
    )


def test_parent(toolkit):
    assert "contributes to" in toolkit.get_parent(CAUSES)
    assert INTERACTS_WITH in toolkit.get_parent("physically interacts with")
    assert BIOLOGICAL_ENTITY in toolkit.get_parent(GENE)
    assert BIOLOGICAL_ENTITY_CURIE in toolkit.get_parent(GENE, formatted=True)


def test_mapping(toolkit):
    assert len(toolkit.get_all_elements_by_mapping("SO:0000704")) == 1
    assert GENE in toolkit.get_all_elements_by_mapping("SO:0000704")

    assert len(toolkit.get_all_elements_by_mapping("MONDO:0000001")) == 1
    assert "disease" in toolkit.get_all_elements_by_mapping("MONDO:0000001")

    assert len(toolkit.get_all_elements_by_mapping("UPHENO:0000001")) == 1
    assert "affects" in toolkit.get_all_elements_by_mapping("UPHENO:0000001")

    assert toolkit.get_element_by_mapping(
        'STY:T071', most_specific=True, formatted=True, mixin=True
    ) == NAMED_THING_CURIE
    assert toolkit.get_element_by_mapping(
        'STY:T044', most_specific=True, formatted=True, mixin=True
    ) == 'biolink:MolecularActivity'

    assert toolkit.get_element_by_mapping(
        "BFO:0000001", most_specific=True, formatted=True, mixin=True
    ) == NAMED_THING_CURIE
    assert toolkit.get_element_by_mapping(
        'STY:T071', most_specific=True, formatted=True, mixin=True
    ) == NAMED_THING_CURIE
    assert toolkit.get_element_by_mapping(
        'STY:T044', most_specific=True, formatted=True, mixin=True
    ) == 'biolink:MolecularActivity'

    assert toolkit.get_element_by_mapping(
        'STY:T066666', most_specific=True, formatted=True, mixin=True
    ) is None


def test_get_slot_domain(toolkit):
    assert "biological process" in toolkit.get_slot_domain(ENABLED_BY)
    assert "biological process or activity" in toolkit.get_slot_domain(ENABLED_BY)
    assert "pathway" in toolkit.get_slot_domain(
        ENABLED_BY, include_ancestors=True
    )
    assert "biolink:BiologicalProcessOrActivity" in toolkit.get_slot_domain(
        ENABLED_BY, include_ancestors=True, formatted=True
    )
    assert ENTITY in toolkit.get_slot_domain("category")
    assert ASSOCIATION in toolkit.get_slot_domain("predicate")


def test_get_slot_range(toolkit):
    assert "disease or phenotypic feature" in toolkit.get_slot_range("treats")
    assert "disease" in toolkit.get_slot_range("treats", include_ancestors=True)
    assert "biolink:Disease" in toolkit.get_slot_range(
        "treats", include_ancestors=True, formatted=True
    )
    assert "label type" in toolkit.get_slot_range("name")


def test_get_all_slots_with_class_domain(toolkit):
    assert "has attribute" in toolkit.get_all_slots_with_class_domain(
        ENTITY, check_ancestors=True, mixin=True
    )
    assert "name" not in toolkit.get_all_slots_with_class_domain(
        TREATMENT, check_ancestors=False, mixin=False
    )
    assert "type" in toolkit.get_all_slots_with_class_domain(ENTITY_CURIE, check_ancestors=True, mixin=True)
    # we don't really have this use case in the model right now - where a domain's mixin has an attribute
    assert "has unit" in toolkit.get_all_slots_with_class_domain(
        "quantity value", check_ancestors=False, mixin=True
    )


def test_get_all_slots_with_class_range(toolkit):
    assert "in taxon" in toolkit.get_all_slots_with_class_range(ORGANISM_TAXON)
    assert "biolink:in_taxon" in toolkit.get_all_slots_with_class_range(
        ORGANISM_TAXON, formatted=True
    )
    assert SUBJECT in toolkit.get_all_slots_with_class_range(
        ORGANISM_TAXON, check_ancestors=True, mixin=False
    )


def test_get_all_predicates_with_class_domain(toolkit):
    assert "genetically interacts with" in toolkit.get_all_slots_with_class_domain(GENE)
    assert INTERACTS_WITH in toolkit.get_all_slots_with_class_domain(
        GENE, check_ancestors=True
    )
    assert "biolink:interacts_with" in toolkit.get_all_slots_with_class_domain(
        "gene", check_ancestors=True, formatted=True
    )
    assert "in complex with" in toolkit.get_all_slots_with_class_domain(
        GENE_OR_GENE_PRODUCT
    )
    assert "expressed in" in toolkit.get_all_slots_with_class_domain(
        GENE_OR_GENE_PRODUCT
    )
    assert RELATED_TO not in toolkit.get_all_slots_with_class_domain(
        GENE_OR_GENE_PRODUCT, check_ancestors=False, mixin=False
    )
    assert RELATED_TO not in toolkit.get_all_slots_with_class_domain(
        GENE_OR_GENE_PRODUCT, check_ancestors=True, mixin=True
    )


def test_get_all_predicates_with_class_range(toolkit):
    assert "manifestation of" in toolkit.get_all_predicates_with_class_range("disease")
    assert "target for" in toolkit.get_all_predicates_with_class_range(
        "disease", check_ancestors=True
    )
    assert (
        "biolink:target_for"
        in toolkit.get_all_predicates_with_class_range(
            "disease", check_ancestors=True, formatted=True
        )
    )
    assert RELATED_TO not in toolkit.get_all_predicates_with_class_range(
        "disease", check_ancestors=True, formatted=True
    )


def test_get_all_properties_with_class_domain(toolkit):
    assert "category" in toolkit.get_all_properties_with_class_domain(ENTITY)
    assert "category" in toolkit.get_all_properties_with_class_domain(
        GENE, check_ancestors=True
    )
    assert "biolink:category" in toolkit.get_all_properties_with_class_domain(
        GENE, check_ancestors=True, formatted=True
    )

    assert "predicate" in toolkit.get_all_properties_with_class_domain(ASSOCIATION)
    assert "predicate" in toolkit.get_all_properties_with_class_domain(
        ASSOCIATION, check_ancestors=True
    )
    assert "biolink:predicate" in toolkit.get_all_properties_with_class_domain(
        ASSOCIATION, check_ancestors=True, formatted=True
    )


def test_get_all_properties_with_class_range(toolkit):
    assert "has gene" in toolkit.get_all_properties_with_class_range(GENE)
    assert SUBJECT in toolkit.get_all_properties_with_class_range(
        GENE, check_ancestors=True
    )
    assert "biolink:subject" in toolkit.get_all_properties_with_class_range(
        GENE, check_ancestors=True, formatted=True
    )


def test_get_value_type_for_slot(toolkit):
    assert "uriorcurie" in toolkit.get_value_type_for_slot(SUBJECT)
    assert "uriorcurie" in toolkit.get_value_type_for_slot("object")
    assert "string" in toolkit.get_value_type_for_slot("symbol")
    assert "metatype:Uriorcurie" in toolkit.get_value_type_for_slot(
        "category", formatted=True
    )


def test_get_all_types(toolkit):
    basic_descendants = {}

    # get_all_types()
    types = toolkit.get_all_types()

    for element in types:
        try:
            basic_descendants.update({
                element: toolkit.get_descendants(
                    element,
                    reflexive=False,
                    mixin=False,
                )
            })
        except Exception as e:
            assert False, f"Error getting descendants for {element}: {e}"


def test_get_all_multivalued_slots(toolkit):
    assert "synonym" in toolkit.get_all_multivalued_slots()
    assert "id" not in toolkit.get_all_multivalued_slots()


def test_get_descendants_with_biolink_prefix(toolkit):
    assert 'noncoding RNA product' in toolkit.get_descendants("noncoding RNA product")
    assert 'microRNA' in toolkit.get_descendants("noncoding RNA product")
    assert 'siRNA' in toolkit.get_descendants("noncoding RNA product")
    
    assert 'noncoding RNA product' in toolkit.get_descendants("biolink:NoncodingRNAProduct")
    assert 'microRNA' in toolkit.get_descendants("biolink:NoncodingRNAProduct")
    assert 'siRNA' in toolkit.get_descendants("biolink:NoncodingRNAProduct")
    
    assert 'microRNA' in toolkit.get_descendants("biolink:MicroRNA")
    assert 'siRNA' in toolkit.get_descendants("biolink:SiRNA")


def test_get_element_with_biolink_prefix_edge_cases(toolkit):
    elem = toolkit.get_element("biolink:NoncodingRNAProduct")
    assert elem is not None
    assert elem.name == "noncoding RNA product"
    
    elem = toolkit.get_element("biolink:MicroRNA")
    assert elem is not None
    assert elem.name == "microRNA"
    
    elem = toolkit.get_element("biolink:SiRNA")
    assert elem is not None
    assert elem.name == "siRNA"
    
    elem = toolkit.get_element("biolink:gene_fusion_with")
    assert elem is not None
    assert elem.name == "gene_fusion_with"
    
    elem = toolkit.get_element("biolink:genetic_neighborhood_of")
    assert elem is not None
    assert elem.name == "genetic_neighborhood_of"


def test_get_parent_with_biolink_prefix(toolkit):
    parent = toolkit.get_parent('microRNA')
    assert parent == 'noncoding RNA product'
    
    parent_curie = toolkit.get_parent('microRNA', formatted=True)
    assert parent_curie == 'biolink:NoncodingRNAProduct'
    
    parent_from_curie = toolkit.get_parent('biolink:microRNA')
    assert parent_from_curie == 'noncoding RNA product'
    
    parent_from_curie_formatted = toolkit.get_parent('biolink:microRNA', formatted=True)
    assert parent_from_curie_formatted == 'biolink:NoncodingRNAProduct'

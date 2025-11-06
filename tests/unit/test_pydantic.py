"""
Tests Pydantic related utility code
"""

import biolink_model.datamodel.pydanticmodel_v2 as pyd
import pytest
from bmt import Toolkit
from bmt.pydantic import (
    entity_id,
    infores,
    get_node_class,
    get_edge_class,
    build_association_knowledge_sources
)

@pytest.fixture(scope="module")
def toolkit():
    return Toolkit()

def test_entity_id():
    assert entity_id().startswith("urn:uuid:")

def test_infores():
    with pytest.raises(AssertionError):
        infores("")
    assert infores("foobar").startswith("infores:")

#############################
## Tests for get_node_class #
#############################

def test_get_node_class_by_category_curie():
    # Biolink CURIE category
    disease_node_id: str = "DOID:0111266"
    node_class = get_node_class(node_id=disease_node_id, categories=["biolink:Disease"])
    assert node_class is not None
    disease_node = node_class(id=disease_node_id,**{})
    assert isinstance(disease_node,pyd.Disease)

def test_get_node_class_simple_name():
    # Naked name of category
    gene_node_id: str = "HGNC:12791"
    node_class = get_node_class(node_id=gene_node_id, categories=["Gene"])
    assert node_class is not None
    gene_node = node_class(id=gene_node_id,**{})
    assert isinstance(gene_node,pyd.Gene)

def test_get_node_class_unknown_category():
    # Unknown category
    nonsense_node_id: str = "foo:bar"
    node_class = get_node_class(node_id=nonsense_node_id, categories=["biolink:Nonsense"])
    assert node_class == pyd.NamedThing

def test_get_node_class_empty_categories():
    # Empty categories
    empty_node_id: str = "empty:node"
    node_class = get_node_class(node_id=empty_node_id, categories=[])
    assert node_class is pyd.NamedThing

def test_get_node_class_from_most_specific_category():
    # List of categories - want the most specific one
    disease_node_id: str = "DOID:0111266"
    node_class = get_node_class(
        node_id=disease_node_id,
        categories=[
            "biolink:Disease",
            "biolink:DiseaseOrPhenotypicFeature",
            "biolink:ThingWithTaxon",
            "biolink:BiologicalEntity",
            "biolink:NamedThing",
        ]
    )
    assert node_class is not None
    disease_node = node_class(id=disease_node_id,**{})
    assert isinstance(disease_node,pyd.Disease)

#############################
## Tests for get_edge_class #
#############################

def test_get_edge_class_by_category_curie():
    # Biolink CURIE association
    edge_class = get_edge_class(
        edge_id="test:association",
        associations=["biolink:GeneToGeneAssociation"]
    )
    assert edge_class is not None
    association = edge_class(
        id="test:association",
        subject="HGNC:12791",
        predicate="biolink:interacts_with",
        object="HGNC:12792",
        knowledge_level=pyd.KnowledgeLevelEnum.knowledge_assertion,
        agent_type=pyd.AgentTypeEnum.manual_agent,
        **{}
    )
    assert isinstance(association, pyd.GeneToGeneAssociation)

def test_get_edge_class_simple_name():
    # Naked name of category
    edge_class = get_edge_class(
        edge_id="test:association",
        associations=["PairwiseMolecularInteraction"]
    )
    assert edge_class is not None
    association = edge_class(
        id="test:association",
        subject="HGNC:12791",
        predicate="biolink:interacts_with",
        object="HGNC:12792",
        knowledge_level=pyd.KnowledgeLevelEnum.knowledge_assertion,
        agent_type=pyd.AgentTypeEnum.manual_agent,
        **{}
    )
    assert isinstance(association, pyd.PairwiseMolecularInteraction)

def test_get_edge_class_unknown_category():
    # Unknown category
    edge_class = get_edge_class(
        edge_id="test:association",
        associations=["biolink:Nonsense"]
    )
    assert edge_class == pyd.Association

def test_get_edge_class_empty_categories():
    # Empty categories
    empty_node_id: str = "empty:edge"
    edge_class = get_edge_class(
        edge_id=empty_node_id,
        associations=[]
    )
    assert edge_class is pyd.Association

def test_get_edge_class_from_most_specific_association():
    # List of associations - want the most specific one
    edge_class = get_edge_class(
        edge_id="test:association",
        associations=[
            "biolink:GeneToGeneAssociation",
            "biolink:PairwiseGeneToGeneInteraction",
            "biolink:PairwiseMolecularInteraction",
            "biolink:Association",
        ]
    )
    assert edge_class is not None
    association = edge_class(
        id="test:association",
        subject="HGNC:12791",
        predicate="biolink:interacts_with",
        object="HGNC:12792",
        knowledge_level=pyd.KnowledgeLevelEnum.knowledge_assertion,
        agent_type=pyd.AgentTypeEnum.manual_agent,
        **{}
    )
    assert isinstance(association, pyd.PairwiseMolecularInteraction)

def test_simple_build_association_knowledge_sources():
    sources: list[pyd.RetrievalSource] = \
        build_association_knowledge_sources(primary="infores:foobar")
    assert sources is not None
    assert len(sources) == 1
    primary_source: pyd.RetrievalSource = sources[0]
    assert primary_source.resource_id == "infores:foobar"
    assert primary_source.resource_role == pyd.ResourceRoleEnum.primary_knowledge_source
    assert primary_source.upstream_resource_ids is None

##################################################
## tests for build_association_knowledge_sources #
##################################################

def test_supported_build_association_knowledge_sources():
    sources: list[pyd.RetrievalSource] = \
        build_association_knowledge_sources(
            primary="infores:foobar",
            supporting = ["infores:foobar2", "infores:foobar3"]
    )
    assert sources is not None
    assert len(sources) == 3
    for source in sources:
        if source.resource_role == pyd.ResourceRoleEnum.primary_knowledge_source:
            assert source.resource_id == "infores:foobar"
            assert source.upstream_resource_ids is not None
            assert all(
                        upstream in ["infores:foobar2", "infores:foobar3"]
                        for upstream in source.upstream_resource_ids
                    )
        elif source.resource_role == pyd.ResourceRoleEnum.supporting_data_source:
            assert source.resource_id in ["infores:foobar2", "infores:foobar3"]
            assert source.upstream_resource_ids is None
        else:
            assert False, f"Unexpected resource role: {source.resource_role}"


def test_aggregated_build_association_knowledge_sources():
    aggregating: dict[str, list[str]] = {
        "infores:tweedle-dee": ["infores:tweedle-dum"]
    }
    sources: list[pyd.RetrievalSource] = \
        build_association_knowledge_sources(
            primary="infores:tweedle-dum",
            aggregating = aggregating
    )
    assert sources is not None
    assert len(sources) == 2
    for source in sources:
        if source.resource_role == pyd.ResourceRoleEnum.primary_knowledge_source:
            assert source.resource_id == "infores:tweedle-dum"
            assert source.upstream_resource_ids is None
        elif source.resource_role == pyd.ResourceRoleEnum.aggregator_knowledge_source:
            assert source.resource_id == "infores:tweedle-dee"
            assert source.upstream_resource_ids is not None
            assert all(
                        upstream in ["infores:tweedle-dum"]
                        for upstream in source.upstream_resource_ids
                    )
        else:
            assert False, f"Unexpected resource role: {source.resource_role}"

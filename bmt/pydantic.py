"""
This module contains some utility code
to facilitate Pydantic coding use cases.
"""
from typing import Optional
import logging
from uuid import uuid4
import biolink_model.datamodel.pydanticmodel_v2 as pyd

from bmt import Toolkit
toolkit = Toolkit()

logger = logging.getLogger(__name__)

def entity_id() -> str:
    """
    Generate a unique identifier for a Biolink Model entity.

    Returns
    -------
    str
        unique identifier
    """
    return uuid4().urn


def infores(identifier: str) -> str:
    """
    Coerce the specified identifier to the Biolink Model infores namespace.
    Parameters
    ----------
    identifier: str
        Input identifier
    Returns
    -------
    str
        identifier properly coerced to infores namespace
    """
    # Limitation: no attempt is made to validate
    # them against the public infores inventory at
    # https://github.com/biolink/information-resource-registry
    assert identifier, "Empty identifier not allowed"
    return identifier if identifier.startswith("infores:") else f"infores:{identifier}"


def get_node_class(
        node_id: str,
        categories: list[str],
        bmt: Toolkit = Toolkit()
) -> type[pyd.NamedThing]:
    """
    Return the most specific Biolink Model Pydantic class for a given node category.

    Parameters
    ----------
    node_id: str
        Node identifier
    categories: list[str]
        List of category Biolink CURIEs
    bmt: Toolkit = Toolkit()
        Biolink Model Toolkit instance (tied to a particular version of the Biolink Model)
    Returns
    -------
    Pydantic class
        instance of NamedThing or its most specific child class; None if unavailable
    """
    if not categories:
        logger.warning(f"Node with id {node_id} has empty categories; defaulting to 'biolink:NamedThing'")
        return pyd.NamedThing
    category = bmt.get_most_specific_category(category_list=categories)
    try:
        category = category.replace("biolink:", "")
        return getattr(pyd, category)
    except AttributeError:
        logger.warning(
            f"No Biolink Model class found for category '{category}',"
            f" for node with id {node_id}; defaulting to 'biolink:NamedThing'"
        )
        return pyd.NamedThing


def get_edge_class(
        edge_id: str,
        associations: list[str],
        bmt: Toolkit = Toolkit()
) -> Optional[type[pyd.Association]]:
    """
    Return the most specific Biolink Model Pydantic class for a given association category.

    Parameters
    ----------
    edge_id: str
        Edge identifier
    associations: list[str]
        List of association Biolink CURIEs
    bmt: Toolkit = Toolkit()
        Biolink Model Toolkit instance (tied to a particular version of the Biolink Model)
    Returns
    -------
    Pydantic class
        instance of Association or its most specific child class; None if unavailable
    """
    if not associations:
        logger.warning(f"Edge with id {edge_id} has empty associations; defaulting to 'biolink:Association'")
        return pyd.Association
    association = bmt.get_most_specific_association(association_list=associations)
    try:
        association = association.replace("biolink:", "")
        return getattr(pyd, association)
    except AttributeError:
        logger.warning(
            f"No Biolink Model class found for association '{association}',"
            f" for node with id {edge_id}; defaulting to 'biolink:Association'"
        )
        return pyd.Association


def build_association_knowledge_sources(
        primary: str,
        supporting: Optional[list[str]] = None,
        aggregating: Optional[dict[str, list[str]]] = None
) -> list[pyd.RetrievalSource]:
    """
    This function attempts to build a list of well-formed Biolink Model RetrievalSource
    of Association 'sources' annotation from the specified knowledge source parameters.
    This method is lenient in that it allows for strings that are not explicitly infores identifiers:
    it converts these to infores identifiers by prefixing with the 'infores:' namespace (but doesn't validate
    them against the public infores inventory at https://github.com/biolink/information-resource-registry).

    Parameters
    ----------
    primary: str
        Infores identifier for the primary knowledge source of an Association
    supporting: Optional[list[str]]
        Infores identifiers of the supporting data sources (default: None)
    aggregating: Optional[dict[str, list[str]]]
        With infores identifiers of the aggregating knowledge sources as keys, and
        list[str] of the upstream knowledge source infores identifiers (default: None)
    Returns
    -------
    list[RetrievalSource]
        not guaranteed in any given order, except that
        the first entry may be the primary knowledge source

    """
    #
    # RetrievalSource fields of interest
    #     resource_id: Union[str, URIorCURIE] = None
    #     resource_role: Union[str, "ResourceRoleEnum"] = None
    #     upstream_resource_ids: Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]] = empty_list()
    #     Limitation: the current use case doesn't use source_record_urls, but...
    #     source_record_urls: Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]] = empty_list()
    #
    sources: list[pyd.RetrievalSource] = []
    primary_knowledge_source: Optional[pyd.RetrievalSource] = None
    if primary:
        primary_knowledge_source = pyd.RetrievalSource(
            id=entity_id(), resource_id=infores(primary), resource_role=pyd.ResourceRoleEnum.primary_knowledge_source, **{}
        )
        sources.append(primary_knowledge_source)

    if supporting:
        for source_id in supporting:
            resource_id = str(source_id)
            supporting_knowledge_source = pyd.RetrievalSource(
                id=entity_id(),
                resource_id=infores(resource_id),
                resource_role=pyd.ResourceRoleEnum.supporting_data_source,
                **{},
            )
            sources.append(supporting_knowledge_source)
            if primary_knowledge_source:
                if primary_knowledge_source.upstream_resource_ids is None:
                    primary_knowledge_source.upstream_resource_ids = []
                primary_knowledge_source.upstream_resource_ids.append(infores(resource_id))
    if aggregating:
        for source_id, upstream_ids in aggregating.items():
            aggregating_knowledge_source = pyd.RetrievalSource(
                id=entity_id(),
                resource_id=infores(source_id),
                resource_role=pyd.ResourceRoleEnum.aggregator_knowledge_source,
                **{},
            )
            aggregating_knowledge_source.upstream_resource_ids = [infores(upstream) for upstream in upstream_ids]
            sources.append(aggregating_knowledge_source)

    return sources

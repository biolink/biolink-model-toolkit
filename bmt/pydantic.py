"""
This module contains some utility code
to facilitate Pydantic coding use cases.
"""
from typing import Optional, Union
import importlib.resources
from functools import lru_cache
import logging
from uuid import uuid4

from linkml_runtime.utils.schemaview import SchemaView
import biolink_model.datamodel.pydanticmodel_v2 as pyd
from bmt import Toolkit

toolkit = Toolkit()

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_biolink_schema() -> SchemaView:
    """Get cached Biolink schema, loading it if not already cached."""

    # Try to load from the local Biolink model first (same version as ingests)
    try:
        with importlib.resources.path("biolink_model.schema", "biolink_model.yaml") as schema_path:
            schema_view = SchemaView(str(schema_path))
            logger.debug("Successfully loaded Biolink schema from local file")
            return schema_view
    except Exception as e:
        logger.warning(f"Failed to load local Biolink schema: {e}")
        # Fallback to loading from official URL
        schema_view = SchemaView("https://w3id.org/biolink/biolink-model.yaml")
        logger.debug("Successfully loaded Biolink schema from URL")
        return schema_view


def get_current_biolink_version() -> str:
    return get_biolink_schema().schema.version


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


def _build_retrieval_source(
        source_spec: Union[str,tuple[str, list[str]]],
        resource_role: Optional[pyd.ResourceRoleEnum]
) -> pyd.RetrievalSource:
    if isinstance(source_spec, tuple):
        assert len(source_spec) == 2, f"Invalid supporting data source tuple: {source_spec}"
        resource_id = str(source_spec[0])
        source_record_urls = source_spec[1]
    else:
        resource_id = source_spec
        source_record_urls = None
    return pyd.RetrievalSource(
        id=entity_id(),
        resource_id=infores(resource_id),
        resource_role=resource_role,
        source_record_urls=source_record_urls,
        **{},
    )

def build_association_knowledge_sources(
        primary: Union[str,tuple[str, list[str]]],
        supporting: Optional[list[Union[str,tuple[str, list[str]]]]] = None,
        aggregating: Optional[Union[str,tuple[str, list[str]]]] = None
) -> list[pyd.RetrievalSource]:
    """
    This function attempts to build a list of a well-formed RetrievalSource list
    for an Association **sources** slot, using given knowledge source parameters
    for primary, supporting and aggregating knowledge sources.

    The use case for 'aggregating knowledge source' represents the limited use case where
    only one primary knowledge source is specified, as a single upstream knowledge source.
    This is, of course, not the general case for all aggregating knowledge sources;
    however, the use case of aggregating knowledge sources with multiple upstream ('primary')
    knowledge sources is not yet supported.

    This method is lenient in that it allows for strings that are not explicitly encoded
    as infores identifiers, converting these to infores identifiers by prefixing with
    the 'infores:' namespace (but the method doesn't validate these coerced infores identifiers
    against the public infores inventory at https://github.com/biolink/information-resource-registry).

    There are optional 'extended form' provisions for the addition of associated **source_record_urls**
    to the instances of **resource_id** provided for primary, aggregating and supporting knowledge sources.

    Parameters
    ----------
    primary:
        **Simple form:** Infores 'resource_id' for the primary knowledge source of an Association.
        **Extended form:** 2-tuple of (resource_id, list[source_record_urls])
        for the primary knowledge source of an Association.

    supporting:
        **Simple form:** List of supporting datasource infores 'resource_id' instances. Supporting
        data sources are automatically assumed to be upstream of the primary knowledge source and
        mapped accordingly.
        **Extended form:** List of 2-tuples with form (resource_id, list[source_record_urls]).

    aggregating:
        **Simple form:** With the infores 'resource_id' of the aggregating knowledge source.
        The primary knowledge source given to the method is automatically assumed to be upstream
        of the aggregating knowledge source and mapped accordingly.
        **Extended form:** 2-tuple of (resource_id, list[source_record_urls])
        for the aggregating knowledge source of an Association.

    Returns
    -------
    list[pyd.RetrievalSource]:
        List of RetrievalSource entries that are not guaranteed in any given order,
        except that the first entry will usually be the primary knowledge source.

    """
    primary_knowledge_source: Optional[pyd.RetrievalSource] = \
        _build_retrieval_source(
            primary,
            pyd.ResourceRoleEnum.primary_knowledge_source
        )
    sources: list[pyd.RetrievalSource] =[primary_knowledge_source]

    if supporting:
        for supporting_source_id in supporting:
            supporting_knowledge_source = \
                _build_retrieval_source(
                    supporting_source_id,
                    pyd.ResourceRoleEnum.supporting_data_source
            )
            sources.append(supporting_knowledge_source)
            if primary_knowledge_source.upstream_resource_ids is None:
                primary_knowledge_source.upstream_resource_ids = []
            primary_knowledge_source.upstream_resource_ids.append(
                infores(supporting_knowledge_source.resource_id)
            )

    if aggregating:
        aggregating_knowledge_source = \
            _build_retrieval_source(
                aggregating,
                pyd.ResourceRoleEnum.aggregator_knowledge_source
            )

        # The use case for 'aggregating knowledge source' represents the
        # limited use case where only one primary knowledge source is specified
        aggregating_knowledge_source.upstream_resource_ids = [
            primary_knowledge_source.resource_id
        ]

        sources.append(aggregating_knowledge_source)

    return sources

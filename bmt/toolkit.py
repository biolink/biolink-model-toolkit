import logging
from functools import lru_cache, reduce
from typing import List, Union, TextIO, Optional, Set
import deprecation
from biolinkml.meta import SchemaDefinition, Element, Definition, ClassDefinition, SlotDefinition

from bmt.toolkit_generator import ToolkitGenerator
from bmt.utils import format_element, parse_name

Url = str
Path = str
REMOTE_PATH = 'https://raw.githubusercontent.com/biolink/biolink-model/1.3.9/biolink-model.yaml'

CACHE_SIZE = 1024


class Toolkit(object):
    """
    Provides a series of methods for performing lookups on the Biolink Model

    Parameters
    ----------
    schema: Union[str, TextIO, SchemaDefinition]
        The path or url to an instance of the biolink-model.yaml file.

    """

    def __init__(self, schema: Union[Url, Path, TextIO, SchemaDefinition] = REMOTE_PATH) -> None:
        self.generator = ToolkitGenerator(schema)
        self.generator.serialize()

    @lru_cache(CACHE_SIZE)
    def get_all_elements(self, formatted: bool = False) -> List[str]:
        """
        Get all elements from Biolink Model.

        This method returns a list containing all
        classes, slots, and types defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        classes = self.get_all_classes(formatted)
        slots = self.get_all_slots(formatted)
        types = self.get_all_types(formatted)
        all_elements = classes + slots + types
        return all_elements

    @lru_cache(CACHE_SIZE)
    def get_all_classes(self, formatted: bool = False) -> List[str]:
        """
        Get all classes from Biolink Model.

        This method returns a list containing all the
        classes defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        classes = []
        for x in self.generator.schema.classes:
            classes.append(x)
        filtered_classes = self._filter_secondary(classes)
        return self._format_all_elements(filtered_classes, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_slots(self, formatted: bool = False) -> List[str]:
        """
        Get all slots from Biolink Model.

        This method returns a list containing all the
        slots defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        slots = []
        for x in self.generator.schema.slots:
            slots.append(x)
        filtered_slots = self._filter_secondary(slots)
        return self._format_all_elements(filtered_slots, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_types(self, formatted: bool = False) -> List[str]:
        """
        Get all types from Biolink Model.

        This method returns a list containing all the
        built-in and defined types in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        types = []
        for x in self.generator.schema.types:
            types.append(x)
        return self._format_all_elements(types, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_entities(self, formatted: bool = False) -> List[str]:
        """
        Get all entities from Biolink Model.

        This method returns a list containing all the classes
        that are descendants of the class ``named thing``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_descendants('named thing')
        return self._format_all_elements(elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_associations(self, formatted: bool = False) -> List[str]:
        """
        Get all associations from Biolink Model.

        This method returns a list containing all the classes
        that are descendants of the class ``association``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_descendants('association')
        return self._format_all_elements(elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_node_properties(self, formatted: bool = False) -> List[str]:
        """
        Get all node properties from Biolink Model.

        This method returns a list containing all the slots
        that are descendants of the slot ``node property``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_descendants('node property')
        filtered_elements = self._filter_secondary(elements)
        return self._format_all_elements(filtered_elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_edge_properties(self, formatted: bool = False) -> List[str]:
        """
        Get all edge properties from Biolink Model.

        This method returns a list containing all the slots
        that are descendants of the slot ``association slot``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_descendants('association slot')
        filtered_elements = self._filter_secondary(elements)
        return self._format_all_elements(filtered_elements, formatted)

    def _filter_secondary(self, elements: List[str]) -> List[str]:
        """
        From a given list of elements, remove elements that are not proper slots.

        This method removes spurious slots like ``gene_to_gene_association_subject``
        that are artifact of domain/range constraints and not actual slots.

        Parameters
        ----------
        elements: List[str]
            List of elements

        Returns
        -------
        List[str]
            A filtered list of elements

        """
        filtered_elements = []
        for e in elements:
            eo = self.generator.obj_for(e)
            if isinstance(eo, SlotDefinition):
                if not eo.alias:
                    filtered_elements.append(e)
            else:
                filtered_elements.append(e)
        return filtered_elements

    @lru_cache(CACHE_SIZE)
    def get_ancestors(self, name: str, reflexive: bool = True, formatted: bool = False) -> List[str]:
        """
        Gets a list of names of ancestors.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        reflexive: bool
            Whether to include the query element in the list of ancestors
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            The names of the given elements ancestors

        """
        element = self.get_element(name)
        ancs = []
        if isinstance(element, (ClassDefinition, SlotDefinition)):
            a = self.generator.ancestors(element)
            ancs = a if reflexive else a[1:]
        return self._format_all_elements(ancs, formatted)

    @lru_cache(CACHE_SIZE)
    def get_descendants(self, name: str, reflexive: bool = True, formatted: bool = False) -> List[str]:
        """
        Gets a list of names of descendants.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        reflexive: bool
            Whether to include the query element in the list of ancestors
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            The names of the given element's descendants

        """
        desc = []
        element = self.get_element(name)
        d = self.generator.descendants(element.name)
        if d and reflexive:
            desc.append(element.name)
        desc += d
        return self._format_all_elements(desc, formatted)

    @lru_cache(CACHE_SIZE)
    def get_children(self, name: str, formatted: bool = False) -> List[str]:
        """
        Gets a list of names of children.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            The names of the given elements children

        """
        element = self.get_element(name)
        children = self.generator.children(element.name)
        return self._format_all_elements(children, formatted)

    @lru_cache(CACHE_SIZE)
    def get_parent(self, name: str, formatted: bool = False) -> Optional[str]:
        """
        Gets the name of the parent.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        Optional[str]
            The name of the given elements parent

        """
        element = self.get_element(name)
        p = element.is_a if isinstance(element, Definition) else None
        if p and formatted:
            parent = format_element(element)
        else:
            parent = p
        return parent

    @lru_cache(CACHE_SIZE)
    def get_element(self, name: str) -> Optional[Element]:
        """
        Gets an element that is identified by the given name, either as its name
        or as one of its aliases.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        Element
            The element identified by the given name

        """
        parsed_name = parse_name(name)
        element = self.generator.obj_for(parsed_name)
        if element is None:
            if name in self.generator.aliases:
                element = self.get_element(self.generator.aliases[name])
        if element is None:
            if '_' in name:
                element = self.get_element(name.replace('_', ' '))
        return element

    @lru_cache(CACHE_SIZE)
    def is_predicate(self, name: str) -> bool:
        """
        Determines whether the given name is the name of an relation/predicate
        in the Biolink Model. An element is a predicate if it descends from
        `related to`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid relation/predicate in Biolink Model
        """
        return 'related to' in self.get_ancestors(name)

    @lru_cache(CACHE_SIZE)
    def in_subset(self, name: str, subset: str) -> bool:
        """
        Determines whether the given name is in a given subset
        in the Biolink Model.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model.
        subset: str
            The name of the subset

        Returns
        -------
        bool
            That the named element is part of a given subset in Biolink Model

        """
        parsed_name = parse_name(name)
        element = self.generator.obj_for(parsed_name)
        return subset in element.in_subset

    @lru_cache(CACHE_SIZE)
    def is_category(self, name: str) -> bool:
        """
        Determines whether the given name is the name of a category in the
        Biolink Model. An element is a category if it descends from
        `named thing`

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid category in Biolink Model

        """
        return 'named thing' in self.get_ancestors(name)

    @lru_cache(CACHE_SIZE)
    def get_element_by_mapping(self, identifier: str, most_specific: bool = False, formatted: bool = False) -> Optional[str]:
        """
        Get a Biolink Model element by mapping.
        This method return the common ancestor of the set of elements referenced by uriorcurie.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        most_specific: bool
            Whether or not to get the first available mapping in the order of specificity
            or to get all mappings of varying specificity
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        Optional[str]
            The Biolink element (or the common ancestor) corresponding to the given URI/CURIE

        """
        if most_specific:
            mappings = self._get_element_by_mapping(identifier)
        else:
            mappings = self.get_all_elements_by_mapping(identifier)
        if mappings:
            ancestors: List[List[str]] = []
            for m in mappings:
                ancestors.append([x for x in self.get_ancestors(m)[::-1] if x in mappings])
            common_ancestors = reduce(lambda s, l: s.intersection(set(l)), ancestors[1:], set(ancestors[0]))
            for a in ancestors[0]:
                if a in common_ancestors:
                    if formatted:
                        element = format_element(self.generator.obj_for(a))
                    else:
                        element = a
                    return element

    @lru_cache(CACHE_SIZE)
    def _get_element_by_mapping(self, identifier: str) -> List[str]:
        """
        Get the most specific mapping corresponding to a given identifier.
        This method first checks for general mappings. If it can't find any then
        it starts looking for exact_mappings, close_mappings, related_mappings,
        narrow_mappings and finally broad_mappings. It will stop if it finds a
        mapping at first occurrence.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.mappings.get(self.generator.namespaces.uri_for(identifier), set())
        if not mappings:
            exact = set(self.get_element_by_exact_mapping(identifier))
            mappings.update(exact)
        if not mappings:
            close = set(self.get_element_by_close_mapping(identifier))
            mappings.update(close)
        if not mappings:
            related = set(self.get_element_by_related_mapping(identifier))
            mappings.update(related)
        if not mappings:
            narrow = set(self.get_element_by_narrow_mapping(identifier))
            mappings.update(narrow)
        if not mappings:
            broad = set(self.get_element_by_broad_mapping(identifier))
            mappings.update(broad)
        return mappings

    @lru_cache(CACHE_SIZE)
    def get_element_by_exact_mapping(self, identifier: str, formatted: bool = False) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its exact_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.exact_mappings.get(self.generator.namespaces.uri_for(identifier), set())
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_close_mapping(self, identifier: str, formatted: bool = False) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its close_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.close_mappings.get(self.generator.namespaces.uri_for(identifier), set())
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_related_mapping(self, identifier: str, formatted: bool = False) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its related_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.related_mappings.get(self.generator.namespaces.uri_for(identifier), set())
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_narrow_mapping(self, identifier: str, formatted: bool = False) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its narrow_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.narrow_mappings.get(self.generator.namespaces.uri_for(identifier), set())
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_broad_mapping(self, identifier: str, formatted: bool = False) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its broad_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.broad_mappings.get(self.generator.namespaces.uri_for(identifier), set())
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_elements_by_mapping(self, identifier: str, formatted: bool = False) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find all Biolink element that corresponds
        to the given identifier as part of its mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.mappings.get(self.generator.namespaces.uri_for(identifier), set())
        exact = set(self.get_element_by_exact_mapping(identifier))
        mappings.update(exact)
        close = set(self.get_element_by_close_mapping(identifier))
        mappings.update(close)
        related = set(self.get_element_by_related_mapping(identifier))
        mappings.update(related)
        narrow = set(self.get_element_by_narrow_mapping(identifier))
        mappings.update(narrow)
        broad = set(self.get_element_by_broad_mapping(identifier))
        mappings.update(broad)
        return self._format_all_elements(mappings, formatted)

    def _format_all_elements(self, elements: List[str], formatted: bool = False) -> List[str]:
        """
        Format all the elements in a given list.

        Parameters
        ----------
        elements: str
            A list of elements
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            The formatted list of elements

        """
        if formatted:
            formatted_elements = [format_element(self.generator.obj_for(x)) for x in elements]
        else:
            formatted_elements = elements
        return formatted_elements

    @deprecation.deprecated(deprecated_in='0.3.0', removed_in='1.0', details='Use get_all_elements method instead')
    def names(self, formatted: bool = False) -> List[str]:
        return self.get_all_elements(formatted)

    @deprecation.deprecated(deprecated_in='0.2.0', removed_in='1.0', details='Use get_descendants method instead')
    def descendents(self, name: str) -> List[str]:
        return self.get_descendants(name)

    @deprecation.deprecated(deprecated_in='0.2.0', removed_in='1.0', details='Use get_ancestors method instead')
    def ancestors(self, name: str) -> List[str]:
        return self.get_ancestors(name)

    @deprecation.deprecated(deprecated_in='0.2.0', removed_in='1.0', details='Use get_children method instead')
    def children(self, name: str) -> List[str]:
        return self.get_children(name)

    @deprecation.deprecated(deprecated_in='0.2.0', removed_in='1.0', details='Use get_parent method instead')
    def parent(self, name: str) -> Optional[str]:
        return self.get_parent(name)

    @deprecation.deprecated(deprecated_in='0.1.1', removed_in='1.0', details='Use is_predicate method instead')
    def is_edgelabel(self, name: str) -> bool:
        return self.is_predicate(name)

    @deprecation.deprecated(deprecated_in='0.1.1', removed_in='1.0', details='Use get_all_elements_by_mapping method instead')
    def get_all_by_mapping(self, uriorcurie: str) -> List[str]:
        return self.get_all_elements_by_mapping(uriorcurie)

    @deprecation.deprecated(deprecated_in='0.1.1', removed_in='1.0', details='Use get_element_by_mapping method instead')
    def get_by_mapping(self, uriorcurie: str) -> Optional[str]:
        return self.get_element_by_mapping(uriorcurie)
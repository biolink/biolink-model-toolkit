import logging
from functools import lru_cache, reduce
from typing import List, Union, TextIO, Optional, Set
import deprecation
from biolinkml.meta import SchemaDefinition, Element, Definition, ClassDefinition, SlotDefinition
from biolinkml.utils.typereferences import References

from bmt.toolkit_generator import ToolkitGenerator

Url = str
Path = str
REMOTE_PATH = 'https://raw.githubusercontent.com/biolink/biolink-model/1.3.9/biolink-model.yaml'


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

    @lru_cache()
    def names(self) -> List[str]:
        """
        Gets the list of names of all elements

        Returns
        -------
        List[str]
            The names of all elements in biolink-model.yaml

        """
        return list(self.generator.aliases.values())

    @lru_cache()
    def get_ancestors(self, name: str) -> List[str]:
        """
        Gets a list of names of ancestors.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model.

        Returns
        -------
        List[str]
            The names of the given elements ancestors.

        """
        obj = self.generator.obj_for(name)
        if isinstance(obj, (ClassDefinition, SlotDefinition)):
            return self.generator.ancestors(obj)
        return []

    @lru_cache()
    def get_descendants(self, name: str) -> List[str]:
        """
        Gets a list of names of descendants.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model.

        Returns
        -------
        List[str]
            The names of the given elements descendants.

        """
        c = []
        for child in self.get_children(name):
            c.append(child)
            c += self.get_descendants(child)
        return c

    @lru_cache()
    def get_children(self, name: str) -> List[str]:
        """
        Gets a list of names of children.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model.

        Returns
        -------
        List[str]
            The names of the given elements children.

        """
        return self._union_of(self.generator.synopsis.isarefs.get(name, References()))

    @lru_cache()
    def get_parent(self, name: str) -> Optional[str]:
        """
        Gets the name of the parent.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model.

        Returns
        -------
        Optional[str]
            The name of the given elements parent

        """
        obj = self.generator.obj_for(name)
        return obj.is_a if isinstance(obj, Definition) else None

    @lru_cache()
    def get_element(self, name: str) -> Optional[Element]:
        """
        Gets an element that is identified by the given name, either as its name
        or as one of its aliases.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model.

        Returns
        -------
        Element
            The element identified by the given name

        """
        if name is None:
            return None
        name = str(name)
        e = self.generator.obj_for(name)
        if e is not None:
            return e

        if name in self.generator.aliases:
            return self.get_element(self.generator.aliases[name])

        if '_' in name:
            return self.get_element(name.replace('_', ' '))

        return None

    @lru_cache()
    def is_predicate(self, name: str) -> bool:
        """
        Determines whether the given name is the name of an relation/predicate
        in the Biolink Model. An element is a predicate if it descends from
        `related to`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model.

        Returns
        -------
        bool
            That the named element is a valid relation/predicate in Biolink Model
        """
        return 'related to' in self.ancestors(name)

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
        element = self.generator.obj_for(name)
        return subset in element.in_subset

    @lru_cache()
    def is_category(self, name: str) -> bool:
        """
        Determines whether the given name is the name of a category in the
        Biolink Model. An element is a category if it descends from
        `named thing`

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model.

        Returns
        -------
        bool
            That the named element is a valid category in Biolink Model

        """
        return 'named thing' in self.ancestors(name)

    @lru_cache()
    def get_element_by_mapping(self, identifier: str, most_specific: bool = False) -> Optional[str]:
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
                ancestors.append([x for x in self.ancestors(m)[::-1] if x in mappings])
            common_ancestors = reduce(lambda s, l: s.intersection(set(l)), ancestors[1:], set(ancestors[0]))
            for a in ancestors[0]:
                if a in common_ancestors:
                    return a

    @lru_cache()
    def _get_element_by_mapping(self, identifier: str) -> Set[str]:
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
        Set[str]
            A set with Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.mappings.get(self.generator.namespaces.uri_for(identifier), set())
        if not mappings:
            exact = self.get_element_by_exact_mapping(identifier)
            mappings.update(exact)
        if not mappings:
            close = self.get_element_by_close_mapping(identifier)
            mappings.update(close)
        if not mappings:
            related = self.get_element_by_related_mapping(identifier)
            mappings.update(related)
        if not mappings:
            narrow = self.get_element_by_narrow_mapping(identifier)
            mappings.update(narrow)
        if not mappings:
            broad = self.get_element_by_broad_mapping(identifier)
            mappings.update(broad)
        return mappings

    @lru_cache()
    def get_element_by_exact_mapping(self, identifier: str) -> Set[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its exact_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE

        Returns
        -------
        Set[str]
            A set with Biolink elements that correspond to the given identifier IRI/CURIE

        """
        return self.generator.exact_mappings.get(self.generator.namespaces.uri_for(identifier), set())

    @lru_cache()
    def get_element_by_close_mapping(self, identifier: str) -> Set[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its close_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE

        Returns
        -------
        Set[str]
            A set with Biolink elements that correspond to the given identifier IRI/CURIE

        """
        return self.generator.close_mappings.get(self.generator.namespaces.uri_for(identifier), set())

    @lru_cache()
    def get_element_by_related_mapping(self, identifier: str) -> Set[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its related_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE

        Returns
        -------
        Set[str]
            A set with Biolink elements that correspond to the given identifier IRI/CURIE

        """
        return self.generator.related_mappings.get(self.generator.namespaces.uri_for(identifier), set())

    @lru_cache()
    def get_element_by_narrow_mapping(self, identifier: str) -> Set[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its narrow_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE

        Returns
        -------
        Set[str]
            A set with Biolink elements that correspond to the given identifier IRI/CURIE

        """
        return self.generator.narrow_mappings.get(self.generator.namespaces.uri_for(identifier), set())

    @lru_cache()
    def get_element_by_broad_mapping(self, identifier: str) -> Set[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its broad_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE

        Returns
        -------
        Set[str]
            A set with Biolink elements that correspond to the given identifier IRI/CURIE

        """
        return self.generator.broad_mappings.get(self.generator.namespaces.uri_for(identifier), set())

    @lru_cache()
    def get_all_elements_by_mapping(self, identifier: str) -> Set[str]:
        """
        Given an identifier as IRI/CURIE, find all Biolink element that corresponds
        to the given identifier as part of its mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE

        Returns
        -------
        Set[str]
            A set with Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.generator.mappings.get(self.generator.namespaces.uri_for(identifier), set())
        exact = self.get_element_by_exact_mapping(identifier)
        mappings.update(exact)
        close = self.get_element_by_close_mapping(identifier)
        mappings.update(close)
        related = self.get_element_by_related_mapping(identifier)
        mappings.update(related)
        narrow = self.get_element_by_narrow_mapping(identifier)
        mappings.update(narrow)
        broad = self.get_element_by_broad_mapping(identifier)
        mappings.update(broad)
        logging.error(mappings)
        return mappings

    @staticmethod
    def _union_of(r: References) -> List[str]:
        """
        Return all references in r

        Parameters
        ----------
        r: biolinkml.utils.typereferences.References

        """
        return list(r.classrefs.union(r.slotrefs.union(r.typerefs).union(r.subsetrefs)))

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

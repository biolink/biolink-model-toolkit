import os
from functools import lru_cache, reduce
from typing import List, Union, TextIO, Optional, Set

from biolinkml.meta import SchemaDefinition, Element, Definition, ClassDefinition, SlotDefinition
from biolinkml.utils.typereferences import References

from .toolkit_generator import ToolkitGenerator

installed_biolink_model_path = os.path.join(os.path.dirname(__file__), 'biolink-model.yaml')

Url = str
Path = str

REMOTE_PATH = 'https://biolink.github.io/biolink-model/biolink-model.yaml'


class Toolkit(object):
    """
    Provides a series of methods for performing lookups on the
    biolink-model.yaml file.
    """

    def __init__(self, schema: Union[Url, Path, TextIO, SchemaDefinition] = REMOTE_PATH) -> None:
        """
        Instantiates a Toolkit object.

        Parameters
        ----------
        schema : Union[str, TextIO, SchemaDefinition]
            The path or url to an instance of the biolink-model.yaml file.
        """
        self.generator = ToolkitGenerator(schema)
        self.generator.serialize()

    @staticmethod
    def _union_of(r: References) -> List[str]:
        """ Return all references in r """
        return list(r.classrefs.union(r.slotrefs.union(r.typerefs).union(r.subsetrefs)))

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
    def ancestors(self, name: str) -> List[str]:
        """
        Gets a list of names of ancestors.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

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
    def descendents(self, name: str) -> List[str]:
        """
        Gets a list of names of descendents.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

        Returns
        -------
        List[str]
            The names of the given elements descendents.
        """
        c = []
        for child in self.children(name):
            c.append(child)
            c += self.descendents(child)
        return c

    @lru_cache()
    def children(self, name: str) -> List[str]:
        """
        Gets a list of names of children.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

        Returns
        -------
        List[str]
            The names of the given elements children.
        """
        return self._union_of(self.generator.synopsis.isarefs.get(name, References()))

    @lru_cache()
    def parent(self, name: str) -> Optional[str]:
        """
        Gets the name of the parent.

        Parameters
        ----------
        name : str
            The name of an element in the biolink model.

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
        name : str
            The name or alias of an element in the biolink model.

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
    def is_edgelabel(self, name: str) -> bool:
        """
        Determines whether the given name is the name of an edge label in the
        biolink model. An element is an edge label just in case it's in the
        `translator_minimal` subset.

        Parameters
        ----------
        name : str
            The name or alias of an element in the biolink model.

        Returns
        -------
        bool
            That the named element is in the translator_minimal subset
        """
        obj = self.generator.obj_for(name)
        return obj is not None and isinstance(obj, Definition) and 'translator_minimal' in obj.in_subset

    @lru_cache()
    def is_category(self, name: str) -> bool:
        """
        Determines whether the given name is the name of a category in the
        biolink model. An element is a category just in case it descends from
        `named thing`

        Parameters
        ----------
        name : str
            The name or alias of an element in the biolink model.

        Returns
        -------
        bool
            That the named element descends from `named thing`
        """
        return 'named thing' in self.ancestors(name)

    @lru_cache()
    def get_all_by_mapping(self, uriorcurie: str) -> Set[str]:
        """
        Gets the set of biolink entities that the given uriorcurie maps to. Mappings
        are determined by the combination of the entity URI (if one exists) combined
        with the entities `mappings` property.

        For example:

              causes:
                description: >-
                  holds between two entities where the occurrence, existence,
                  or activity of one causes the occurrence or  generation of
                  the other
                is_a: contributes to
                in_subset:
                  - translator_minimal
                mappings:
                  - RO:0002410
                  - SEMMEDDB:CAUSES
                  - WD:P1542

        Parameters
        ----------
        uriorcurie : str
            A URI or CURIE (compact URI) identifier of an entity in biolink-model.yaml

        Returns
        -------
        List[str]
            The list of names of entities that the given uriorcurie maps onto
        """
        return self.generator.mappings.get(self.generator.namespaces.uri_for(uriorcurie), {})

    @lru_cache()
    def get_by_mapping(self, uriorcurie: str) -> Optional[str]:
        """
        Return the most distal common ancestor of the set of elements referenced buy uriorcurie


        Parameters
        ----------
        uriorcurie : str
            A URI or CURIE (compact URI) identifier of an entity in biolink-model.yaml

        Returns
        -------
        Optional[str]
            The most distal common ancestor of URI in the model hierarhy
        """
        references = self.get_all_by_mapping(uriorcurie)    # All elements that are referenced
        if not references:
            return None

        mapped_ancestors: List[List[str]] = []              # Ancestors in map by entity ordered by
                                                            # most distal to most proximal, which is
                                                            # always entity
        for e in references:
            # Approach:
            #   For the most distal to the most proximate (which is e) ancestor as a:
            #       if a is included in the map list
            mapped_ancestors.append([a for a in self.ancestors(e)[::-1] if a in references])
        common_ancestors = reduce(
            lambda s, l: s.intersection(set(l)), mapped_ancestors[1:], set(mapped_ancestors[0]))
        for a in mapped_ancestors[0]:
            if a in common_ancestors:
                return a
        return None

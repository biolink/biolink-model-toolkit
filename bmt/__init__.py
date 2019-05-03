import os

from typing import List, Set, Union, TextIO, Optional, TypeVar, Dict

from functools import lru_cache

from metamodel.metamodel import SchemaDefinition, ClassDefinition, SlotDefinition, ClassDefinitionName, \
    TypeDefinition, Element, SlotDefinitionName, TypeDefinitionName, PrefixLocalName

from .toolkit_generator import ToolkitGenerator

installed_biolink_model_path = os.path.join(os.path.dirname(__file__), 'biolink-model.yaml')

Url = str
Path = str

REMOTE_PATH='https://biolink.github.io/biolink-model/biolink-model.yaml'

class Toolkit(object):
    """
    Provides a series of methods for performing lookups on the
    biolink-model.yaml file.
    """

    def __init__(self, schema:Union[Url, Path, TextIO, SchemaDefinition]=REMOTE_PATH) -> ToolkitGenerator:
        """
        Instantiates a Toolkit object.

        Parameters
        ----------
        schema : Union[str, TextIO, SchemaDefinition]
            The path or url to an instance of the biolink-model.yaml file.
        """
        if schema is None:
            self.generator = ToolkitGenerator(path)
            self.generator.serialize()
        else:
            self.generator = ToolkitGenerator(schema)
            self.generator.serialize()

    @staticmethod
    def build_locally() -> ToolkitGenerator:
        """
        Uses the locally installed instance of biolink-model.yaml to instantiate
        a new Toolkit object.

        Returns
        -------
        Toolkit
            An instance that will perform lookups on the locally installed
            instance of the biolink-model.yaml file.
        """
        return Toolkit(schema=installed_biolink_model_path)

    @lru_cache()
    def mappings(self) -> Dict[str, str]:
        """
        Gets all mappings in biolink-model.yaml

        Returns
        -------
        Dict[str, str]
            A mapping of CURIE identifiers onto elements in biolink-model.yaml
        """
        return self.generator.mappings

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
    def ancestors(self, name:str) -> List[str]:
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
        if not isinstance(name, str):
            return []
        try:
            return self.generator.ancestors(name.replace('_', ' '))
        except AttributeError:
            return []

    @lru_cache()
    def descendents(self, name:str) -> List[str]:
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
        if not isinstance(name, str):
            return []
        c = self.children(name)
        for child in c:
            c += self.children(child)
        return c

    @lru_cache()
    def children(self, name:str) -> List[str]:
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
        if not isinstance(name, str):
            return []
        return list(self.generator.children.get(name.replace('_', ' '), []))

    @lru_cache()
    def parent(self, name:str) -> Optional[str]:
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
        if not isinstance(name, str):
            return None
        return self.generator.parent.get(name.replace('_', ' '))

    @lru_cache()
    def get_element(self, name:str) -> Optional[Element]:
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
        if not isinstance(name, str):
            return None
        name = name.replace('_', ' ')
        name = self.generator.aliases.get(name, name)
        return self.generator.obj_for(name)

    @lru_cache()
    def is_edgelabel(self, name:str) -> bool:
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
        if not isinstance(name, str):
            return False
        e = self.get_element(name)
        if e is None:
            return False
        elif e.in_subset is None:
            return False
        else:
            return 'translator_minimal' in e.in_subset

    @lru_cache()
    def is_category(self, name:str) -> bool:
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
        if not isinstance(name, str):
            return False
        return 'named thing' in self.ancestors(name)

    @lru_cache()
    def get_all_by_mapping(self, curie:str) -> List[str]:
        """
        Gets the set of biolink entities that the given curie maps to. Mappings
        are determined by an entities `mappings` property in biolink-model.yaml.

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
        curie : str
            A CURIE (compact URI) identifier of an entity in biolink-model.yaml

        Returns
        -------
        List[str]
            The list of names of entities that the given curie maps onto
        """
        return self.mappings().get(curie, [])

    @lru_cache()
    def get_by_mapping(self, curie:str) -> Optional[str]:
        """
        Gets an entity at the highest level of inheritance that the given
        curie maps to. Mappings are determined by an entities `mappings`
        property in biolink-model.yaml. This method aims to choose the most
        appropriate entity when multiple entities are mapped onto by a given
        CURIE.

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
        curie : str
            A CURIE (compact URI) identifier of an entity in biolink-model.yaml

        Returns
        -------
        Optional[str]
            The name of an entity that the given curie maps onto
        """
        entities = self.get_all_by_mapping(curie)

        for e in entities:
            e = e.replace('_', ' ')
            ancestors = self.ancestors(e)
            try:
                ancestors.remove(e)
            except ValueError:
                pass

            if not any(a in entities for a in ancestors):
                return e

        if entities != []:
            return entities[0]
        else:
            return None

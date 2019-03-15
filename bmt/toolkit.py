import os

from typing import List, Set, Union, TextIO, Optional, TypeVar, Dict

from functools import lru_cache

from metamodel.metamodel import SchemaDefinition, ClassDefinition, SlotDefinition, ClassDefinitionName, \
    TypeDefinition, Element, SlotDefinitionName, TypeDefinitionName, PrefixLocalName

from .toolkit_generator import ToolkitGenerator

path = os.path.join(os.path.dirname(__file__), 'biolink-model.yaml')

Url = str
Path = str

class Toolkit(object):
    def __init__(self, schema:Union[Url, Path, TextIO, SchemaDefinition]=None) -> ToolkitGenerator:
        """
        If provided as a string, schema may be either a url to a remote yaml
        file, or a path to a local yaml file.
        """
        if schema is None:
            self.generator = ToolkitGenerator(path)
            self.generator.serialize()
        else:
            self.generator = ToolkitGenerator(schema)
            self.generator.serialize()

    def mappings(self) -> Dict[str, str]:
        """
        Returns a dictionary mapping CURIE identifiers from other ontologies
        onto elements from the biolink model. This is built from each elements
        `mappings` attribute.
        """
        return self.generator.mappings

    @lru_cache()
    def ancestors(self, s:str) -> List[Element]:
        if not isinstance(s, str):
            return []
        try:
            return self.generator.ancestors(s.replace('_', ' '))
        except AttributeError:
            return []

    @lru_cache()
    def descendents(self, s:str) -> List[Element]:
        if not isinstance(s, str):
            return []
        c = self.children(s)
        for child in c:
            c += self.children(child)
        return c

    @lru_cache()
    def children(self, s:str) -> List[Element]:
        if not isinstance(s, str):
            return []
        return self.generator.children.get(s.replace('_', ' '), [])

    @lru_cache()
    def parent(self, s:str) -> Optional[Element]:
        if not isinstance(s, str):
            return None
        return self.generator.parent.get(s.replace('_', ' '))

    @lru_cache()
    def get_predicate(self, s:str) -> Optional[Element]:
        if not isinstance(s, str):
            return None
        else:
            return self.generator.predicates.get(s.replace('_', ' '))

    @lru_cache()
    def get_class(self, s:str) -> Optional[Element]:
        if not isinstance(s, str):
            return None
        else:
            return self.generator.classes.get(s.replace('_', ' '))

    @lru_cache()
    def get_element(self, name:str) -> Optional[Element]:
        if not isinstance(name, str):
            return None
        return self.generator.obj_for(name.replace('_', ' '))

    @lru_cache()
    def is_edgelabel(self, s:str) -> bool:
        """
        Takes a string and checks that it is in the `translator_minimal` sublist.
        """
        if not isinstance(s, str):
            return False
        e = self.get_element(s)
        is_nonnull = e is not None and e.in_subset is not None
        return is_nonnull and 'translator_minimal' in e.in_subset

    @lru_cache()
    def is_predicate(self, s:str) -> bool:
        """
        Takes a string and checks that the element it refers to inherits from
        "related to".
        """
        if not isinstance(s, str):
            return False
        s = s.replace('_', ' ')
        return s == 'related to' or 'related to' in self.ancestors(s)

    @lru_cache()
    def is_category(self, s:str) -> bool:
        """
        Takes a string and checks that it is a category: that it inherits
        from "named thing"
        """
        if not isinstance(s, str):
            return False
        ancestors = self.ancestors(s)
        return 'named thing' in ancestors and 'association' not in ancestors

    @lru_cache()
    def get_all_by_mapping(self, curie:str) -> Optional[List[str]]:
        """
        Gets the set of biolink entities that the given curie maps to
        """
        return self.mappings().get(curie, [])

    @lru_cache()
    def get_by_mapping(self, curie:str) -> Optional[str]:
        """
        Gets the biolink entity of the highest level of inheritance that the given
        curie maps to. If no such entity exists, arbitrarily chooses one entity
        and returns it.
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

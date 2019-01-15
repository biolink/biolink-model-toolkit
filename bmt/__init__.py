import os

from typing import List, Set, Union, TextIO, Optional, TypeVar

from functools import lru_cache

from metamodel.metamodel import SchemaDefinition, ClassDefinition, SlotDefinition, ClassDefinitionName, \
    TypeDefinition, Element, SlotDefinitionName, TypeDefinitionName, PrefixLocalName

from .toolkit_generator import ToolkitGenerator

path = os.path.join(os.path.dirname(__file__), 'biolink-model.yaml')

generator = None

def load_generator(schema:Union[str, TextIO, SchemaDefinition]=None) -> ToolkitGenerator:
    """
    Loads the generator object that is used for each of the methods in this file
    """
    global generator

    if generator is None or schema is not None:
        if schema is None:
            generator = ToolkitGenerator(path)
            generator.serialize()
        else:
            generator = ToolkitGenerator(schema)
            generator.serialize()

        ancestors.cache_clear()
        descendents.cache_clear()
        is_edgelabel.cache_clear()
        is_category.cache_clear()
        get_element.cache_clear()
        get_all_by_mapping.cache_clear()
        get_by_mapping.cache_clear()

    return generator

@lru_cache()
def ancestors(s:str) -> Optional[Element]:
    try:
        return load_generator().ancestors(s.replace('_', ' '))
    except AttributeError:
        return []

@lru_cache()
def descendents(s:str) -> Optional[Element]:
    c = children(s)
    for child in c:
        c += children(child)
    return c

def children(s:str) -> List[Element]:
    return load_generator().children.get(s.replace('_', ' '), [])

def parent(s:str) -> Optional[Element]:
    return load_generator().parent.get(s.replace('_', ' '))

@lru_cache()
def is_edgelabel(s:str) -> bool:
    """
    Takes a string and checks that it is an edge label, that is checks that the
    entity it refers to inherits from "related to" and uses underscores rather
    than spaces.
    """
    if ' ' in s:
        return False
    else:
        return 'related to' in ancestors(s.replace('_', ' '))

@lru_cache()
def is_category(s:str) -> bool:
    """
    Takes a string and checks that it is a category: that it inherits
    from "named thing"
    """
    ancestors = ancestors(s)
    return 'named thing' in ancestors and 'association' not in ancestors

@lru_cache()
def get_element(name:str) -> Optional[Element]:
    return load_generator().obj_for(name.replace('_', ' '))

@lru_cache()
def get_all_by_mapping(curie:str) -> Optional[List[str]]:
    """
    Gets the set of biolink entities that the given curie maps to
    """
    return list(load_generator().mappings.get(curie, []))

@lru_cache()
def get_by_mapping(curie:str) -> Optional[str]:
    """
    Gets the biolink entity of the highest level of inheritance that the given
    curie maps to. If no such entity exists, arbitrarily chooses one entity
    and returns it.
    """
    entities = get_all_by_mapping(curie)

    for e in entities:
        e = e.replace('_', ' ')
        ancestors = ancestors(e)
        ancestors.remove(e)
        if not any(a in entities for a in ancestors):
            return e

    if entities != []:
        return entities[0]
    else:
        return None

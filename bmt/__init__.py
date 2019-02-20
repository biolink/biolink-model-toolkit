"""
Contains a series of methods for using the biolink model. A new Toolkit may be
loaded loaded like this:

>>> import bmt
>>> bmt.load('https://biolink.github.io/biolink-model/biolink-model.yaml')

If load is never manually called then a default copy will be used.

Each of these methods are cached. But that cache is reset each time load is
called.

Alternatively, you can use your own instance of Toolkit if you want to avoid
using global variables.
"""

from typing import List, Set, Union, TextIO, Optional, TypeVar

from metamodel.metamodel import SchemaDefinition, ClassDefinition, SlotDefinition, ClassDefinitionName, \
    TypeDefinition, Element, SlotDefinitionName, TypeDefinitionName, PrefixLocalName

from .toolkit import Toolkit

toolkit = None

def load(schema:Union[str, TextIO, SchemaDefinition]=None) -> Toolkit:
    """
    Loads the generator object that is used for each of the methods in this file
    """
    global toolkit

    if toolkit is None or schema is not None:
        toolkit = Toolkit(schema)

    return toolkit

def get_predicate(s:str) -> Optional[Element]:
    return load().get_predicate(s)

def get_class(s:str) -> Optional[Element]:
    return load().get_class(s)

def ancestors(s:str) -> Optional[Element]:
    return load().ancestors(s)

def descendents(s:str) -> Optional[Element]:
    return load().descendents(s)

def children(s:str) -> List[Element]:
    return load().children(s)

def parent(s:str) -> Optional[Element]:
    return load().parent(s)

def is_edgelabel(s:str) -> bool:
    """
    Takes a string and checks that it is in the `translator_minimal` sublist.
    """
    return load().is_edgelabel(s)

def is_predicate(s:str) -> bool:
    """
    Takes a string and checks that the element it refers to inherits from
    "related to".
    """
    return load().is_predicate(s)

def is_category(s:str) -> bool:
    """
    Takes a string and checks that it is a category: that it inherits
    from "named thing"
    """
    return load().is_category(s)

def get_element(name:str) -> Optional[Element]:
    return load().get_element(name)

def get_all_by_mapping(curie:str) -> Optional[List[str]]:
    """
    Gets the set of biolink entities that the given curie maps to
    """
    return load().get_all_by_mapping(curie)

def get_by_mapping(curie:str) -> Optional[str]:
    """
    Gets the biolink entity of the highest level of inheritance that the given
    curie maps to. If no such entity exists, arbitrarily chooses one entity
    and returns it.
    """
    return load().get_by_mapping(curie)

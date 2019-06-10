from collections import defaultdict
from typing import Union, TextIO, Dict, Set, Optional, List

from biolinkml.meta import SchemaDefinition, ClassDefinition, SlotDefinition, TypeDefinition, Element, SubsetDefinition
from biolinkml.utils.generator import Generator


class ToolkitGenerator(Generator):
    """
    A shell of an implementation of Generator, for the sole purpose of accessing
    it's methods.
    """
    valid_formats = [None]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.mappings: Dict[str, Set[str]] = defaultdict(set)   # URI to slot names
        self.aliases: Dict[str, str] = dict()                   # Alias to reference

    def visit_element(self, element: Element, element_uri: Optional[str]) -> None:
        for curie in element.mappings:
            self.mappings[self.namespaces.uri_for(curie)].add(element.name)
        if element_uri:
            self.mappings[self.namespaces.uri_for(element_uri)].add(element.name)
        self.aliases.update({a: element.name for a in element.aliases})

    def visit_slot(self, aliased_slot_name: str, slot: SlotDefinition) -> None:
        self.visit_element(slot, slot.slot_uri)
        self.aliases.update({a: slot.name for a in slot.aliases})

    def visit_type(self, typ: TypeDefinition) -> None:
        self.visit_element(typ, typ.uri)

    def visit_class(self, cls: ClassDefinition) -> bool:
        self.visit_element(cls, cls.class_uri)
        return False

    def visit_subset(self, subset: SubsetDefinition) -> None:
        self.visit_element(subset, None)

from typing import List, Union, TextIO

from metamodel.metamodel import SchemaDefinition, ClassDefinition, SlotDefinition, ClassDefinitionName, \
    TypeDefinition, Element, SlotDefinitionName, TypeDefinitionName, PrefixLocalName
from metamodel.utils.generator import Generator, SLOT_OR_SLOTNAME, CLASS_OR_CLASSNAME

from collections import defaultdict

class ToolkitGenerator(Generator):
    """
    A shell of an implementation of Generator, for the sole purpose of accessing
    it's methods.
    """
    valid_formats = [None]
    def __init__(self, schema: Union[str, TextIO, SchemaDefinition]) -> None:
        super().__init__(schema, None)

        self.mappings = defaultdict(set)
        self.children = defaultdict(list)
        self.parent = dict()

    def visit_slot(self, aliased_slot_name: str, slot: SlotDefinition) -> None:
        ancestors = self.ancestors(slot)
        if 'related to' in ancestors:
            slot.edge_label = slot.name.replace(' ', '_')

            for curie in slot.mappings:
                self.mappings[curie].add(slot.edge_label)

            self.children[slot.is_a].append(slot.name)
            self.parent[slot.name] = slot.is_a

    def visit_class(self, cls: ClassDefinition) -> bool:
        ancestors = self.ancestors(cls)
        if 'named thing' in ancestors:
            for curie in cls.mappings:
                self.mappings[curie].add(cls.name)

            self.children[cls.is_a].append(cls.name)
            self.parent[cls.name] = cls.is_a

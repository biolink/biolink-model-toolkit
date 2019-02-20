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
        self.predicates = {}
        self.classes = {}

    def add_predicate(self, s:str, e:Element):
        if s not in self.predicates:
            self.predicates[s] = e
        elif s != self.predicates[s].name:
            raise Exception(f'Predicate {s} already identifies {self.predicates[s].name}')

    def add_class(self, s:str, e:Element):
        if s not in self.classes:
            self.classes[s] = e
        elif s != self.classes[s].name:
            raise Exception(f'Class {s} already identifies {self.classes[s].name}')

    def visit_slot(self, aliased_slot_name: str, slot: SlotDefinition) -> None:
        ancestors = self.ancestors(slot)
        if 'related to' in ancestors:
            slot.edge_label = slot.name.replace(' ', '_')

            self.add_predicate(slot.name, slot)
            for alias in slot.aliases:
                self.add_predicate(alias, slot)

            for curie in slot.mappings:
                self.mappings[curie].add(slot.edge_label)

            self.children[slot.is_a].append(slot.name)
            self.parent[slot.name] = slot.is_a

    def visit_class(self, cls: ClassDefinition) -> bool:
        ancestors = self.ancestors(cls)
        if 'named thing' in ancestors:
            for curie in cls.mappings:
                self.mappings[curie].add(cls.name)

            self.add_class(cls.name, cls)
            for alias in cls.aliases:
                self.add_class(alias, cls)

            self.children[cls.is_a].append(cls.name)
            self.parent[cls.name] = cls.is_a

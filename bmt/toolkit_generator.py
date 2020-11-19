from collections import defaultdict
from typing import Union, TextIO, Dict, Set, Optional, List

from biolinkml.meta import SchemaDefinition, ClassDefinition, SlotDefinition, TypeDefinition, Element, SubsetDefinition, \
    ElementName
from biolinkml.utils.generator import Generator
from biolinkml.utils.typereferences import References


class ToolkitGenerator(Generator):
    """
    An extension to biolinkml.utils.generator.Generator for accessing the Biolink Model.

    Parameters
    ----------
    *args: Dict
        Arguments
    **kwargs: Dict
        Additional arguments

    """
    valid_formats = [None]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mappings: Dict[str, Set[str]] = defaultdict(set)
        self.exact_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.close_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.related_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.narrow_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.broad_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.aliases: Dict[str, str] = dict()

    def visit_element(self, element: Element, element_uri: Optional[str]) -> None:
        """
        Given an element and an element URI (optional), visit the element
        in the Biolink Model and pull the necessary properties corresponding
        to that element.

        Parameters
        ----------
        element: biolinkml.meta.Element
            The element to access
        element_uri: Optional[str]
            The URI for the element

        """
        for curie in element.mappings:
            self.mappings[self.namespaces.uri_for(curie)].add(element.name)
        for curie in element.exact_mappings:
            self.exact_mappings[self.namespaces.uri_for(curie)].add(element.name)
        for curie in element.close_mappings:
            self.close_mappings[self.namespaces.uri_for(curie)].add(element.name)
        for curie in element.related_mappings:
            self.related_mappings[self.namespaces.uri_for(curie)].add(element.name)
        for curie in element.narrow_mappings:
            self.narrow_mappings[self.namespaces.uri_for(curie)].add(element.name)
        for curie in element.broad_mappings:
            self.broad_mappings[self.namespaces.uri_for(curie)].add(element.name)
        if element_uri:
            self.mappings[self.namespaces.uri_for(element_uri)].add(element.name)
        self.aliases.update({a: element.name for a in element.aliases})

    def visit_slot(self, aliased_slot_name: str, slot: SlotDefinition) -> None:
        """
        Given a slot, visit the slot in the Biolink Model and pull necessary
        properties corresponding to that slot.

        Parameters
        ----------
        aliased_slot_name: str
            Alias name of the slot
        slot: biolinkml.meta.SlotDefinition
            The slot definition

        """
        self.visit_element(slot, slot.slot_uri)
        self.aliases.update({a: slot.name for a in slot.aliases})

    def visit_type(self, typ: TypeDefinition) -> None:
        """
        Given a type, visit the type in the Biolink Model and pull necessary
        properties corresponding to that type.

        Parameters
        ----------
        typ: biolinkml.meta.TypeDefinition
            The type definition

        """
        self.visit_element(typ, typ.uri)

    def visit_class(self, cls: ClassDefinition) -> bool:
        """
        Given a class, visit the class in the Biolink Model and pull necessary
        properties corresponding to that class.

        Parameters
        ----------
        cls: biolinkml.meta.ClassDefinition
            The class definition

        """
        self.visit_element(cls, cls.class_uri)
        return False

    def visit_subset(self, subset: SubsetDefinition) -> None:
        """
        Given a subset, visit the subset in the Biolink Model and pull necessary
        properties corresponding to that class.

        Parameters
        ----------
        subset: biolinkml.meta.SubsetDefinition
            The subset definition
        """
        self.visit_element(subset, None)

    def ancestors(self, element: Union[ClassDefinition, SlotDefinition]) -> List[ElementName]:
        """
        Return an ordered list of ancestor names for the supplied slot or class.

        Parameters
        ----------
        element: Union[ClassDefinition, SlotDefinition]
            An element

        """
        return [element.name] + ([] if element.is_a is None else self.ancestors(self.parent(element)))

    def descendants(self, element_name: str):
        """
        Return an ordered list of descendant names for the supplied slot or class.

        Parameters
        ----------
        element_name: Union[ClassDefinition, SlotDefinition]
            An element

        """
        c = []
        for child in self.children(element_name):
            c.append(child)
            c += self.descendants(child)
        return c

    def children(self, name: str) -> List[str]:
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
        return self._union_of(self.synopsis.isarefs.get(name, References()))

    @staticmethod
    def _union_of(r: References) -> List[str]:
        """
        Return all references in r

        Parameters
        ----------
        r: biolinkml.utils.typereferences.References

        """
        return list(r.classrefs.union(r.slotrefs.union(r.typerefs).union(r.subsetrefs)))

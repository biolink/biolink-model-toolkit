from collections import defaultdict
from typing import Union, Dict, Set, Optional, List

from linkml_runtime.linkml_model.meta import (
    ClassDefinition,
    SlotDefinition,
    TypeDefinition,
    Element,
    SubsetDefinition,
    ElementName,
)
from linkml.utils.generator import Generator
from linkml.utils.typereferences import References


class ToolkitGenerator(Generator):
    """
    An extension to linkml.utils.generator.Generator for accessing the Biolink Model.

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
        self.id_prefixes: Dict[str, Set[str]] = defaultdict(set)

    def visit_element(self, element: Element, element_uri: Optional[str]) -> None:
        """
        Given an element and an element URI (optional), visit the element
        in the Biolink Model and pull the necessary properties corresponding
        to that element.

        Parameters
        ----------
        element: linkml_runtime.linkml_model.meta.Element
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
        for id_prefix in element.id_prefixes:
            self.id_prefixes[element.name].add(id_prefix)
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
        slot: linkml_runtime.linkml_model.meta.SlotDefinition
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
        typ: linkml_runtime.linkml_model.meta.TypeDefinition
            The type definition

        """
        self.visit_element(typ, typ.uri)

    def visit_class(self, cls: ClassDefinition) -> bool:
        """
        Given a class, visit the class in the Biolink Model and pull necessary
        properties corresponding to that class.

        Parameters
        ----------
        cls: linkml_runtime.linkml_model.meta.ClassDefinition
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
        subset: linkml_runtime.linkml_model.meta.SubsetDefinition
            The subset definition
        """
        self.visit_element(subset, None)

    def obj_for(
        self, el_or_elname: str, is_range_name: bool = False
    ) -> Optional[Element]:
        """
        Get object for a given element name.

        Parameters
        ----------
        el_or_elname: str
            The element or element name
        is_range_name: bool
            If True, then that means we are looking for a class or type

        Returns
        -------
        Optional[Element]
            An instance of Element corresponding to the given name

        """
        element_obj = None
        if el_or_elname in self.schema.classes:
            element_obj = self.class_or_type_for(el_or_elname)
        elif el_or_elname in self.schema.slots:
            element_obj = self.slot_for(el_or_elname)
        elif (
            el_or_elname in self.schema.types
            or el_or_elname == self.schema.default_range
        ):
            element_obj = self.class_or_type_for(el_or_elname)
        elif el_or_elname in self.schema.subsets:
            element_obj = self.subset_for(el_or_elname)
        else:
            element_obj = self.class_or_type_for(el_or_elname)

        if not element_obj:
            # try case-insensitive match
            classes = {k.lower(): v for k, v in self.schema.classes.items()}
            slots = {k.lower(): v for k, v in self.schema.slots.items()}
            types = {k.lower(): v for k, v in self.schema.types.items()}
            subsets = {k.lower(): v for k, v in self.schema.subsets.items()}
            el_or_elname_lower = el_or_elname.lower()
            if el_or_elname_lower in classes:
                element_obj = self.class_or_type_for(classes[el_or_elname_lower].name)
            elif el_or_elname_lower in slots:
                element_obj = self.slot_for(slots[el_or_elname_lower].name)
            elif (
                el_or_elname_lower in types
                or el_or_elname_lower == self.schema.default_range
            ):
                element_obj = self.class_or_type_for(types[el_or_elname_lower].name)
            elif el_or_elname_lower in self.schema.subsets:
                element_obj = self.subset_for(subsets[el_or_elname_lower].name)
            else:
                element_obj = self.class_or_type_for(el_or_elname_lower)

        return element_obj

    def ancestors(
        self, element: Union[ClassDefinition, SlotDefinition]
    ) -> List[ElementName]:
        """
        Return an ordered list of ancestor names for the supplied slot or class.

        Parameters
        ----------
        element: Union[ClassDefinition, SlotDefinition]
            An element
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        """
        return [element.name] + (
            [] if element.is_a is None else self.ancestors(self.parent(element))
        )

    def descendants(self, element_name: str, mixin: bool = True):
        """
        Return an ordered list of descendant names for the supplied slot or class.

        Parameters
        ----------
        element_name: Union[ClassDefinition, SlotDefinition]
            An element
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        """
        c = []
        for child in self.children(element_name, mixin):
            c.append(child)
            c += self.descendants(child, mixin)
        return c

    def children(self, name: str, mixin: bool = True) -> List[str]:
        """
        Gets a list of names of children.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model.
        mixin: bool
            If True, then that means we want to find mixin children as well as is_a children

        Returns
        -------
        List[str]
            The names of the given elements children.

        """
        kids_or_mixin_kids = []
        if mixin:
            for mixin in self._union_of(
                self.synopsis.mixinrefs.get(name, References())
            ):
                kids_or_mixin_kids.append(mixin)
            for kid in self._union_of(self.synopsis.isarefs.get(name, References())):
                kids_or_mixin_kids.append(kid)
        else:
            for kid in self._union_of(self.synopsis.isarefs.get(name, References())):
                kids_or_mixin_kids.append(kid)
        return kids_or_mixin_kids

    @staticmethod
    def _union_of(r: References) -> List[str]:
        """
        Return all references in r

        Parameters
        ----------
        r: linkml.utils.typereferences.References

        """
        return list(r.classrefs.union(r.slotrefs.union(r.typerefs).union(r.subsetrefs)))

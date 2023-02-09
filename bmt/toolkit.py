import logging
import yaml
import csv
import deprecation
import requests
from oaklib.implementations import UbergraphImplementation
from functools import lru_cache, reduce

from typing import List, Union, TextIO, Optional, Dict
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.linkml_model.meta import (
    SchemaDefinition,
    Element,
    ElementName,
    Definition,
    ClassDefinition,
    SlotDefinition,
)
from pprint import pprint

from bmt.utils import format_element, parse_name

Url = str
Path = str

REMOTE_PATH = "https://raw.githubusercontent.com/biolink/biolink-model/v3.2.1/biolink-model.yaml"
PREDICATE_MAP = 'https://raw.githubusercontent.com/biolink/biolink-model/v3.2.1/predicate_mapping.yaml'
INFORES_MAP = 'https://raw.githubusercontent.com/biolink/biolink-model/v3.2.1/infores_catalog_nodes.tsv'

NODE_PROPERTY = "node property"
ASSOCIATION_SLOT = "association slot"
RELATED_TO = "related to"

CACHE_SIZE = 1024

logger = logging.getLogger(__name__)


class Toolkit(object):
    """
    Provides a series of methods for performing lookups on the Biolink Model

    Parameters
    ----------
    schema: Union[str, TextIO, SchemaDefinition]
        The path or url to an instance of the biolink-model.yaml file.

    """

    def __init__(
            self, schema: Union[Url, Path, TextIO, SchemaDefinition] = REMOTE_PATH,
            predicate_map: Url = PREDICATE_MAP,
            infores_map: Url = INFORES_MAP
    ) -> None:
        self.oi = UbergraphImplementation()
        self.view = SchemaView(schema)
        r = requests.get(predicate_map)
        self.pmap = yaml.safe_load(r.text)

        r = requests.get(infores_map)
        content = r.content.decode('iso-8859-1')
        self.infores_map = {}
        for line in csv.reader(content.splitlines(), delimiter='\t'):
            if line[2] == 'id':
                continue
            self.infores_map[line[2]] = {
                "status": line[0],
                "name": line[1],
                "url": line[3],
                "synonyms": line[4],
                "has_contributor": line[6],
                "description": line[7],
                "category": line[8]
            }

    @lru_cache(CACHE_SIZE)
    def get_all_elements(self, formatted: bool = False) -> List[str]:
        """
        Get all elements from Biolink Model.

        This method returns a list containing all
        classes, slots, and types defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        classes = self.get_all_classes(formatted)
        slots = self.get_all_slots(formatted)
        types = self.get_all_types(formatted)
        all_elements = classes + slots + types
        return all_elements

    @lru_cache(CACHE_SIZE)
    def get_all_classes(self, formatted: bool = False) -> List[str]:
        """
        Get all classes from Biolink Model.

        This method returns a list containing all the
        classes defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        classes = []
        for x in self.view.schema.classes:
            classes.append(x)
        filtered_classes = self._filter_secondary(classes)
        return self._format_all_elements(filtered_classes, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_slots(self, formatted: bool = False) -> List[str]:
        """
        Get all slots from Biolink Model.

        This method returns a list containing all the
        slots defined in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        slots = []
        for x in self.view.schema.slots:
            slots.append(x)
        filtered_slots = self._filter_secondary(slots)
        return self._format_all_elements(filtered_slots, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_types(self, formatted: bool = False) -> List[str]:
        """
        Get all types from Biolink Model.

        This method returns a list containing all the
        built-in and defined types in the model.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        types = []
        for x in self.view.all_types():
            types.append(x)
        return self._format_all_elements(types, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_entities(self, formatted: bool = False) -> List[str]:
        """
        Get all entities from Biolink Model.

        This method returns a list containing all the classes
        that are descendants of the class ``named thing``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_descendants("named thing")
        return self._format_all_elements(elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_associations(self, formatted: bool = False) -> List[str]:
        """
        Get all associations from Biolink Model.

        This method returns a list containing all the classes
        that are descendants of the class ``association``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_descendants("association")
        return self._format_all_elements(elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_node_properties(self, formatted: bool = False) -> List[str]:
        """
        Get all node properties from Biolink Model.

        This method returns a list containing all the slots
        that are descendants of the slot ``node property``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_all_slots_with_class_domain("entity")
        elements += self.get_descendants("node property")
        filtered_elements = self._filter_secondary(elements)
        return self._format_all_elements(filtered_elements, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_edge_properties(self, formatted: bool = False) -> List[str]:
        """
        Get all edge properties from Biolink Model.

        This method returns a list containing all the slots
        that are descendants of the slot ``association slot``.

        Parameters
        ----------
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of elements

        """
        elements = self.get_all_slots_with_class_domain("entity")
        elements += self.get_descendants("association slot")
        filtered_elements = self._filter_secondary(elements)
        return self._format_all_elements(filtered_elements, formatted)

    def _filter_secondary(self, elements: List[str]) -> List[str]:
        """
        From a given list of elements, remove elements that are not proper slots.

        This method removes spurious slots like ``gene_to_gene_association_subject``
        that are artifact of domain/range constraints and not actual slots.

        Parameters
        ----------
        elements: List[str]
            List of elements

        Returns
        -------
        List[str]
            A filtered list of elements

        """
        filtered_elements = []
        for e in elements:
            eo = self.view.get_element(e)
            if isinstance(eo, SlotDefinition):
                if not eo.alias:
                    filtered_elements.append(e)
            else:
                filtered_elements.append(e)
        return filtered_elements

    @lru_cache(CACHE_SIZE)
    def get_permissible_value_ancestors(self, permissible_value: str, enum_name: str, formatted: bool = False) -> List[
        str]:
        """
        Get ancestors of a permissible value.

        This method returns a list containing all the ancestors of a
        permissible value of a given enum.

        Parameters
        ----------
        enum_name: str
            The name of the enum
        permissible_value: str
            The name of the permissible value

        Returns
        -------
        List[str]
            A list of elements

        """
        ancestors = self.view.permissible_value_ancestors(permissible_value, enum_name)
        if formatted:
            return self._format_all_elements(ancestors)
        return ancestors

    @lru_cache(CACHE_SIZE)
    def get_infores_details(self, infores_id: str):
        """
        Get details of an information resource.

        This method returns a dictionary containing details of a given
        information resource.

        Parameters
        ----------
        infores_id: str
            The identifier of the information resource

        Returns
        -------
        Dict[str, Any]
            A dictionary containing details of the information resource

        """
        pprint(self.infores_map)
        infores = self.infores_map.get(infores_id)
        return infores

    @lru_cache(CACHE_SIZE)
    def get_predicate_mapping(self, mapped_predicate: str) -> Dict[str, str]:
        """
        Get the predicates that map to a given predicate.

        This method returns a list containing all the predicates that map to
        a given predicate.

        Parameters
        ----------
        mapped_predicate: str
            The name of the mapped predicate

        Returns
        -------
        List[str]
            A list of elements

        """
        association = {}

        for mp in self.pmap.values():
            for item in mp:
                if item['mapped predicate'] == mapped_predicate:
                    for k, v in item.items():
                        association[format_element(self.get_element(k))] = v
        return association

    @lru_cache(CACHE_SIZE)
    def get_permissible_value_parent(self, permissible_value: str, enum_name: str) -> str:
        """
        Get parent of a permissible value.

        This method returns a list containing all the parent of a
        permissible value of a given enum.

        Parameters
        ----------
        enum_name: str
            The name of the enum
        permissible_value: str
            The name of the permissible value

        Returns
        -------
        List[str]
            A list of elements

        """
        parent = self.view.permissible_value_parent(permissible_value, enum_name)
        return parent

    @lru_cache(CACHE_SIZE)
    def get_ancestors(
            self,
            name: str,
            reflexive: bool = True,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Gets a list of names of ancestors.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        reflexive: bool
            Whether to include the query element in the list of ancestors
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            The names of the given elements ancestors

        """
        element = self.get_element(name)
        ancs = []
        if isinstance(element, ClassDefinition):
            ancs = self.view.class_ancestors(element.name, mixins=mixin, reflexive=reflexive)
        if isinstance(element, SlotDefinition):
            ancs = self.view.slot_ancestors(element.name, mixins=mixin, reflexive=reflexive)
            filtered_ancs = self._filter_secondary(ancs)
        else:
            filtered_ancs = ancs
        return self._format_all_elements(filtered_ancs, formatted)

    def _get_mixin_descendants(self, ancestors: List[ElementName]) -> List[ElementName]:
        mixins_parents = []
        for ancestor in ancestors:
            a_element = self.get_element(ancestor)
            if a_element.mixins:
                for mixin in a_element.mixins:
                    mixin_element = self.get_element(mixin)
                    mixin_parents = self.view.ancestors(mixin_element)
                    mixins_parents = mixins_parents + mixin_parents
        return mixins_parents

    @lru_cache(CACHE_SIZE)
    def get_descendants(
            self,
            name: str,
            reflexive: bool = True,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Gets a list of names of descendants.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        reflexive: bool
            Whether to include the query element in the list of ancestors
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            The names of the given element's descendants

        """
        desc = []
        filtered_desc = []
        element = self.get_element(name)

        if element:
            if isinstance(element, ClassDefinition):
                desc = self.view.class_descendants(element.name, mixins=mixin, reflexive=reflexive)
            if isinstance(element, SlotDefinition):
                desc = self.view.slot_descendants(element.name, mixins=mixin, reflexive=reflexive)
                filtered_desc = self._filter_secondary(desc)
            else:
                filtered_desc = desc
        else:
            raise ValueError("not a valid biolink component")

        return self._format_all_elements(filtered_desc, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_multivalued_slots(self) -> List[str]:
        """
        Gets a list of names of all multivalued slots.

        Returns
        -------
        List[str]
            The names of all multivalued slots

        """
        multivalued_slots = []
        slots = self.view.all_slots()
        for slot_name, slot_def in slots.items():
            if self.view.is_multivalued(slot_name):
                multivalued_slots.append(slot_name)
        return multivalued_slots

    @lru_cache(CACHE_SIZE)
    def get_children(
            self, name: str, formatted: bool = False, mixin: bool = True
    ) -> List[str]:
        """
        Gets a list of names of children.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            The names of the given elements children

        """
        children = []
        element = self.get_element(name)
        if element:
            children = self.view.get_children(element.name, mixin)
        return self._format_all_elements(children, formatted)

    @lru_cache(CACHE_SIZE)
    def get_parent(self, name: str, formatted: bool = False) -> Optional[str]:
        """
        Gets the name of the parent.

        Parameters
        ----------
        name: str
            The name of an element in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        Optional[str]
            The name of the given elements parent

        """
        parent = None
        element = self.get_element(name)
        if element:
            p = element.is_a if isinstance(element, Definition) else None
            if p and formatted:
                parent = format_element(p)
            else:
                parent = p
        return parent

    @lru_cache(CACHE_SIZE)
    def get_element(self, name: str) -> Optional[Element]:
        """
        Gets an element that is identified by the given name, either as its name
        or as one of its aliases.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        Element
            The element identified by the given name

        """
        parsed_name = parse_name(name)
        logger.debug(parsed_name)
        element = self.view.get_element(parsed_name)
        if element is None and self.view.all_aliases() is not None:
            for e in self.view.all_aliases():
                if name in self.view.all_aliases()[e]:
                    element = self.view.get_element(e)
        if element is None and "_" in name:
            element = self.get_element(name.replace("_", " "))
        if element is None:
            for e, el in self.view.all_elements().items():
                if el.name.lower() == name.lower():
                    element = el
        return element

    def get_slot_domain(
            self,
            slot_name,
            include_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Get the domain for a given slot.

        Parameters
        ----------
        slot_name: str
            The name or alias of a slot in the Biolink Model
        include_ancestors: bool
            Whether or not to include ancestors of the domain class
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            The domain for a given slot

        """
        slot_domain = []
        domain_classes = set()
        element = self.get_element(slot_name)
        if element and element.domain:
            domain_classes.add(element.domain)
            if include_ancestors:
                slot_domain.extend(
                    self.get_ancestors(element.domain, reflexive=True, mixin=mixin)
                )
            else:
                slot_domain.append(element.domain)
        for d in element.domain_of:
            if d not in domain_classes:
                if include_ancestors:
                    slot_domain.extend(
                        self.get_ancestors(d, reflexive=True, mixin=mixin)
                    )
                else:
                    slot_domain.append(d)
        return self._format_all_elements(slot_domain, formatted)

    def get_slot_range(
            self,
            slot_name,
            include_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Get the range for a given slot.

        Parameters
        ----------
        slot_name: str
            The name or alias of a slot in the Biolink Model
        include_ancestors: bool
            Whether or not to include ancestors of the range class
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors


        Returns
        -------
        List[str]
            The range for a given slot

        """
        slot_range = []
        element = self.get_element(slot_name)
        if element and element.range:
            slot_range.append(element.range)
            if include_ancestors:
                ancs = self.get_ancestors(element.range, reflexive=False, mixin=mixin)
                slot_range.extend(ancs)
        return self._format_all_elements(slot_range, formatted)

    def validate_qualifier(self, qualifier_type_id: str, qualifier_value: str) -> bool:
        """
        Validates a qualifier.

        Parameters
        ----------
        qualifier_type_id: str
            The name or alias of a qualifier in the Biolink Model
        qualifier_value: str
            The value of the qualifier

        Returns
        -------
        bool
            Whether or not the given qualifier is valid

        """
        if self.is_qualifier(qualifier_type_id):
            qualifier_slot = self.view.get_slot(qualifier_type_id)
            if qualifier_slot and self.is_enum(qualifier_slot.range):
                enum = self.view.get_enum(qualifier_slot.range)
                if self.is_permissible_value_of_enum(enum.name, qualifier_value):
                    return True
        return False

    def get_all_slots_with_class_domain(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all the slots where the class is the domain.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        element = self.get_element(class_name)
        slots = self._get_all_slots_with_class_domain(element, check_ancestors, mixin)
        slot_names = [x.name for x in slots]
        return self._format_all_elements(slot_names, formatted)

    def get_all_slots_with_class_range(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all the slots where the class is the range.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        element = self.get_element(class_name)
        slots = self._get_all_slots_with_class_range(element, check_ancestors, mixin)
        slot_names = [x.name for x in slots]
        return self._format_all_elements(slot_names, formatted)

    def get_all_predicates_with_class_domain(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all Biolink predicates where the class is the domain.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_domain(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_all_predicates_with_class_range(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ):
        """
        Given a class, get all Biolink predicates where the class is the range.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_range(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_all_properties_with_class_domain(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all Biolink properties where the class is the domain.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_domain(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO not in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_all_properties_with_class_range(
            self,
            class_name,
            check_ancestors: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> List[str]:
        """
        Given a class, get all Biolink properties where the class is the range.

        Parameters
        ----------
        class_name: str
            The name or alias of a class in the Biolink Model
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[str]
            A list of slots

        """
        filtered_slots = []
        element = self.get_element(class_name)
        if element:
            slots = self._get_all_slots_with_class_range(
                element, check_ancestors, mixin
            )
            for s in slots:
                if not s.alias and RELATED_TO not in self.get_ancestors(s.name, mixin):
                    filtered_slots.append(s.name)
        return self._format_all_elements(filtered_slots, formatted)

    def get_value_type_for_slot(self, slot_name, formatted: bool = False) -> str:
        """
        Get the value type for a given slot.

        Parameters
        ----------
        slot_name: str
            The name or alias of a slot in the Biolink Model
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        str
            The slot type

        """
        element_type = None
        element = self.get_element(slot_name)
        if element:
            types = self.get_all_types()
            if element.range is None and self.view.schema.default_range:
                element.range = self.view.schema.default_range
            if element.range in types:
                et = element.range
            else:
                et = "uriorcurie"
            if formatted:
                element_type = format_element(self.view.get_element(et))
            else:
                element_type = et
        return element_type

    def _get_all_slots_with_class_domain(
            self, element: Element, check_ancestors: bool, mixin: bool = True
    ) -> List[Element]:
        """
        Given a class, get all the slots where the class is the domain.

        Parameters
        ----------
        element: linkml_model.meta.Element
            An element
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its domain
        mixin:
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[linkml_model.meta.Element]
            A list of slots

        """
        slots = []
        for k, v in self.view.schema.slots.items():
            if check_ancestors:
                if (v.domain == element.name or v.domain in self.get_ancestors(element.name, mixin)
                        or element.name in v.domain_of
                        or any(v.domain_of) in self.get_ancestors(element.name, mixin)):
                    slots.append(v)
            else:
                if element.name == v.domain or element.name in v.domain_of:
                    slots.append(v)
        return slots

    def _get_all_slots_with_class_range(
            self, element: Element, check_ancestors: bool, mixin: bool = True
    ) -> List[Element]:
        """
        Given a class, get all the slots where the class is the range.

        Parameters
        ----------
        element: linkml_model.meta.Element
            An element
        check_ancestors: bool
            Whether or not to lookup slots that include ancestors of the given class as its range
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        List[linkml_model.meta.Element]
            A list of slots

        """
        slots = []
        for k, v in self.view.schema.slots.items():
            if check_ancestors:
                if v.range == element.name or v.range in self.get_ancestors(
                        element.name, mixin
                ):
                    slots.append(v)
            else:
                if v.range and element.name == v.range:
                    slots.append(v)
        return slots

    @lru_cache(CACHE_SIZE)
    def is_node_property(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a node property
        in the Biolink Model. An element is a node property if it descends from
        `NODE_PROPERTY`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid node property in Biolink Model
        """
        return NODE_PROPERTY in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def is_association_slot(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of an association slot
        in the Biolink Model. An element is an association slot if it descends from
        `ASSOCIATION_SLOT`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid an association slot in Biolink Model
        """
        return ASSOCIATION_SLOT in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def is_predicate(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a relation/predicate
        in the Biolink Model. An element is a predicate if it descends from
        `RELATED_TO`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid relation/predicate in Biolink Model
        """
        return RELATED_TO in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def is_translator_canonical_predicate(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a canonical relation/predicate
        in the Biolink Model. An element is a canonical predicate if it descends from
        `RELATED_TO` and is tagged with the annotation 'biolink:canonical_predicate'

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid translator canonical prediacte in Biolink Model
        """
        element = self.get_element(name)
        annotation_tags = []
        if element:
            for annotation in element.annotations:
                annotation_tags.append(annotation)
        is_canonical = (
            True
            if element is not None and "canonical_predicate" in annotation_tags
            else False
        )
        return (
            True
            if RELATED_TO in self.get_ancestors(name, mixin) and is_canonical
            else False
        )

    @lru_cache(CACHE_SIZE)
    def is_mixin(self, name: str) -> bool:
        """
        Determines whether the given name is the name of a mixin
        in the Biolink Model. An element is a mixin if one of its properties is "is_mixin:true"

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid mixin in Biolink Model
        """
        element = self.get_element(name)
        is_mixin = element.mixin if isinstance(element, Definition) else False
        return is_mixin

    @lru_cache(CACHE_SIZE)
    def get_inverse(self, slot_name: str):
        return self.view.inverse(slot_name)

    @lru_cache(CACHE_SIZE)
    def has_inverse(self, name: str) -> bool:
        """
        Determines whether the given name is a predicate and if that predicate has an inverse defined
        in the Biolink Model. An element is a predicate if it descends from
        `RELATED_TO`

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid mixin in Biolink Model
        """
        element = self.get_element(name)
        has_inverse = element.inverse if isinstance(element, SlotDefinition) else False
        return bool(has_inverse)

    @lru_cache(CACHE_SIZE)
    def in_subset(self, name: str, subset: str) -> bool:
        """
        Determines whether the given name is in a given subset
        in the Biolink Model.

        Parameters
        ----------
        name: str
            The name or alias of an element in the Biolink Model.
        subset: str
            The name of the subset

        Returns
        -------
        bool
            That the named element is part of a given subset in Biolink Model

        """
        parsed_name = parse_name(name)
        element = self.view.get_element(parsed_name)
        return subset in element.in_subset

    @lru_cache(CACHE_SIZE)
    def is_category(self, name: str, mixin: bool = True) -> bool:
        """
        Determines whether the given name is the name of a category in the
        Biolink Model. An element is a category if it descends from
        `named thing`

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        bool
            That the named element is a valid category in Biolink Model
        """
        return "named thing" in self.get_ancestors(name, mixin)

    @lru_cache(CACHE_SIZE)
    def is_qualifier(self, name: str) -> bool:
        """
        Predicate to test (by name) if a given Biolink Model element is an Edge Qualifier.

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid edge qualifier in the Biolink Model
        """

        if self.view.get_slot(parse_name(name)) and "qualifier" in self.view.slot_ancestors(parse_name(name)):
            return True
        else:
            return False

    @lru_cache(CACHE_SIZE)
    def is_enum(self, name: str) -> bool:
        """
        Predicate to test (by name) if a given Biolink Model element is an Enum.

        Parameters
        ----------
        name : str
            The name or alias of an element in the Biolink Model

        Returns
        -------
        bool
            That the named element is a valid enum in the Biolink Model
        """
        if ":" in name:
            enum = self.view.get_enum(name.split(":")[1])
        else:
            enum = self.view.get_enum(name)
        if not enum:
            return False
        return True

    @lru_cache(CACHE_SIZE)
    def is_reachable_from_enum(self, enum_name: str, value) -> bool:
        """
        method to test (by name) if a candidate
        'reachable value' ontology term is associated with the given Enum

        Parameters
        ----------
        enum_name : str
            The name or alias of an Enum in the Biolink Model
        value : Any
            The name or alias of the candidate 'reachable value' associated with the given Enum

        Returns
        -------
        bool
            That the named element is a valid 'reachable value' in the Enum
        """
        if self.is_enum(enum_name):
            enum = self.view.get_enum(enum_name)
            if enum.reachable_from is not None and enum.reachable_from.source_ontology:
                if value in self.oi.descendants(enum.reachable_from.source_nodes,
                                                enum.reachable_from.relationship_types):
                    return True
                else:
                    return False
        else:
            return False

    @lru_cache(CACHE_SIZE)
    def is_permissible_value_of_enum(self, enum_name: str, value) -> bool:
        """
        method to test (by name) if a candidate
        'permissible value' is associated with the given Enum

        Parameters
        ----------
        enum_name : str
            The name or alias of an Enum in the Biolink Model
        value : Any
            The name or alias of the candidate 'permissible value' associated with the given Enum

        Returns
        -------
        bool
            That the named element is in the set of 'permissible values' of the Enum
        """

        if ":" in enum_name:
            enum = self.view.get_enum(enum_name.split(":")[1])
        else:
            enum = self.view.get_enum(enum_name, strict=True)
        if enum and value in enum.permissible_values:
            return True
        if self.is_reachable_from_enum(enum_name, value):
            return True
        else:
            return False

    @lru_cache(CACHE_SIZE)
    def get_element_by_prefix(
            self,
            identifier: str
    ) -> List[str]:
        """
        Get a Biolink Model element by prefix.
        This method return the common ancestor of the set of elements referenced by uriorcurie.

        Parameters
        ----------
        identifier: str
            The identifier as a CURIE

        Returns
        -------
        Optional[str]
                The Biolink element corresponding to the given URI/CURIE as available via
                the id_prefixes mapped to that element.

        """
        categories = []
        if ":" in identifier:
            id_components = identifier.split(":")
            prefix = id_components[0]
            elements = self.get_all_elements()
            for category in elements:
                element = self.get_element(category)
                if hasattr(element, 'id_prefixes') and prefix in element.id_prefixes:
                    categories.append(element.name)
        if len(categories) == 0:
            logger.warning("no biolink class found for the given curie: %s, try get_element_by_mapping?", identifier)

        return categories

    @lru_cache(CACHE_SIZE)
    def get_element_by_mapping(
            self,
            identifier: str,
            most_specific: bool = False,
            formatted: bool = False,
            mixin: bool = True,
    ) -> Optional[str]:
        """
        Get a Biolink Model element by mapping.
        This method return the common ancestor of the set of elements referenced by uriorcurie.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        most_specific: bool
            Whether or not to get the first available mapping in the order of specificity
            or to get all mappings of varying specificity
        formatted: bool
            Whether to format element names as CURIEs
        mixin: bool
            If True, then that means we want to find mixin ancestors as well as is_a ancestors

        Returns
        -------
        Optional[str]
            The Biolink element (or the common ancestor) corresponding to the given URI/CURIE

        """
        if most_specific:
            mappings = self._get_element_by_mapping(identifier)
        else:
            mappings = self.get_all_elements_by_mapping(identifier)
        if mappings:
            ancestors: List[List[str]] = []
            for m in mappings:
                ancestors.append(
                    [x for x in self.get_ancestors(m, mixin)[::-1] if x in mappings]
                )
                logger.debug(ancestors)
            without_empty_lists = list(filter(None, ancestors))
            common_ancestors = reduce(
                lambda s, l: s.intersection(set(l)), without_empty_lists[1:], set(without_empty_lists[0])
            )
            logger.debug("common_ancestors")
            logger.debug(common_ancestors)
            for a in without_empty_lists[0]:
                logger.debug("ancestors[0]")
                logger.debug(a)
                if a in common_ancestors:
                    if formatted:
                        element = format_element(self.view.get_element(a))
                    else:
                        element = a
                    return element

    @lru_cache(CACHE_SIZE)
    def _get_element_by_mapping(self, identifier: str) -> List[str]:
        """
        Get the most specific mapping corresponding to a given identifier.
        This method first checks for general mappings. If it can't find any then
        it starts looking for exact_mappings, close_mappings, related_mappings,
        narrow_mappings and finally broad_mappings. It will stop if it finds a
        mapping at first occurrence.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.get_mappings().get(
            self.view.namespaces.uri_for(identifier), set()
        )
        if not mappings:
            exact = set(self.get_element_by_exact_mapping(identifier))
            mappings.update(exact)
        if not mappings:
            close = set(self.get_element_by_close_mapping(identifier))
            mappings.update(close)
        if not mappings:
            related = set(self.get_element_by_related_mapping(identifier))
            mappings.update(related)
        if not mappings:
            narrow = set(self.get_element_by_narrow_mapping(identifier))
            mappings.update(narrow)
        if not mappings:
            broad = set(self.get_element_by_broad_mapping(identifier))
            mappings.update(broad)
        return mappings

    @lru_cache(CACHE_SIZE)
    def get_element_by_exact_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its exact_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.exact_mappings.get(
            self.view.namespaces.uri_for(identifier), set()
        )
        logger.debug(mappings)
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_close_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its close_mappings.

        Parameters
        ----------
        identifier:
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.close_mappings.get(
            self.view.namespaces.uri_for(identifier), set()
        )
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_related_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its related_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.related_mappings.get(
            self.view.namespaces.uri_for(identifier), set()
        )
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_narrow_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its narrow_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.narrow_mappings.get(
            self.view.namespaces.uri_for(identifier), set()
        )
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_element_by_broad_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find a Biolink element that corresponds
        to the given identifier as part of its broad_mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.broad_mappings.get(
            self.view.namespaces.uri_for(identifier), set()
        )
        return self._format_all_elements(mappings, formatted)

    @lru_cache(CACHE_SIZE)
    def get_all_elements_by_mapping(
            self, identifier: str, formatted: bool = False
    ) -> List[str]:
        """
        Given an identifier as IRI/CURIE, find all Biolink elements that correspond
        to the given identifier as part of its mappings.

        Parameters
        ----------
        identifier: str
            The identifier as an IRI or CURIE
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            A list of Biolink elements that correspond to the given identifier IRI/CURIE

        """
        mappings = self.view.get_element_by_mapping(identifier)
        return self._format_all_elements(mappings, formatted)

    def _format_all_elements(
            self, elements: List[str], formatted: bool = False
    ) -> List[str]:
        """
        Format all the elements in a given list.

        Parameters
        ----------
        elements: str
            A list of elements
        formatted: bool
            Whether to format element names as CURIEs

        Returns
        -------
        List[str]
            The formatted list of elements

        """
        if formatted:
            formatted_elements = [
                format_element(self.view.get_element(x)) for x in elements
            ]
        else:
            formatted_elements = elements
        return formatted_elements

    @lru_cache(CACHE_SIZE)
    def get_model_version(self) -> str:
        """
        Return the version of the biolink-model in use.

        Returns
        -------
        str
            The biolink-model version

        """
        return self.view.schema.version

    @deprecation.deprecated(
        deprecated_in="0.3.0",
        removed_in="1.0",
        details="Use get_all_elements method instead",
    )
    def names(self, formatted: bool = False) -> List[str]:
        return self.get_all_elements(formatted)

    @deprecation.deprecated(
        deprecated_in="0.2.0",
        removed_in="1.0",
        details="Use get_descendants method instead",
    )
    def descendents(self, name: str, mixin: bool = True) -> List[str]:
        return self.get_descendants(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.2.0",
        removed_in="1.0",
        details="Use get_ancestors method instead",
    )
    def ancestors(self, name: str, mixin: bool = True) -> List[str]:
        return self.get_ancestors(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.2.0",
        removed_in="1.0",
        details="Use get_children method instead",
    )
    def children(self, name: str, mixin: bool = True) -> List[str]:
        return self.get_children(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.2.0", removed_in="1.0", details="Use get_parent method instead"
    )
    def parent(self, name: str, mixin: bool = True) -> Optional[str]:
        return self.get_parent(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.1.1",
        removed_in="1.0",
        details="Use is_predicate method instead",
    )
    def is_edgelabel(self, name: str, mixin: bool = True) -> bool:
        return self.is_predicate(name, mixin)

    @deprecation.deprecated(
        deprecated_in="0.1.1",
        removed_in="1.0",
        details="Use get_all_elements_by_mapping method instead",
    )
    def get_all_by_mapping(self, uriorcurie: str) -> List[str]:
        return self.get_all_elements_by_mapping(uriorcurie)

    @deprecation.deprecated(
        deprecated_in="0.1.1",
        removed_in="1.0",
        details="Use get_element_by_mapping method instead",
    )
    def get_by_mapping(self, uriorcurie: str) -> Optional[str]:
        return self.get_element_by_mapping(uriorcurie)
